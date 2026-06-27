from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from app.services.data_generator import DataGenerator
from app.services.data_generator_config import RU_HOLIDAYS, event_pressure_for_day
from ml.backtesting import run_rolling_backtest
from ml.features import normalize_history_rows


def _demo_history_for_product(product_code: str):
    start = date(2025, 6, 27)
    end = date(2026, 6, 26)
    product_codes = ["AI_92", "AI_95", "DT_S", "DT_W"]
    dataset = DataGenerator(seed=42).generate(
        start_date=start,
        end_date=end,
        product_codes=product_codes,
    )
    purchases = {
        (item.purchase_date, item.product_code): item
        for item in dataset.purchases
    }
    sales_by_day: dict[date, dict[str, float]] = defaultdict(dict)
    for row in dataset.sales:
        sales_by_day[row.sale_date][row.product_code] = float(row.volume_liters)

    rows = []
    product_sales = sorted(
        [item for item in dataset.sales if item.product_code == product_code],
        key=lambda item: item.sale_date,
    )
    for sale in product_sales:
        purchase = purchases[(sale.sale_date, product_code)]
        gasoline_group_volume = (
            sales_by_day[sale.sale_date].get("AI_92", 0.0)
            + sales_by_day[sale.sale_date].get("AI_95", 0.0)
        )
        previous_day = sale.sale_date - timedelta(days=1)
        previous_week = sale.sale_date - timedelta(days=7)
        group_lag_1 = (
            sales_by_day[previous_day].get("AI_92", 0.0)
            + sales_by_day[previous_day].get("AI_95", 0.0)
        )
        group_lag_7 = (
            sales_by_day[previous_week].get("AI_92", 0.0)
            + sales_by_day[previous_week].get("AI_95", 0.0)
        )
        retail = float(sale.avg_retail_price_rub)
        purchase_price = float(purchase.purchase_price_rub)
        rows.append(
            {
                "date": sale.sale_date,
                "volume_liters": float(sale.volume_liters),
                "avg_retail_price_rub": retail,
                "avg_purchase_price_rub": purchase_price,
                "gross_margin_rub_per_liter": retail - purchase_price,
                "holiday_flag": 1.0
                if (sale.sale_date.month, sale.sale_date.day) in RU_HOLIDAYS
                else 0.0,
                "event_pressure_score": event_pressure_for_day(sale.sale_date),
                "product_share_in_group": (
                    float(sale.volume_liters) / gasoline_group_volume
                    if gasoline_group_volume > 0
                    else 0.0
                ),
                "group_volume_liters": gasoline_group_volume,
                "group_volume_lag_1": group_lag_1 or gasoline_group_volume,
                "group_volume_lag_7": group_lag_7 or group_lag_1 or gasoline_group_volume,
            }
        )
    return normalize_history_rows(rows)


def test_catboost_beats_seasonal_baseline_on_main_ai95_demo_slice() -> None:
    history = _demo_history_for_product("AI_95")

    baseline = run_rolling_backtest(
        history,
        model_type="seasonal_naive",
        horizon_days=7,
        window_type="rolling",
        max_folds=12,
    )
    catboost = run_rolling_backtest(
        history,
        model_type="catboost",
        horizon_days=7,
        window_type="rolling",
        max_folds=12,
    )

    assert catboost.smape <= baseline.smape
