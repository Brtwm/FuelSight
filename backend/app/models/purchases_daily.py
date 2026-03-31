from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class PurchasesDaily(Base):
    __tablename__ = "purchases_daily"
    __table_args__ = (
        CheckConstraint("volume_liters > 0", name="ck_purchases_daily_volume_positive"),
        CheckConstraint("purchase_price_rub >= 0", name="ck_purchases_daily_price_non_negative"),
        CheckConstraint(
            "logistics_cost_rub >= 0",
            name="ck_purchases_daily_logistics_non_negative",
        ),
        CheckConstraint("total_cost_rub > 0", name="ck_purchases_daily_total_cost_positive"),
        Index("idx_purchases_daily_date_product", "purchase_date", "product_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    volume_liters: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    purchase_price_rub: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    logistics_cost_rub: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        server_default=text("0"),
    )
    supplier_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_cost_rub: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    data_source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    product: Mapped["Product"] = relationship(back_populates="purchases_daily")
