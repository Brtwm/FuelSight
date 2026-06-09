from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import pstdev
from typing import Literal

from ml.backtesting.metrics import mae, rmse, smape
from ml.features import MAX_LAG, HistoryPoint, build_training_matrix
from ml.inference import forecast_with_baseline, forecast_with_catboost
from ml.models import CatBoostDemandModel, is_catboost_available

ModelKind = Literal["seasonal_naive", "catboost"]
WindowType = Literal["rolling", "expanding"]


@dataclass(frozen=True)
class BacktestOutcome:
    model_type: ModelKind
    mae: float
    rmse: float
    smape: float
    residual_std: float
    folds: int
    predictions: list[float]
    actual: list[float]
    dates: list[date]


def _train_catboost_next_day(train_points: list[HistoryPoint]) -> CatBoostDemandModel:
    x_train, y_train = build_training_matrix(train_points)
    if len(y_train) < 20:
        raise ValueError("Not enough rows to train CatBoost")
    return CatBoostDemandModel.train(x_train, y_train)


def _forecast_path(
    *,
    model_type: ModelKind,
    train_points: list[HistoryPoint],
    horizon_days: int,
) -> list[float]:
    if model_type == "seasonal_naive":
        return [
            point.y_hat for point in forecast_with_baseline(train_points, horizon_days=horizon_days)
        ]
    model = _train_catboost_next_day(train_points)
    return [
        point.y_hat
        for point in forecast_with_catboost(
            train_points,
            horizon_days=horizon_days,
            model=model,
        )
    ]


def run_rolling_backtest(
    history_points: list[HistoryPoint],
    *,
    model_type: ModelKind,
    horizon_days: int,
    window_type: WindowType = "rolling",
    max_folds: int = 8,
) -> BacktestOutcome:
    if len(history_points) < MAX_LAG + horizon_days + 20:
        raise ValueError("Insufficient history for backtest")

    origins = list(range(MAX_LAG + 20, len(history_points) - 1))
    if len(origins) > max_folds:
        origins = origins[-max_folds:]

    actual_values: list[float] = []
    predicted_values: list[float] = []
    dates: list[date] = []

    for origin in origins:
        remaining = len(history_points) - origin - 1
        if remaining <= 0:
            continue
        steps = min(horizon_days, remaining)
        if window_type == "rolling":
            start_index = max(0, origin - 180)
        else:
            start_index = 0
        train_points = history_points[start_index : origin + 1]
        try:
            forecast_path = _forecast_path(
                model_type=model_type,
                train_points=train_points,
                horizon_days=steps,
            )
        except Exception:
            if model_type == "catboost":
                continue
            raise

        fold_actual = [history_points[origin + step].volume_liters for step in range(1, steps + 1)]
        fold_dates = [history_points[origin + step].day for step in range(1, steps + 1)]
        predicted_values.extend(forecast_path)
        actual_values.extend(fold_actual)
        dates.extend(fold_dates)

    if not actual_values or not predicted_values:
        raise ValueError("Insufficient history for backtest")

    residuals = [a - p for a, p in zip(actual_values, predicted_values, strict=True)]
    residual_std = pstdev(residuals) if len(residuals) > 1 else 0.0

    return BacktestOutcome(
        model_type=model_type,
        mae=mae(actual_values, predicted_values),
        rmse=rmse(actual_values, predicted_values),
        smape=smape(actual_values, predicted_values),
        residual_std=residual_std,
        folds=len(origins),
        predictions=predicted_values,
        actual=actual_values,
        dates=dates,
    )


def select_best_outcome(outcomes: list[BacktestOutcome]) -> BacktestOutcome:
    if not outcomes:
        raise ValueError("No backtest outcomes provided")
    return sorted(outcomes, key=lambda item: (item.smape, item.rmse))[0]


def available_model_kinds() -> list[ModelKind]:
    if is_catboost_available():
        return ["seasonal_naive", "catboost"]
    return ["seasonal_naive"]
