from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.grabber.schemas import StandardDocument

Base = declarative_base()


class ProcessedDocumentORM(Base):
    """Таблица PostgreSQL для хранения реестра обработанных документов."""

    __tablename__ = "processed_documents"

    doc_id = Column(String(64), primary_key=True)  # SHA-256
    source_url = Column(Text, nullable=False)
    title = Column(Text, nullable=True)
    file_type = Column(String(20), nullable=False)
    doc_metadata = Column(JSONB, nullable=False)  # NoSQL метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PostgresMetadataStorage:
    """Асинхронный сервис взаимодействия с PostgreSQL."""

    def __init__(self, db_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db"):
        self.engine = create_async_engine(db_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        """Создание таблиц при запуске."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def is_duplicate(self, doc_id: str) -> bool:
        """Проверка дедупликации: возвращает True, если документ уже обрабатывался."""
        async with self.async_session() as session:
            result = await session.get(ProcessedDocumentORM, doc_id)
            return result is not None

    async def save_document(self, doc: StandardDocument) -> bool:
        """Сохраняет метаданные и запись о документе в БД."""
        if await self.is_duplicate(doc.doc_id):
            return False  # Пропускаем дубликат

        async with self.async_session() as session:
            async with session.begin():
                record = ProcessedDocumentORM(
                    doc_id=doc.doc_id,
                    source_url=doc.source_url,
                    title=doc.title,
                    file_type=doc.file_type,
                    doc_metadata=doc.metadata,
                )
                session.add(record)
            return True