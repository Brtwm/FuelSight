from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExternalIndicatorDaily(Base):
    __tablename__ = "external_indicators_daily"
    __table_args__ = (
        UniqueConstraint(
            "indicator_date",
            "indicator_code",
            "provider_name",
            name="uq_external_indicators_daily_date_code_provider",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    indicator_date: Mapped[date] = mapped_column(Date, nullable=False)
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False)
    value_numeric: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_mode: Mapped[str] = mapped_column(String(32), nullable=False)
    cache_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
