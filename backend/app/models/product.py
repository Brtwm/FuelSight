from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.purchases_daily import PurchasesDaily
    from app.models.sales_daily import SalesDaily


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    unit: Mapped[str] = mapped_column(String(16), nullable=False, server_default=text("'liter'"))
    density_kg_m3: Mapped[Decimal | None] = mapped_column(Numeric(8, 3), nullable=True)
    vat_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    excise_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    sales_daily: Mapped[list["SalesDaily"]] = relationship(back_populates="product")
    purchases_daily: Mapped[list["PurchasesDaily"]] = relationship(back_populates="product")
