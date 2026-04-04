"""phase4 kpi margin view

Revision ID: 20260404_0002
Revises: 20260329_0001
Create Date: 2026-04-04 18:30:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260404_0002"
down_revision: str | None = "20260329_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE VIEW vw_margin_daily AS
        WITH sales_agg AS (
          SELECT
            sd.sale_date::date AS date,
            sd.product_id,
            SUM(sd.volume_liters)::numeric AS sales_volume_liters,
            SUM(sd.revenue_rub)::numeric AS revenue_rub,
            CASE
              WHEN SUM(sd.volume_liters) > 0
              THEN (SUM(sd.revenue_rub) / SUM(sd.volume_liters))::numeric
              ELSE NULL
            END AS avg_retail_price_rub
          FROM sales_daily sd
          GROUP BY sd.sale_date, sd.product_id
        ),
        purchase_agg AS (
          SELECT
            pd.purchase_date::date AS date,
            pd.product_id,
            SUM(pd.volume_liters)::numeric AS purchase_volume_liters,
            CASE
              WHEN SUM(pd.volume_liters) > 0
              THEN (SUM(pd.volume_liters * pd.purchase_price_rub) / SUM(pd.volume_liters))::numeric
              ELSE NULL
            END AS avg_purchase_price_rub
          FROM purchases_daily pd
          GROUP BY pd.purchase_date, pd.product_id
        )
        SELECT
          s.date,
          s.product_id,
          p.code AS product_code,
          s.sales_volume_liters AS volume_liters,
          s.revenue_rub,
          s.avg_retail_price_rub,
          COALESCE(pa.purchase_volume_liters, 0)::numeric AS purchase_volume_liters,
          pa.avg_purchase_price_rub,
          (pa.product_id IS NULL) AS purchase_data_missing,
          CASE
            WHEN pa.product_id IS NULL THEN NULL
            ELSE (s.revenue_rub - (s.sales_volume_liters * pa.avg_purchase_price_rub))::numeric
          END AS gross_margin_rub,
          CASE
            WHEN pa.product_id IS NULL THEN NULL
            ELSE (s.avg_retail_price_rub - pa.avg_purchase_price_rub)::numeric
          END AS gross_margin_rub_per_liter,
          CASE
            WHEN pa.product_id IS NULL OR s.avg_retail_price_rub = 0 THEN NULL
            ELSE (
              ((s.avg_retail_price_rub - pa.avg_purchase_price_rub) / s.avg_retail_price_rub) * 100
            )::numeric
          END AS gross_margin_pct
        FROM sales_agg s
        JOIN products p ON p.id = s.product_id
        LEFT JOIN purchase_agg pa
          ON pa.date = s.date
         AND pa.product_id = s.product_id
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS vw_margin_daily")
