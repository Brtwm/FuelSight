from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

import app.services.forecast_service as forecast_service_module
from app.services.forecast_service import MIN_TEST_OBSERVATIONS, ForecastService
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


class _LatestBacktestSession:
    def __init__(self, latest: object | None) -> None:
        self.latest = latest

    def scalar(self, _statement):  # noqa: ANN001, ANN201
        return self.latest


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


def test_run_backtest_uses_enough_folds_for_representative_validation_period(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session = _RecordingSession()
    settings = SimpleNamespace(model_artifacts_dir=str(tmp_path))
    service = ForecastService(session=session, settings=settings)
    history = _build_history(140)
    calls: list[dict[str, object]] = []
    outcomes = {
        "seasonal_naive": BacktestOutcome(
            model_type="seasonal_naive",
            mae=10.0,
            rmse=12.0,
            smape=8.0,
            residual_std=2.0,
            folds=MIN_TEST_OBSERVATIONS,
            predictions=[95.0] * MIN_TEST_OBSERVATIONS,
            actual=[100.0] * MIN_TEST_OBSERVATIONS,
            dates=[point.day for point in history[-MIN_TEST_OBSERVATIONS:]],
        ),
        "catboost": BacktestOutcome(
            model_type="catboost",
            mae=8.0,
            rmse=10.0,
            smape=6.0,
            residual_std=1.5,
            folds=MIN_TEST_OBSERVATIONS,
            predictions=[98.0] * MIN_TEST_OBSERVATIONS,
            actual=[100.0] * MIN_TEST_OBSERVATIONS,
            dates=[point.day for point in history[-MIN_TEST_OBSERVATIONS:]],
        ),
    }

    def fake_run_rolling_backtest(_history, *, model_type, **kwargs):  # noqa: ANN001, ANN202
        calls.append({"model_type": model_type, **kwargs})
        return outcomes[model_type]

    monkeypatch.setattr(
        service,
        "_get_product",
        lambda _: SimpleNamespace(id=uuid4(), code="AI_95"),
    )
    monkeypatch.setattr(service, "_load_history", lambda _: history)
    monkeypatch.setattr(
        service,
        "_register_active_model",
        lambda **_: SimpleNamespace(
            version="20260404212000",
            trained_at=datetime(2026, 4, 4, 21, 20, 0),
            metrics_json={},
        ),
    )
    monkeypatch.setattr(service, "_write_backtest_report", lambda **_: tmp_path / "report.json")
    monkeypatch.setattr(forecast_service_module, "is_catboost_available", lambda: True)
    monkeypatch.setattr(
        forecast_service_module,
        "run_rolling_backtest",
        fake_run_rolling_backtest,
    )

    service.run_backtest(product_code="AI_95", horizon_days=7, window_type="rolling")

    assert calls
    assert {call["model_type"] for call in calls} == {"seasonal_naive", "catboost"}
    assert all(call["max_folds"] == MIN_TEST_OBSERVATIONS for call in calls)


def test_run_backtest_selects_baseline_when_catboost_is_worse(
    monkeypatch,
    tmp_path: Path,
) -> None:
    session = _RecordingSession()
    settings = SimpleNamespace(model_artifacts_dir=str(tmp_path))
    service = ForecastService(session=session, settings=settings)
    history = _build_history(140)
    registered_winners: list[str] = []
    outcomes = {
        "seasonal_naive": BacktestOutcome(
            model_type="seasonal_naive",
            mae=100.0,
            rmse=120.0,
            smape=10.0,
            residual_std=2.0,
            folds=MIN_TEST_OBSERVATIONS,
            predictions=[95.0] * MIN_TEST_OBSERVATIONS,
            actual=[100.0] * MIN_TEST_OBSERVATIONS,
            dates=[point.day for point in history[-MIN_TEST_OBSERVATIONS:]],
        ),
        "catboost": BacktestOutcome(
            model_type="catboost",
            mae=140.0,
            rmse=170.0,
            smape=14.0,
            residual_std=3.0,
            folds=MIN_TEST_OBSERVATIONS,
            predictions=[90.0] * MIN_TEST_OBSERVATIONS,
            actual=[100.0] * MIN_TEST_OBSERVATIONS,
            dates=[point.day for point in history[-MIN_TEST_OBSERVATIONS:]],
        ),
    }

    def fake_register_active_model(**kwargs):  # noqa: ANN003, ANN202
        registered_winners.append(kwargs["winner"].model_type)
        return SimpleNamespace(
            version="20260404212000",
            trained_at=datetime(2026, 4, 4, 21, 20, 0),
            metrics_json={},
        )

    monkeypatch.setattr(
        service,
        "_get_product",
        lambda _: SimpleNamespace(id=uuid4(), code="AI_95"),
    )
    monkeypatch.setattr(service, "_load_history", lambda _: history)
    monkeypatch.setattr(service, "_register_active_model", fake_register_active_model)
    monkeypatch.setattr(service, "_write_backtest_report", lambda **_: tmp_path / "report.json")
    monkeypatch.setattr(forecast_service_module, "is_catboost_available", lambda: True)
    monkeypatch.setattr(
        forecast_service_module,
        "run_rolling_backtest",
        lambda _history, *, model_type, **_kwargs: outcomes[model_type],
    )

    result = service.run_backtest(product_code="AI_95", horizon_days=7, window_type="rolling")

    assert registered_winners == ["seasonal_naive"]
    assert result.data["model_type"] == "seasonal_naive"
    assert result.data["metrics"] == {"mae": 100.0, "rmse": 120.0, "smape": 10.0}
    assert result.data["validation_summary"]["status"] == "LIMITED"
    assert result.data["validation_summary"]["status_reason"] == (
        "CatBoost is worse than Seasonal Naive by SMAPE."
    )
    assert session.added[0].metrics_json["winner"] == "seasonal_naive"


def test_validation_series_collapses_duplicate_dates_and_averages_predictions() -> None:
    first_day = date(2026, 6, 9)
    second_day = date(2026, 6, 10)
    catboost_outcome = BacktestOutcome(
        model_type="catboost",
        mae=8.0,
        rmse=10.0,
        smape=4.0,
        residual_std=1.0,
        folds=2,
        predictions=[98.0, 102.0, 110.0],
        actual=[100.0, 100.0, 112.0],
        dates=[first_day, first_day, second_day],
    )
    baseline_outcome = BacktestOutcome(
        model_type="seasonal_naive",
        mae=10.0,
        rmse=12.0,
        smape=5.0,
        residual_std=1.5,
        folds=2,
        predictions=[96.0, 100.0, 108.0],
        actual=[100.0, 100.0, 112.0],
        dates=[first_day, first_day, second_day],
    )

    series = ForecastService._build_validation_series(
        catboost_outcome=catboost_outcome,
        baseline_outcome=baseline_outcome,
    )

    assert series == [
        {
            "date": "2026-06-09",
            "actual": 100.0,
            "catboost_prediction": 100.0,
            "seasonal_naive_prediction": 98.0,
        },
        {
            "date": "2026-06-10",
            "actual": 112.0,
            "catboost_prediction": 110.0,
            "seasonal_naive_prediction": 108.0,
        },
    ]


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


def test_validation_summary_uses_unique_series_dates_for_test_observations() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={
            "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
            "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
        },
        observations={"test": 30},
        series=[
            {
                "date": "2026-01-01",
                "actual": 100.0,
                "catboost_prediction": 98.0,
                "seasonal_naive_prediction": 95.0,
            },
            {
                "date": "2026-01-01",
                "actual": 100.0,
                "catboost_prediction": 100.0,
                "seasonal_naive_prediction": 97.0,
            },
            {
                "date": "2026-01-02",
                "actual": 110.0,
                "catboost_prediction": 108.0,
                "seasonal_naive_prediction": 104.0,
            },
        ],
    )

    assert summary["observations"] == {"total": None, "train": None, "test": 2}
    assert summary["test_period"] == {"start": "2026-01-01", "end": "2026-01-02"}
    assert summary["status"] == "LIMITED"
    assert "fewer than 30" in summary["status_reason"]
    assert summary["series"] == [
        {
            "date": "2026-01-01",
            "actual": 100.0,
            "catboost_prediction": 99.0,
            "seasonal_naive_prediction": 96.0,
        },
        {
            "date": "2026-01-02",
            "actual": 110.0,
            "catboost_prediction": 108.0,
            "seasonal_naive_prediction": 104.0,
        },
    ]


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
    assert summary["metrics"]["improvement"] == {
        "mae_pct": None,
        "rmse_pct": None,
        "smape_pct": None,
    }


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
    assert summary["metrics"]["improvement"]["smape_pct"] == -66.67


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


