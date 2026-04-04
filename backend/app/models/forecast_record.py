from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.model_record import ModelRecord
    from app.models.product import Product


class ForecastRecord(Base):
    __tablename__ = "forecasts"
    __table_args__ = (Index("idx_forecasts_product_target_date", "product_id", "target_date"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    model_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("models.id", ondelete="SET NULL"),
        nullable=True,
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    scenario_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        server_default=text("'base'"),
    )
    scenario_params_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    y_hat: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    y_lo: Mapped[Decimal | None] = mapped_column(Numeric(14, 3), nullable=True)
    y_hi: Mapped[Decimal | None] = mapped_column(Numeric(14, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    model: Mapped["ModelRecord | None"] = relationship(back_populates="forecasts")
    product: Mapped["Product"] = relationship(back_populates="forecasts")
