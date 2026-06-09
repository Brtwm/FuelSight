from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

import app.services.forecast_service as forecast_service_module
from app.services.forecast_service import ForecastService
from ml.backtesting import BacktestOutcome
from ml.features import MAX_LAG, HistoryPoint


class _RecordingSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0

    def add(self, obj):  # noqa: ANN001, ANN201
        self.added.append(obj)

    def commit(self) -> None:
        self.commits += 1


def _build_history(days: int = 120) -> list[HistoryPoint]:
    base_date = date(2025, 1, 1)
    result: list[HistoryPoint] = []
    for index in range(days):
        weekday_factor = 1.12 if (index % 7) in {4, 5} else 1.0
        volume = 11000.0 + (index * 4.5) + (300.0 * weekday_factor)
        result.append(
            HistoryPoint(
                day=base_date.fromordinal(base_date.toordinal() + index),
                volume_liters=volume,
                avg_retail_price_rub=58.0 + ((index % 11) * 0.05),
                avg_purchase_price_rub=52.0 + ((index % 13) * 0.04),
                gross_margin_rub_per_liter=5.5 + ((index % 9) * 0.02),
            )
        )
    return result


def test_run_forecast_uses_baseline_fallback_without_active_model(monkeypatch) -> None:
    service = ForecastService(session=SimpleNamespace())
    history = _build_history(90)

    monkeypatch.setattr(
        service,
        "_get_product",
        lambda _: SimpleNamespace(id=uuid4(), code="AI_95"),
    )
    monkeypatch.setattr(service, "_load_history", lambda _: history)
    monkeypatch.setattr(service, "_get_active_model", lambda *_: None)
    monkeypatch.setattr(service, "_store_forecast_rows", lambda **_: None)

    result = service.run_forecast(product_code="AI_95", horizon_days=7, scenario=None)

    assert result.data["model_status"] == "baseline_fallback"
    assert result.data["model_type"] == "seasonal_naive"
    assert len(result.data["forecast_points"]) == 7
    assert result.data["model_freshness"] == "degraded"
    assert result.data["retrain_status"] in {"degraded", "failed"}
    assert "external_context_quality" in result.data
    assert "event_context" in result.data
    assert "reference_overlays" in result.data
    assert result.meta["points"] == 7


def test_run_forecast_rejects_invalid_scenario() -> None:
    service = ForecastService(session=SimpleNamespace())
    with pytest.raises(ValueError, match="retail_price_delta_pct"):
        service._scenario_delta_pct({"retail_price_delta_pct": 100})


def test_run_backtest_writes_backtest_run_and_returns_metrics(monkeypatch, tmp_path: Path) -> None:
    session = _RecordingSession()
    settings = SimpleNamespace(model_artifacts_dir=str(tmp_path))
    service = ForecastService(session=session, settings=settings)
    history = _build_history(140)
    outcomes = {
        "seasonal_naive": BacktestOutcome(
            model_type="seasonal_naive",
            mae=10.0,
            rmse=12.0,
            smape=8.0,
            residual_std=2.0,
            folds=4,
            predictions=[95.0] * 40,
            actual=[100.0] * 40,
            dates=[point.day for point in history[-40:]],
        ),
        "catboost": BacktestOutcome(
            model_type="catboost",
            mae=8.0,
            rmse=10.0,
            smape=6.0,
            residual_std=1.5,
            folds=4,
            predictions=[98.0] * 40,
            actual=[100.0] * 40,
            dates=[point.day for point in history[-40:]],
        ),
    }

    fake_model = SimpleNamespace(
        version="20260404212000",
        trained_at=datetime(2026, 4, 4, 21, 20, 0),
    )

    monkeypatch.setattr(
        service,
        "_get_product",
        lambda _: SimpleNamespace(id=uuid4(), code="AI_95"),
    )
    monkeypatch.setattr(service, "_load_history", lambda _: history)
    monkeypatch.setattr(service, "_register_active_model", lambda **_: fake_model)
    monkeypatch.setattr(service, "_write_backtest_report", lambda **_: tmp_path / "report.json")
    monkeypatch.setattr(forecast_service_module, "is_catboost_available", lambda: True)
    monkeypatch.setattr(
        forecast_service_module,
        "run_rolling_backtest",
        lambda _history, *, model_type, **_kwargs: outcomes[model_type],
    )

    result = service.run_backtest(product_code="AI_95", horizon_days=7, window_type="rolling")

    assert result.data["product_code"] == "AI_95"
    assert result.data["horizon_days"] == 7
    assert "metrics" in result.data
    assert result.data["validation_summary"]["status"] == "OK"
    assert result.data["validation_summary"]["test_period"] == {
        "start": history[-40].day.isoformat(),
        "end": history[-1].day.isoformat(),
    }
    assert result.data["validation_summary"]["series"][0] == {
        "date": history[-40].day.isoformat(),
        "actual": 100.0,
        "catboost_prediction": 98.0,
        "seasonal_naive_prediction": 95.0,
    }
    assert result.data["validation_summary"]["metrics"]["improvement"]["smape_pct"] == 25.0
    assert session.added, "BacktestRun entry should be added to session"
    assert session.added[0].metrics_json["validation_summary"] == result.data["validation_summary"]
    assert session.commits == 1