def test_validation_summary_with_metrics_but_no_dated_series_is_limited() -> None:
    summary = ForecastService._build_validation_summary(
        comparison={
            "catboost": {"mae": 1.0, "rmse": 2.0, "smape": 3.0},
            "seasonal_naive": {"mae": 2.0, "rmse": 3.0, "smape": 4.0},
        },
        observations={"test": 30},
        series=[],
    )

    assert summary["status"] == "LIMITED"
    assert summary["test_period"] is None
    assert summary["series"] == []
    assert "dated test-period series" in summary["status_reason"]


def test_validation_summary_without_evaluation_data_is_unknown() -> None:
    summary = ForecastService._build_validation_summary(comparison=None)

    assert summary["status"] == "UNKNOWN"
    assert summary["metrics"] is None


def _latest_backtest_run(metrics_json: dict[str, object]) -> SimpleNamespace:
    timestamp = datetime(2026, 4, 4, 20, 0, 0)
    return SimpleNamespace(
        model_type="catboost",
        horizon_days=7,
        window_type="rolling",
        status="success",
        metrics_json=metrics_json,
        started_at=timestamp,
        finished_at=timestamp,
    )


def _latest_backtest_service(latest: object | None) -> ForecastService:
    service = ForecastService(session=_LatestBacktestSession(latest))
    service._get_product = lambda _: SimpleNamespace(id=uuid4(), code="AI_95")  # type: ignore[method-assign]
    service._resolve_health_payload = lambda **_: {  # type: ignore[method-assign]
        "model_freshness": "fresh",
        "training_window": {"start_date": "2025-01-01", "end_date": "2025-12-31"},
        "baseline_comparison": None,
        "feature_sources": [],
        "retrain_status": "ok",
        "provider_mode": "cached",
    }
    service._external_context_service = SimpleNamespace(
        build_external_context_quality=lambda: {"quality_status": "ok"}
    )
    return service


