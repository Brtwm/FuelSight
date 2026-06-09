from __future__ import annotations

from datetime import UTC, date, datetime

from pydantic import ValidationError

from app.schemas.backtests import BacktestMetrics, BacktestPayload, ValidationSummary
from app.schemas.forecasts import ForecastRunRequest


def test_forecast_scenario_rejects_non_price_delta_fields() -> None:
    try:
        ForecastRunRequest(
            product_code="AI_95",
            horizon_days=7,
            scenario={
                "retail_price_delta_pct": 2.5,
                "marketing_budget_delta_pct": 10.0,
            },
        )
    except ValidationError as exc:
        assert "marketing_budget_delta_pct" in str(exc)
    else:
        raise AssertionError("Expected unsupported scenario fields to be rejected")


def test_backtest_payload_accepts_missing_validation_summary() -> None:
    payload = BacktestPayload(
        product_code="AI_95",
        horizon_days=7,
        model_type="catboost",
        window_type="rolling",
        metrics=BacktestMetrics(mae=1.0, rmse=2.0, smape=3.0),
        comparison={
            "catboost": BacktestMetrics(mae=1.0, rmse=2.0, smape=3.0),
            "seasonal_naive": BacktestMetrics(mae=1.5, rmse=2.5, smape=4.0),
        },
        trained_at=datetime.now(UTC),
    )

    assert payload.validation_summary is None


def test_backtest_payload_accepts_populated_validation_summary() -> None:
    payload = BacktestPayload(
        product_code="AI_95",
        horizon_days=7,
        model_type="catboost",
        window_type="rolling",
        metrics=BacktestMetrics(mae=1.0, rmse=2.0, smape=3.0),
        comparison={
            "catboost": BacktestMetrics(mae=1.0, rmse=2.0, smape=3.0),
            "seasonal_naive": BacktestMetrics(mae=1.5, rmse=2.5, smape=4.0),
        },
        trained_at=datetime.now(UTC),
        validation_summary=ValidationSummary(
            status="OK",
            status_reason="CatBoost is evaluated on the test period.",
            train_period={"start": date(2025, 1, 1), "end": date(2025, 12, 31)},
            test_period={"start": date(2026, 1, 1), "end": date(2026, 1, 30)},
            observations={"total": None, "train": None, "test": 30},
            metrics={
                "catboost": {"mae": 1.0, "rmse": 2.0, "smape": 3.0},
                "seasonal_naive": {"mae": 1.5, "rmse": 2.5, "smape": 4.0},
                "improvement": {"mae_pct": 33.33, "rmse_pct": 20.0, "smape_pct": 25.0},
            },
            series=[
                {
                    "date": date(2026, 1, 1),
                    "actual": 100.0,
                    "catboost_prediction": 99.0,
                    "seasonal_naive_prediction": 95.0,
                }
            ],
        ),
    )

    dumped = payload.model_dump(mode="json")
    assert dumped["validation_summary"]["status"] == "OK"
    assert dumped["validation_summary"]["metrics"]["improvement"]["smape_pct"] == 25.0
