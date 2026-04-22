from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.forecast_service import ForecastService
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

    result = service.run_backtest(product_code="AI_95", horizon_days=7, window_type="rolling")

    assert result.data["product_code"] == "AI_95"
    assert result.data["horizon_days"] == 7
    assert "metrics" in result.data
    assert session.added, "BacktestRun entry should be added to session"
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
