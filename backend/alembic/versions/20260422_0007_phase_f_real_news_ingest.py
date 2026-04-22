"""phase f real news ingest baseline

Revision ID: 20260422_0007
Revises: 20260420_0006
Create Date: 2026-04-22 15:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260422_0007"
down_revision: str | None = "20260420_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("news_raw", sa.Column("provider_name", sa.String(length=64), nullable=True))
    op.add_column(
        "news_raw",
        sa.Column(
            "provider_mode",
            sa.String(length=32),
            server_default=sa.text("'manual_snapshot'"),
            nullable=False,
        ),
    )
    op.add_column("news_raw", sa.Column("confidence", sa.Float(), nullable=True))
    op.add_column("news_raw", sa.Column("cached_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "news_raw",
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.execute("UPDATE news_raw SET provider_name = source_name WHERE provider_name IS NULL")
    op.alter_column("news_raw", "provider_name", nullable=False)
    op.create_check_constraint(
        "ck_news_raw_provider_mode",
        "news_raw",
        "provider_mode IN ('live', 'cached', 'manual_snapshot')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_news_raw_provider_mode", "news_raw", type_="check")
    op.drop_column("news_raw", "metadata_json")
    op.drop_column("news_raw", "cached_at")
    op.drop_column("news_raw", "confidence")
    op.drop_column("news_raw", "provider_mode")
    op.drop_column("news_raw", "provider_name")