def test_run_forecast_requires_minimum_history(monkeypatch) -> None:
    service = ForecastService(session=SimpleNamespace())
    short_history = _build_history(MAX_LAG)
    monkeypatch.setattr(
        service,
        "_get_product",
        lambda _: SimpleNamespace(id=uuid4(), code="AI_95"),
    )
    monkeypatch.setattr(service, "_load_history", lambda _: short_history)

    with pytest.raises(ValueError, match="Insufficient history"):
        service.run_forecast(product_code="AI_95", horizon_days=1, scenario=None)


def test_load_latest_feature_manifest_is_deterministic_by_run_date(tmp_path: Path) -> None:
    settings = SimpleNamespace(feature_store_dir=str(tmp_path))
    service = ForecastService(session=SimpleNamespace(), settings=settings)
    old_dir = tmp_path / "2025-04-01"
    new_dir = tmp_path / "2025-04-02"
    old_dir.mkdir(parents=True, exist_ok=True)
    new_dir.mkdir(parents=True, exist_ok=True)

    older = old_dir / "feature_refresh_manifest_old.json"
    newer = new_dir / "feature_refresh_manifest_new.json"
    older.write_text(
        '{"run_id":"old","run_date":"2025-04-01","coverage_ratio":0.99}',
        encoding="utf-8",
    )
    newer.write_text(
        '{"run_id":"new","run_date":"2025-04-02","coverage_ratio":0.98}',
        encoding="utf-8",
    )
    older.write_text(older.read_text(encoding="utf-8"), encoding="utf-8")

    manifest = service._load_latest_feature_refresh_manifest()
    assert manifest is not None
    assert manifest["run_id"] == "new"


def _validation_series(points: int = 30) -> list[dict[str, object]]:
    base_date = date(2026, 1, 1)
    return [
        {
            "date": base_date.fromordinal(base_date.toordinal() + index).isoformat(),
            "actual": 100.0,
            "catboost_prediction": 98.0,
            "seasonal_naive_prediction": 95.0,
        }
        for index in range(points)
    ]


def test_validation_summary_computes_improvement_percentages() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={
            "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
            "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
        },
        training_window={"start_date": "2025-01-01", "end_date": "2025-12-31"},
        observations={"test": 30},
        series=_validation_series(30),
    )

    assert summary["status"] == "OK"
    assert summary["train_period"] == {"start": "2025-01-01", "end": "2025-12-31"}
    assert summary["test_period"] == {"start": "2026-01-01", "end": "2026-01-30"}
    assert summary["metrics"]["improvement"] == {
        "mae_pct": 20.0,
        "rmse_pct": 25.0,
        "smape_pct": 25.0,
    }


def test_validation_summary_zero_baseline_denominator_returns_null_improvement() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={
            "catboost": {"mae": 1.0, "rmse": 2.0, "smape": 3.0},
            "seasonal_naive": {"mae": 0.0, "rmse": 0.0, "smape": 0.0},
        },
        observations={"test": 30},
        series=_validation_series(30),
    )

    assert summary["status"] == "LIMITED"
    assert summary["metrics"]["improvement"] == {
        "mae_pct": None,
        "rmse_pct": None,
        "smape_pct": None,
    }


def test_validation_summary_missing_baseline_is_limited() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={"catboost": {"mae": 1.0, "rmse": 2.0, "smape": 3.0}},
        observations={"test": 30},
        series=_validation_series(30),
    )

    assert summary["status"] == "LIMITED"
    assert summary["status_reason"] == "Seasonal Naive metrics are unavailable."


def test_validation_summary_missing_catboost_is_limited() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={"seasonal_naive": {"mae": 1.0, "rmse": 2.0, "smape": 3.0}},
        observations={"test": 30},
        series=_validation_series(30),
    )

    assert summary["status"] == "LIMITED"
    assert summary["status_reason"] == "CatBoost metrics are unavailable."


def test_validation_summary_catboost_worse_by_smape_is_limited() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={
            "catboost": {"mae": 1.0, "rmse": 2.0, "smape": 5.0},
            "seasonal_naive": {"mae": 1.0, "rmse": 2.0, "smape": 3.0},
        },
        observations={"test": 30},
        series=_validation_series(30),
    )

    assert summary["status"] == "LIMITED"
    assert summary["status_reason"] == "CatBoost is worse than Seasonal Naive by SMAPE."


def test_validation_summary_fewer_than_min_test_observations_is_limited() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={
            "catboost": {"mae": 1.0, "rmse": 2.0, "smape": 3.0},
            "seasonal_naive": {"mae": 2.0, "rmse": 3.0, "smape": 4.0},
        },
        observations={"test": 29},
        series=_validation_series(29),
    )

    assert summary["status"] == "LIMITED"
    assert "fewer than 30" in summary["status_reason"]


def test_validation_summary_without_evaluation_data_is_unknown() -> None:
    summary = ForecastService._build_validation_summary(comparison=None)

    assert summary["status"] == "UNKNOWN"
    assert summary["metrics"] is None
