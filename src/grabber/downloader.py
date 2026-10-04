import asyncio
import logging
from typing import List, Optional
import httpx

from src.grabber.schemas import RawDocument

logger = logging.getLogger(__name__)


class GitHubRepositoryDownloader:
    """Асинхронный загрузчик файлов из GitHub репозиториев (например, Ultralytics YOLO)."""

    def __init__(self, github_token: Optional[str] = None, timeout: float = 15.0):
        self.timeout = timeout
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            self.headers["Authorization"] = f"Bearer {github_token}"

    async def fetch_yolo_docs_and_code(
        self,
        owner: str = "ultralytics",
        repo: str = "ultralytics",
        branch: str = "main",
        allowed_extensions: tuple = (".md", ".py", ".yaml"),
    ) -> List[RawDocument]:
        """Скачивает документацию и исходный код из репозитория YOLO."""
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"

        async with httpx.AsyncClient(
            headers=self.headers, timeout=self.timeout, follow_redirects=True
        ) as client:
            logger.info(f"Запрос дерева файлов репозитория {owner}/{repo}...")
            response = await client.get(tree_url)
            response.raise_for_status()
            tree_data = response.json()

            items = tree_data.get("tree", [])
            # Фильтруем только файлы с нужными расширениями
            target_files = [
                item
                for item in items
                if item["type"] == "blob"
                and item["path"].endswith(allowed_extensions)
            ]

            logger.info(
                f"Найдено {len(target_files)} подходящих файлов. Начинаем загрузку..."
            )

            # Ограничиваем параллельные запросы к GitHub (Semaphore)
            semaphore = asyncio.Semaphore(10)

            async def _download_single(item: dict) -> Optional[RawDocument]:
                async with semaphore:
                    path = item["path"]
                    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                    try:
                        res = await client.get(raw_url)
                        if res.status_code == 200:
                            content_type = "text/markdown" if path.endswith(".md") else "text/plain"
                            return RawDocument(
                                source_url=raw_url,
                                content=res.content,
                                content_type=content_type,
                            )
                    except Exception as e:
                        logger.error(f"Ошибка скачивания {path}: {e}")
                    return None

            tasks = [_download_single(item) for item in target_files]
            results = await asyncio.gather(*tasks)

            # Фильтруем провалившиеся скачивания
            successful_docs = [doc for doc in results if doc is not None]
            logger.info(f"Успешно скачано {len(successful_docs)} документов.")
            return successful_docs