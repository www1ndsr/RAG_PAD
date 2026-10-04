import hashlib
from src.grabber.schemas import ParsedDocument, RawDocument, StandardDocument


class DocumentConverter:
    """Приведение документов к единому формату StandardDocument."""

    def to_standard(
        self, raw_doc: RawDocument, parsed_doc: ParsedDocument
    ) -> StandardDocument:
        # Генерируем хэш SHA-256 от текста документа для дедупликации
        content_hash = hashlib.sha256(
            parsed_doc.text_content.encode("utf-8")
        ).hexdigest()

        file_ext = raw_doc.source_url.split(".")[-1]

        return StandardDocument(
            doc_id=content_hash,
            source_url=raw_doc.source_url,
            title=parsed_doc.title or "Untitled Document",
            content=parsed_doc.text_content,
            file_type=file_ext,
            metadata={
                "content_type": raw_doc.content_type,
                "fetched_at": raw_doc.fetched_at.isoformat(),
                **parsed_doc.raw_metadata,
            },
        )