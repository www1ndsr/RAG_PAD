from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RawDocument(BaseModel):
    """Сырой документ, загруженный из GitHub / Web."""

    source_url: str
    content: bytes
    content_type: str  # e.g., 'text/markdown', 'text/x-python', 'application/json'
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class ParsedDocument(BaseModel):
    """Извлеченный и очищенный текст с первичными метаданными."""

    title: Optional[str] = None
    text_content: str
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class StandardDocument(BaseModel):
    """Каноническая модель документа, готовая для сохранения в БД и отправки в чанкер."""

    doc_id: str  # SHA-256 хэш (дедупликация)
    source_url: str
    title: str
    content: str
    file_type: str  # 'markdown', 'python', 'yaml'
    metadata: Dict[str, Any]  # JSONB для PostgreSQL
    created_at: datetime = Field(default_factory=datetime.utcnow)