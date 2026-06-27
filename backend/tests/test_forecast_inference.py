from __future__ import annotations

from datetime import date, timedelta

from ml.features import FEATURE_NAMES, MAX_LAG, HistoryPoint
from ml.inference import forecast_with_catboost


class _CapturingModel:
    def __init__(self) -> None:
        self.features: list[list[float]] = []

    def predict_next(self, features: list[float]) -> float:
        self.features.append(features)
        return 1000.0


def _history_with_external_context(days: int = MAX_LAG + 2) -> list[HistoryPoint]:
    start = date(2026, 1, 1)
    return [
        HistoryPoint(
            day=start + timedelta(days=index),
            volume_liters=1000.0 + index,
            avg_retail_price_rub=58.0,
            avg_purchase_price_rub=50.0,
            gross_margin_rub_per_liter=8.0,
            crude_brent_usd=82.5,
            usd_rub=91.2,
            wholesale_gasoline_index=67.4,
            wholesale_diesel_index=70.1,
            holiday_flag=1.0,
            event_pressure_score=0.3,
            product_share_in_group=0.44,
            group_volume_liters=2400.0,
            group_volume_lag_1=2380.0,
            group_volume_lag_7=2300.0,
        )
        for index in range(days)
    ]


def test_catboost_recursive_forecast_preserves_external_features() -> None:
    model = _CapturingModel()
    crude_index = FEATURE_NAMES.index("crude_brent_usd")
    event_index = FEATURE_NAMES.index("event_pressure_score")
    group_lag_index = FEATURE_NAMES.index("group_volume_lag_7")

    forecast_with_catboost(_history_with_external_context(), horizon_days=2, model=model)  # type: ignore[arg-type]

    assert len(model.features) == 2
    assert model.features[1][crude_index] == 82.5
    assert model.features[1][event_index] == 0.3
    assert model.features[1][group_lag_index] == 2300.0