def test_get_latest_backtest_returns_normalized_stored_validation_summary() -> None:
    stored_summary = {
        "status": "OK",
        "status_reason": "CatBoost is evaluated on the test period.",
        "train_period": {"start": "2025-01-01", "end": "2025-12-31"},
        "test_period": {"start": "2026-01-01", "end": "2026-01-30"},
        "observations": {"total": 395, "train": 365, "test": 30},
        "metrics": {
            "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
            "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
            "improvement": {"mae_pct": 20.0, "rmse_pct": 25.0, "smape_pct": 25.0},
        },
        "series": _validation_series(30),
    }
    service = _latest_backtest_service(
        _latest_backtest_run(
            {
                "winner_metrics": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                "comparison": {
                    "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                    "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
                },
                "model_version": "20260404200000",
                "validation_summary": stored_summary,
            }
        )
    )

    result = service.get_latest_backtest(product_code="AI_95", horizon_days=7)

    assert result.data is not None
    summary = result.data["validation_summary"]
    assert summary["status"] == "OK"
    assert summary["status_reason"] == (
        "CatBoost is evaluated on the test period and is not worse than Seasonal Naive "
        "by SMAPE."
    )
    assert summary["observations"] == {"total": 395, "train": 365, "test": 30}
    assert summary["test_period"] == {"start": "2026-01-01", "end": "2026-01-30"}
    assert len(summary["series"]) == 30
    assert result.meta["external_context"] == {"quality_status": "ok"}


def test_get_latest_backtest_recomputes_health_from_run_timestamp() -> None:
    service = _latest_backtest_service(
        _latest_backtest_run(
            {
                "winner_metrics": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                "comparison": {
                    "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                    "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
                },
                "model_version": "20260404200000",
                "model_freshness": "degraded",
                "retrain_status": "degraded",
                "validation_summary": {
                    "status": "OK",
                    "status_reason": "CatBoost is evaluated on the test period.",
                    "train_period": {"start": "2025-01-01", "end": "2025-12-31"},
                    "test_period": {"start": "2026-01-01", "end": "2026-01-30"},
                    "observations": {"total": 395, "train": 365, "test": 30},
                    "metrics": {
                        "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                        "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
                        "improvement": {"mae_pct": 20.0, "rmse_pct": 25.0, "smape_pct": 25.0},
                    },
                    "series": _validation_series(30),
                },
            }
        )
    )
    service._session.latest.finished_at = datetime.now(UTC)
    service._session.latest.started_at = datetime.now(UTC)

    result = service.get_latest_backtest(product_code="AI_95", horizon_days=7)

    assert result.data is not None
    assert result.data["model_freshness"] == "fresh"
    assert result.data["retrain_status"] == "ok"
    assert result.meta["model_freshness"] == "fresh"


