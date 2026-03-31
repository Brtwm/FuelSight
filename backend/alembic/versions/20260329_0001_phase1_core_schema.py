"""phase1 core schema

Revision ID: 20260329_0001
Revises:
Create Date: 2026-03-29 23:45:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260329_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "roles",
        sa.Column("id", sa.SmallInteger(), autoincrement=True, nullable=False),
        sa.Column("slug", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("unit", sa.String(length=16), server_default=sa.text("'liter'"), nullable=False),
        sa.Column("density_kg_m3", sa.Numeric(precision=8, scale=3), nullable=True),
        sa.Column("vat_rate", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("excise_rate", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("role_id", sa.SmallInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "sales_daily",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("volume_liters", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("revenue_rub", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("avg_retail_price_rub", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("data_source", sa.String(length=32), nullable=False),
        sa.Column("source_batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("avg_retail_price_rub > 0", name="ck_sales_daily_price_positive"),
        sa.CheckConstraint("revenue_rub > 0", name="ck_sales_daily_revenue_positive"),
        sa.CheckConstraint("volume_liters > 0", name="ck_sales_daily_volume_positive"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "sale_date",
            "product_id",
            "data_source",
            "source_batch_id",
            name="uq_sales_daily_batch",
        ),
    )
    op.create_index(
        "idx_sales_daily_date_product",
        "sales_daily",
        ["sale_date", "product_id"],
        unique=False,
    )

    op.create_table(
        "purchases_daily",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("volume_liters", sa.Numeric(precision=14, scale=3), nullable=False),
        sa.Column("purchase_price_rub", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column(
            "logistics_cost_rub",
            sa.Numeric(precision=12, scale=2),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("supplier_name", sa.String(length=255), nullable=True),
        sa.Column("total_cost_rub", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("data_source", sa.String(length=32), nullable=False),
        sa.Column("source_batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "logistics_cost_rub >= 0",
            name="ck_purchases_daily_logistics_non_negative",
        ),
        sa.CheckConstraint("purchase_price_rub >= 0", name="ck_purchases_daily_price_non_negative"),
        sa.CheckConstraint("total_cost_rub > 0", name="ck_purchases_daily_total_cost_positive"),
        sa.CheckConstraint("volume_liters > 0", name="ck_purchases_daily_volume_positive"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_purchases_daily_date_product",
        "purchases_daily",
        ["purchase_date", "product_id"],
        unique=False,
    )

    op.create_table(
        "import_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(length=32), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rows_total", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("rows_success", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("rows_failed", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("error_report_path", sa.Text(), nullable=True),
        sa.Column("started_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("rows_failed >= 0", name="ck_import_jobs_rows_failed_non_negative"),
        sa.CheckConstraint("rows_success >= 0", name="ck_import_jobs_rows_success_non_negative"),
        sa.CheckConstraint("rows_total >= 0", name="ck_import_jobs_rows_total_non_negative"),
        sa.ForeignKeyConstraint(["started_by"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("import_jobs")
    op.drop_index("idx_purchases_daily_date_product", table_name="purchases_daily")
    op.drop_table("purchases_daily")
    op.drop_index("idx_sales_daily_date_product", table_name="sales_daily")
    op.drop_table("sales_daily")
    op.drop_table("users")
    op.drop_table("products")
    op.drop_table("roles")
