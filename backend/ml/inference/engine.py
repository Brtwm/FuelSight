from __future__ import annotations

from dataclasses import dataclass

from ml.features import (
    MAX_LAG,
    HistoryPoint,
    append_future_point,
    build_feature_vector,
    scenario_demand_multiplier,
)
from ml.models import CatBoostDemandModel, SeasonalNaiveModel


@dataclass(frozen=True)
class ForecastPoint:
    y_hat: float
    y_lo: float | None
    y_hi: float | None


def _interval(y_hat: float, residual_std: float | None) -> tuple[float | None, float | None]:
    if residual_std is None or residual_std <= 0:
        return None, None
    margin = 1.64 * residual_std
    return max(0.0, y_hat - margin), max(y_hat, y_hat + margin)


def forecast_with_baseline(
    history_points: list[HistoryPoint],
    horizon_days: int,
    *,
    scenario_delta_pct: float = 0.0,
    residual_std: float | None = None,
) -> list[ForecastPoint]:
    values = [row.volume_liters for row in history_points]
    model = SeasonalNaiveModel().fit(values)
    multiplier = scenario_demand_multiplier(scenario_delta_pct)
    path = model.forecast(values, horizon_days=horizon_days)
    points: list[ForecastPoint] = []
    effective_std = residual_std if residual_std is not None else model.residual_std
    for y_hat_raw in path:
        y_hat = max(0.0, y_hat_raw * multiplier)
        y_lo, y_hi = _interval(y_hat, effective_std)
        points.append(ForecastPoint(y_hat=y_hat, y_lo=y_lo, y_hi=y_hi))
    return points


def forecast_with_catboost(
    history_points: list[HistoryPoint],
    horizon_days: int,
    model: CatBoostDemandModel,
    *,
    scenario_delta_pct: float = 0.0,
    residual_std: float | None = None,
) -> list[ForecastPoint]:
    if len(history_points) < MAX_LAG + 1:
        raise ValueError(f"At least {MAX_LAG + 1} history points are required")

    dynamic = [*history_points]
    points: list[ForecastPoint] = []
    multiplier = scenario_demand_multiplier(scenario_delta_pct)

    for _ in range(horizon_days):
        dynamic.append(append_future_point(dynamic, scenario_delta_pct=scenario_delta_pct))
        feature_index = len(dynamic) - 1
        features = build_feature_vector(dynamic, feature_index)
        y_hat_raw = model.predict_next(features)
        y_hat = max(0.0, y_hat_raw * multiplier)
        latest = dynamic[-1]
        dynamic[-1] = HistoryPoint(
            day=latest.day,
            volume_liters=y_hat,
            avg_retail_price_rub=latest.avg_retail_price_rub,
            avg_purchase_price_rub=latest.avg_purchase_price_rub,
            gross_margin_rub_per_liter=latest.gross_margin_rub_per_liter,
        )
        y_lo, y_hi = _interval(y_hat, residual_std)
        points.append(ForecastPoint(y_hat=y_hat, y_lo=y_lo, y_hi=y_hi))

    return points
