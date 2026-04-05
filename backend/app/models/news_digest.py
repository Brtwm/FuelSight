from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NewsDigest(Base):
    __tablename__ = "news_digests"
    __table_args__ = (
        UniqueConstraint("digest_date", "period_type", name="uq_news_digests_date_period"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    digest_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(String(16), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    bullet_points_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    source_ids_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    llm_mode: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'off'"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
