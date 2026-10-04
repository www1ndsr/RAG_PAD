import asyncio
import logging
import os
from src.grabber import (
    GitHubRepositoryDownloader,
    DocumentParser,
    DocumentConverter,
    PostgresMetadataStorage,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db",
    )

    logger.info("Подключение к PostgreSQL и создание таблиц...")
    storage = PostgresMetadataStorage(db_url=db_url)
    await storage.init_db()

    downloader = GitHubRepositoryDownloader()
    parser = DocumentParser()
    converter = DocumentConverter()

    logger.info("Скачивание файлов из репозитория Ultralytics YOLO...")
    raw_docs = await downloader.fetch_yolo_docs_and_code()

    saved_count = 0
    skipped_count = 0

    logger.info("Обработка и сохранение документов в PostgreSQL...")
    for raw_doc in raw_docs:
        parsed_doc = parser.parse(raw_doc)
        std_doc = converter.to_standard(raw_doc, parsed_doc)

        is_saved = await storage.save_document(std_doc)
        if is_saved:
            saved_count += 1
            logger.info(f"Сохранён: {std_doc.title} ({std_doc.source_url})")
        else:
            skipped_count += 1
            logger.info(f"Пропущен дубликат: {std_doc.doc_id[:12]}...")

    logger.info(
        f"Завершено! Сохранено новых: {saved_count}, Пропущено дубликатов: {skipped_count}"
    )


if __name__ == "__main__":
    asyncio.run(main())