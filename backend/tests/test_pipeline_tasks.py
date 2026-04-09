from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.pipeline import tasks


class _FakeResult:
    def __init__(self, rows):  # noqa: ANN001
        self._rows = rows

    def mappings(self):  # noqa: ANN201
        return self._rows


class _FakeSession:
    def __init__(self, rows):  # noqa: ANN001
        self._rows = rows

    def execute(self, _query):  # noqa: ANN001, ANN201
        return _FakeResult(self._rows)


class _FakeSessionContext:
    def __init__(self, rows):  # noqa: ANN001
        self._session = _FakeSession(rows)

    def __enter__(self):  # noqa: ANN201
        return self._session

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        return False


@dataclass
class _DummySettings:
    news_index_dir: str
    feature_store_dir: str
    external_cache_dir: str


def test_ingest_external_indicators_daily_creates_manifest(monkeypatch, tmp_path: Path) -> None:
    class _NoopSession:
        pass

    class _NoopSessionContext:
        def __enter__(self):  # noqa: ANN201
            return _NoopSession()

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    class _FakeIngestResult:
        run_id = "run-001"
        expected_points = 60
        written_points = 60
        coverage_ratio = 1.0
        fallback_ratio = 0.0
        provider_mode_counts = {"live": 60}
        indicator_coverage = []
        cache_dir = str(tmp_path / "external")

        def to_manifest(self, *, manifest_path: str):  # noqa: ANN001, ANN201
            return {
                "run_id": self.run_id,
                "run_date": "2025-02-01",
                "window": {"start_date": "2025-01-03", "end_date": "2025-02-01"},
                "status": "ok",
                "expected_points": self.expected_points,
                "written_points": self.written_points,
                "coverage_ratio": self.coverage_ratio,
                "provider_mode_counts": self.provider_mode_counts,
                "fallback_ratio": self.fallback_ratio,
                "indicator_coverage": [],
                "artifacts": {"manifest_path": manifest_path, "cache_dir": self.cache_dir},
            }

    class _FakeExternalIndicatorsService:
        def __init__(self, session, settings):  # noqa: ANN001
            self._session = session
            self._settings = settings

        def ingest_range(self, **kwargs):  # noqa: ANN003, ANN201
            assert kwargs["prefer_live"] is True
            return _FakeIngestResult()

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _NoopSessionContext())
    monkeypatch.setattr(tasks, "ExternalIndicatorsService", _FakeExternalIndicatorsService)
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
    )

    result = tasks.ingest_external_indicators_daily(
        settings=settings,
        provider="auto",
        run_date=date(2025, 2, 1),
        lookback_days=30,
    )

    assert result["status"] == "success"
    manifest_path = Path(result["manifest_path"])
    assert manifest_path.exists()
    payload = manifest_path.read_text(encoding="utf-8")
    assert "fallback_ratio" in payload
    assert "coverage_ratio" in payload
    assert result["window"]["lookback_days"] == 30


def test_build_feature_store_daily_exports_csv(monkeypatch, tmp_path: Path) -> None:
    rows = []
    for day_index in range(40):
        rows.append(
            {
                "product_code": "AI_95",
                "date": date(2025, 1, 1).fromordinal(date(2025, 1, 1).toordinal() + day_index),
                "volume_liters": 10000 + (day_index * 10),
                "avg_retail_price_rub": 58.0,
                "avg_purchase_price_rub": 52.0,
                "gross_margin_rub_per_liter": 6.0,
            }
        )

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _FakeSessionContext(rows))
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
    )

    result = tasks.build_feature_store_daily(run_date=date(2025, 2, 1), settings=settings)

    assert result["status"] == "success"
    assert result["feature_rows"] > 0
    output_path = Path(result["output_path"])
    assert output_path.exists()
    csv_text = output_path.read_text(encoding="utf-8")
    assert "product_code" in csv_text
    assert "target_volume_liters" in csv_text


def test_train_models_weekly_collects_success_and_skips(monkeypatch, tmp_path: Path) -> None:
    class _NoopSession:
        pass

    class _NoopSessionContext:
        def __enter__(self):  # noqa: ANN201
            return _NoopSession()

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    class _FakeForecastService:
        def __init__(self, session, settings):  # noqa: ANN001
            self._session = session
            self._settings = settings

        def run_backtest(self, *, product_code: str, horizon_days: int, window_type: str):  # noqa: ANN201
            if horizon_days == 30:
                raise ValueError("Insufficient history for backtest")
            return type(
                "Result",
                (),
                {
                    "data": {
                        "model_type": "seasonal_naive",
                        "model_version": f"{product_code}_{horizon_days}",
                        "metrics": {"smape": 5.0},
                    }
                },
            )()

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _NoopSessionContext())
    monkeypatch.setattr(tasks, "ForecastService", _FakeForecastService)
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
    )

    result = tasks.train_models_weekly(
        settings=settings,
        product_codes=["AI_95"],
        horizons=[1, 30],
    )

    assert result["status"] == "success"
    assert result["total_runs"] == 2
    assert result["success_runs"] == 1
    assert result["skipped_runs"] == 1
