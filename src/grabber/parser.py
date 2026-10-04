import ast
import re
from src.grabber.schemas import ParsedDocument, RawDocument


class DocumentParser:
    """Парсер для обработки Markdown, YAML и Python файлов."""

    def parse(self, raw_doc: RawDocument) -> ParsedDocument:
        content_text = raw_doc.content.decode("utf-8", errors="ignore")

        if raw_doc.source_url.endswith(".md"):
            return self._parse_markdown(content_text)
        elif raw_doc.source_url.endswith(".py"):
            return self._parse_python(content_text)
        else:
            return ParsedDocument(
                title=raw_doc.source_url.split("/")[-1],
                text_content=content_text,
            )

    def _parse_markdown(self, text: str) -> ParsedDocument:
        # Извлекаем заголовок первого уровня `# Title`
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Markdown Document"

        # Удаляем HTML-комментарии, если они есть
        cleaned_text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()

        return ParsedDocument(
            title=title,
            text_content=cleaned_text,
            raw_metadata={"format": "markdown"},
        )

    def _parse_python(self, text: str) -> ParsedDocument:
        """Извлекает docstring модуля и структуру классов/функций для индексации кода."""
        module_doc = ""
        try:
            tree = ast.parse(text)
            module_doc = ast.get_docstring(tree) or ""
        except Exception:
            pass

        return ParsedDocument(
            title=text.splitlines()[0] if text else "Python Script",
            text_content=text,
            raw_metadata={
                "format": "python",
                "module_docstring": module_doc,
            },
        )