from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Float, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from app.core.database import Base


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kw: Any) -> str:  # noqa: ANN401
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect: Any):  # noqa: ANN401
        def process(value: list[float] | str | None) -> str | None:
            if value is None or isinstance(value, str):
                return value
            return "[" + ",".join(f"{float(item):.8f}" for item in value) + "]"

        return process

    def result_processor(self, dialect: Any, coltype: Any):  # noqa: ANN401
        def process(value: str | None) -> list[float] | None:
            if value is None:
                return None
            stripped = value.strip().strip("[]")
            if not stripped:
                return []
            return [float(item) for item in stripped.split(",")]

        return process


class RagChunk(Base):
    __tablename__ = "rag_chunks"
    __table_args__ = (
        Index("idx_rag_chunks_source", "source_type", "source_id"),
        Index("idx_rag_chunks_published_at", "published_at"),
        Index(
            "idx_rag_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    full_text_chunk: Mapped[str] = mapped_column(Text, nullable=False)
    external_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(64), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
