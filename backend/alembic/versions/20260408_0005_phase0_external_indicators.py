"""phase0 external indicators table

Revision ID: 20260408_0005
Revises: 20260405_0004
Create Date: 2026-04-08 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260408_0005"
down_revision: str | None = "20260405_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_indicators_daily",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("indicator_date", sa.Date(), nullable=False),
        sa.Column("indicator_code", sa.String(length=64), nullable=False),
        sa.Column("value_numeric", sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_mode", sa.String(length=32), nullable=False),
        sa.Column("cache_key", sa.String(length=255), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "indicator_date",
            "indicator_code",
            "provider_name",
            name="uq_external_indicators_daily_date_code_provider",
        ),
    )


def downgrade() -> None:
    op.drop_table("external_indicators_daily")