def test_fresh_model_health_does_not_become_stale_when_external_context_is_degraded() -> None:
    service = ForecastService(session=SimpleNamespace())
    freshness, retrain_status = service._compute_model_health(
        model_trained_at=datetime.now(UTC) - timedelta(hours=2),
        model_status="active",
        feature_manifest={
            "run_date": date.today().isoformat(),
            "coverage_ratio": 0.1,
            "fallback_ratio": 0.9,
        },
    )

    assert freshness == "fresh"
    assert retrain_status == "ok"


def test_get_latest_backtest_normalizes_legacy_duplicate_validation_series() -> None:
    service = _latest_backtest_service(
        _latest_backtest_run(
            {
                "winner_metrics": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                "comparison": {
                    "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                    "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
                },
                "model_version": "20260404200000",
                "validation_summary": {
                    "status": "OK",
                    "status_reason": "legacy OK",
                    "train_period": {"start": "2025-01-01", "end": "2025-12-31"},
                    "test_period": {"start": "2026-01-01", "end": "2026-01-30"},
                    "observations": {"total": 395, "train": 365, "test": 30},
                    "metrics": {
                        "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                        "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
                        "improvement": {"mae_pct": 20.0, "rmse_pct": 25.0, "smape_pct": 25.0},
                    },
                    "series": [
                        {
                            "date": "2026-01-01",
                            "actual": 100.0,
                            "catboost_prediction": 98.0,
                            "seasonal_naive_prediction": 95.0,
                        },
                        {
                            "date": "2026-01-01",
                            "actual": 100.0,
                            "catboost_prediction": 100.0,
                            "seasonal_naive_prediction": 97.0,
                        },
                        {
                            "date": "2026-01-02",
                            "actual": 110.0,
                            "catboost_prediction": 108.0,
                            "seasonal_naive_prediction": 104.0,
                        },
                    ],
                },
            }
        )
    )

    result = service.get_latest_backtest(product_code="AI_95", horizon_days=7)

    assert result.data is not None
    summary = result.data["validation_summary"]
    assert summary["status"] == "LIMITED"
    assert "fewer than 30" in summary["status_reason"]
    assert summary["observations"] == {"total": 395, "train": 365, "test": 2}
    assert summary["test_period"] == {"start": "2026-01-01", "end": "2026-01-02"}
    assert summary["series"] == [
        {
            "date": "2026-01-01",
            "actual": 100.0,
            "catboost_prediction": 99.0,
            "seasonal_naive_prediction": 96.0,
        },
        {
            "date": "2026-01-02",
            "actual": 110.0,
            "catboost_prediction": 108.0,
            "seasonal_naive_prediction": 104.0,
        },
    ]


def test_get_latest_backtest_builds_fallback_validation_summary_for_legacy_metrics() -> None:
    service = _latest_backtest_service(
        _latest_backtest_run(
            {
                "winner_metrics": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                "comparison": {
                    "catboost": {"mae": 80.0, "rmse": 90.0, "smape": 6.0},
                    "seasonal_naive": {"mae": 100.0, "rmse": 120.0, "smape": 8.0},
                },
                "model_version": "20260404200000",
            }
        )
    )

    result = service.get_latest_backtest(product_code="AI_95", horizon_days=7)

    assert result.data is not None
    summary = result.data["validation_summary"]
    assert summary["status"] == "LIMITED"
    assert summary["status_reason"] == (
        "Backtest metrics are available, but test observations are unknown."
    )
    assert summary["train_period"] == {"start": "2025-01-01", "end": "2025-12-31"}
    assert summary["metrics"]["improvement"]["smape_pct"] == 25.0
    assert summary["series"] == []
