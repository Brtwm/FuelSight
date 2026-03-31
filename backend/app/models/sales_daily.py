from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.product import Product


class SalesDaily(Base):
    __tablename__ = "sales_daily"
    __table_args__ = (
        UniqueConstraint(
            "sale_date",
            "product_id",
            "data_source",
            "source_batch_id",
            name="uq_sales_daily_batch",
        ),
        CheckConstraint("volume_liters > 0", name="ck_sales_daily_volume_positive"),
        CheckConstraint("revenue_rub > 0", name="ck_sales_daily_revenue_positive"),
        CheckConstraint("avg_retail_price_rub > 0", name="ck_sales_daily_price_positive"),
        Index("idx_sales_daily_date_product", "sale_date", "product_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    sale_date: Mapped[date] = mapped_column(Date, nullable=False)
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )
    volume_liters: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    revenue_rub: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    avg_retail_price_rub: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    data_source: Mapped[str] = mapped_column(String(32), nullable=False)
    source_batch_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    product: Mapped["Product"] = relationship(back_populates="sales_daily")
