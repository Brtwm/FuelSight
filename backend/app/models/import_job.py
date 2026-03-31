from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint("rows_total >= 0", name="ck_import_jobs_rows_total_non_negative"),
        CheckConstraint("rows_success >= 0", name="ck_import_jobs_rows_success_non_negative"),
        CheckConstraint("rows_failed >= 0", name="ck_import_jobs_rows_failed_non_negative"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    rows_total: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    rows_success: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    rows_failed: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    error_report_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_by: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    started_by_user: Mapped["User"] = relationship(back_populates="import_jobs")
