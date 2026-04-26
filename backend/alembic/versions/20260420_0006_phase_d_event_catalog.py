"""phase d event catalog

Revision ID: 20260420_0006
Revises: 20260408_0005
Create Date: 2026-04-20 16:00:00.000000
"""

from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260420_0006"
down_revision: str | None = "20260408_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_catalog",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("event_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("start_month", sa.Integer(), nullable=False),
        sa.Column("start_day", sa.Integer(), nullable=False),
        sa.Column("end_month", sa.Integer(), nullable=False),
        sa.Column("end_day", sa.Integer(), nullable=False),
        sa.Column("pressure_score", sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column(
            "demand_delta_pct",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "purchase_delta_pct",
            sa.Numeric(precision=8, scale=4),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "source_mode", sa.String(length=32), server_default=sa.text("'db'"), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_code", name="uq_event_catalog_event_code"),
    )

    event_catalog = sa.table(
        "event_catalog",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("event_code", sa.String(length=64)),
        sa.column("title", sa.String(length=255)),
        sa.column("start_month", sa.Integer()),
        sa.column("start_day", sa.Integer()),
        sa.column("end_month", sa.Integer()),
        sa.column("end_day", sa.Integer()),
        sa.column("pressure_score", sa.Numeric(precision=8, scale=4)),
        sa.column("demand_delta_pct", sa.Numeric(precision=8, scale=4)),
        sa.column("purchase_delta_pct", sa.Numeric(precision=8, scale=4)),
        sa.column("source_mode", sa.String(length=32)),
        sa.column("is_active", sa.Boolean()),
        sa.column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    now = datetime.utcnow()
    op.bulk_insert(
        event_catalog,
        [
            {
                "id": uuid4(),
                "event_code": "spring_refinery_repairs",
                "title": "Плановые ремонты НПЗ весной",
                "start_month": 3,
                "start_day": 20,
                "end_month": 4,
                "end_day": 20,
                "pressure_score": 0.35,
                "demand_delta_pct": 0.0,
                "purchase_delta_pct": 3.0,
                "source_mode": "db",
                "is_active": True,
                "metadata_json": {"seed": "phase_d"},
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": uuid4(),
                "event_code": "may_holiday_mobility",
                "title": "Майские праздники и рост мобильности",
                "start_month": 5,
                "start_day": 1,
                "end_month": 5,
                "end_day": 11,
                "pressure_score": 0.20,
                "demand_delta_pct": 4.0,
                "purchase_delta_pct": 0.0,
                "source_mode": "db",
                "is_active": True,
                "metadata_json": {"seed": "phase_d"},
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": uuid4(),
                "event_code": "summer_logistics_tension",
                "title": "Летние логистические ограничения",
                "start_month": 7,
                "start_day": 10,
                "end_month": 8,
                "end_day": 20,
                "pressure_score": 0.28,
                "demand_delta_pct": 0.0,
                "purchase_delta_pct": 2.2,
                "source_mode": "db",
                "is_active": True,
                "metadata_json": {"seed": "phase_d"},
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": uuid4(),
                "event_code": "autumn_fx_volatility",
                "title": "Осенняя волатильность валюты",
                "start_month": 9,
                "start_day": 15,
                "end_month": 10,
                "end_day": 20,
                "pressure_score": 0.22,
                "demand_delta_pct": 0.0,
                "purchase_delta_pct": 1.8,
                "source_mode": "db",
                "is_active": True,
                "metadata_json": {"seed": "phase_d"},
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": uuid4(),
                "event_code": "winter_diesel_peak",
                "title": "Зимний пик спроса на ДТ",
                "start_month": 11,
                "start_day": 20,
                "end_month": 2,
                "end_day": 15,
                "pressure_score": 0.30,
                "demand_delta_pct": 3.0,
                "purchase_delta_pct": 0.0,
                "source_mode": "db",
                "is_active": True,
                "metadata_json": {"seed": "phase_d"},
                "created_at": now,
                "updated_at": now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("event_catalog")
