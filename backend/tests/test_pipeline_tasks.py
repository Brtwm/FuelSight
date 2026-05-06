from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from types import SimpleNamespace

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

    def scalars(self, _query):  # noqa: ANN001, ANN201
        return []


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
    model_artifacts_dir: str


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
        model_artifacts_dir=str(tmp_path / "models"),
    )

    result = tasks.ingest_external_indicators_daily(
        settings=settings,
        provider="auto",
        run_date=date(2025, 2, 1),
        lookback_days=30,
    )

    assert result["status"] == "ok"
    assert result["quality_status"] == "ok"
    manifest_path = Path(result["manifest_path"])
    assert manifest_path.exists()
    payload = manifest_path.read_text(encoding="utf-8")
    assert "fallback_ratio" in payload
    assert "coverage_ratio" in payload
    assert result["window"]["lookback_days"] == 30


def test_refresh_rag_index_daily_writes_chunks(monkeypatch, tmp_path: Path) -> None:
    class _FakeSession:
        def __init__(self) -> None:
            self.added = []
            self.committed = False

        def scalars(self, _query):  # noqa: ANN001, ANN201
            return []

        def execute(self, _query):  # noqa: ANN001
            return None

        def add_all(self, rows):  # noqa: ANN001
            self.added.extend(rows)

        def commit(self):
            self.committed = True

    fake_session = _FakeSession()

    class _FakeSessionContext:
        def __enter__(self):  # noqa: ANN201
            return fake_session

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    class _FakeRagIndexService:
        @staticmethod
        def build_news_raw_chunks(rows):  # noqa: ANN001, ANN201
            return [SimpleNamespace(source_type="news_raw")] if list(rows) == [] else []

        @staticmethod
        def build_news_digest_chunks(rows):  # noqa: ANN001, ANN201
            return [SimpleNamespace(source_type="news_digest")] if list(rows) == [] else []

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _FakeSessionContext())
    monkeypatch.setattr(tasks, "RagIndexService", _FakeRagIndexService)
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
        model_artifacts_dir=str(tmp_path / "models"),
    )

    result = tasks.refresh_rag_index_daily(settings=settings)

    assert result["status"] == "ok"
    assert result["written_chunks"] == 2
    assert result["index_replaced"] is True
    assert [item.source_type for item in fake_session.added] == ["news_raw", "news_digest"]
    assert fake_session.committed is True


def test_refresh_rag_index_daily_preserves_existing_index_when_no_chunks(
    monkeypatch, tmp_path: Path
) -> None:
    class _FakeSession:
        def __init__(self) -> None:
            self.deleted = False
            self.added = []
            self.committed = False

        def scalars(self, _query):  # noqa: ANN001, ANN201
            return []

        def execute(self, _query):  # noqa: ANN001
            self.deleted = True
            return None

        def add_all(self, rows):  # noqa: ANN001
            self.added.extend(rows)

        def commit(self):
            self.committed = True

    fake_session = _FakeSession()

    class _FakeSessionContext:
        def __enter__(self):  # noqa: ANN201
            return fake_session

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    class _FakeRagIndexService:
        @staticmethod
        def build_news_raw_chunks(rows):  # noqa: ANN001, ANN201
            return []

        @staticmethod
        def build_news_digest_chunks(rows):  # noqa: ANN001, ANN201
            return []

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _FakeSessionContext())
    monkeypatch.setattr(tasks, "RagIndexService", _FakeRagIndexService)
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
        model_artifacts_dir=str(tmp_path / "models"),
    )

    result = tasks.refresh_rag_index_daily(settings=settings)

    assert result["status"] == "degraded"
    assert result["quality_status"] == "degraded"
    assert result["written_chunks"] == 0
    assert result["index_replaced"] is False
    assert fake_session.deleted is False
    assert fake_session.added == []
    assert fake_session.committed is False
    assert Path(result["manifest_path"]).exists()


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

    class _FakeExternalIndicatorsRepository:
        def __init__(self, _session):  # noqa: ANN001
            pass

        def get_points_with_mode(self, **_kwargs):  # noqa: ANN003, ANN201
            return {}

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _FakeSessionContext(rows))
    monkeypatch.setattr(tasks, "ExternalIndicatorsRepository", _FakeExternalIndicatorsRepository)
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
        model_artifacts_dir=str(tmp_path / "models"),
    )

    result = tasks.build_feature_store_daily(run_date=date(2025, 2, 1), settings=settings)

    assert result["status"] == "degraded"
    assert result["quality_status"] == "degraded"
    assert result["reasons"]
    assert result["feature_rows"] > 0
    output_path = Path(result["output_path"])
    assert output_path.exists()
    csv_text = output_path.read_text(encoding="utf-8")
    assert "product_code" in csv_text
    assert "target_volume_liters" in csv_text
    assert "manifest_path" in result


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
        model_artifacts_dir=str(tmp_path / "models"),
    )

    run_day = date.today().isoformat()
    feature_manifest_dir = Path(settings.feature_store_dir) / run_day
    feature_manifest_dir.mkdir(parents=True, exist_ok=True)
    (feature_manifest_dir / "feature_refresh_manifest_seed.json").write_text(
        json.dumps(
            {
                "run_id": "seed",
                "run_date": run_day,
                "coverage_ratio": 0.97,
                "fallback_ratio": 0.1,
                "provider_mode_counts": {"live": 42},
            }
        ),
        encoding="utf-8",
    )

    result = tasks.train_models_weekly(
        settings=settings,
        product_codes=["AI_95"],
        horizons=[1, 30],
    )

    assert result["status"] in {"success", "warning"}
    assert result["total_runs"] == 2
    assert result["success_runs"] == 1
    assert result["skipped_runs"] == 1
    assert result["train_backtest_manifest_path"]
    assert result["model_freshness_manifest_path"]


def test_load_latest_feature_manifest_is_deterministic_by_run_date(tmp_path: Path) -> None:
    root = tmp_path / "features"
    old_dir = root / "2025-04-01"
    new_dir = root / "2025-04-02"
    old_dir.mkdir(parents=True, exist_ok=True)
    new_dir.mkdir(parents=True, exist_ok=True)

    older = old_dir / "feature_refresh_manifest_old.json"
    newer = new_dir / "feature_refresh_manifest_new.json"
    older.write_text(
        json.dumps({"run_id": "old", "run_date": "2025-04-01", "coverage_ratio": 0.99}),
        encoding="utf-8",
    )
    newer.write_text(
        json.dumps({"run_id": "new", "run_date": "2025-04-02", "coverage_ratio": 0.98}),
        encoding="utf-8",
    )

    # Break mtime ordering intentionally: older file gets newer mtime.
    old_content = older.read_text(encoding="utf-8")
    older.write_text(old_content, encoding="utf-8")

    manifest = tasks._load_latest_feature_refresh_manifest(str(root))

    assert manifest is not None
    assert manifest["run_id"] == "new"


def test_refresh_news_daily_writes_manifest(monkeypatch, tmp_path: Path) -> None:
    class _NoopSession:
        pass

    class _NoopSessionContext:
        def __enter__(self):  # noqa: ANN201
            return _NoopSession()

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    class _FakeNewsService:
        def __init__(self, session, settings):  # noqa: ANN001
            self._session = session
            self._settings = settings

        def refresh_news(self, *, provider_mode: str, lookback_days: int):  # noqa: ANN201
            assert provider_mode == "auto"
            assert lookback_days == 14
            return type(
                "NewsRefreshResult",
                (),
                {
                    "status": "warning",
                    "imported_news_count": 8,
                    "created_digests": 2,
                    "provider_mode": "cached",
                    "news_freshness": "fresh",
                    "quality_status": "warning",
                    "provider_mode_counts": {"cached": 8},
                    "written_news_count": 8,
                    "coverage_ratio": 0.75,
                    "cache_dir": str(tmp_path / "news"),
                    "last_success_at": "2026-04-22T12:00:00+00:00",
                    "provider_diagnostics": [],
                },
            )()

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _NoopSessionContext())
    monkeypatch.setattr(tasks, "NewsService", _FakeNewsService)
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
        model_artifacts_dir=str(tmp_path / "models"),
    )

    result = tasks.refresh_news_daily(
        settings=settings,
        provider="auto",
        run_date=date(2026, 4, 22),
        lookback_days=14,
    )

    assert result["status"] == "warning"
    assert result["provider_mode"] == "cached"
    assert result["written_news_count"] == 8
    manifest_path = Path(result["manifest_path"])
    assert manifest_path.exists()
    payload = manifest_path.read_text(encoding="utf-8")
    assert "coverage_ratio" in payload
    assert "provider_mode_counts" in payload


def test_build_defense_report_uses_service_and_returns_artifacts(
    monkeypatch, tmp_path: Path
) -> None:
    class _NoopSession:
        pass

    class _NoopSessionContext:
        def __enter__(self):  # noqa: ANN201
            return _NoopSession()

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    class _FakeReport:
        run_id = "run-001"
        profile = "offline-safe"
        overall_status = "ok"
        artifacts = {
            "json": str(tmp_path / "defense-report.json"),
            "pdf": str(tmp_path / "defense-report.pdf"),
        }

        def model_dump(self, *, mode: str):  # noqa: ANN001, ANN201
            assert mode == "json"
            return {
                "run_id": self.run_id,
                "profile": self.profile,
                "overall_status": self.overall_status,
                "artifacts": self.artifacts,
            }

    class _FakeDefenseReportService:
        def __init__(self, *, session, settings):  # noqa: ANN001
            self.session = session
            self.settings = settings

        def build_report(self, *, profile):  # noqa: ANN001, ANN201
            assert profile == "offline-safe"
            return _FakeReport()

    monkeypatch.setattr(tasks, "SessionLocal", lambda: _NoopSessionContext())
    monkeypatch.setattr(tasks, "DefenseReportService", _FakeDefenseReportService)
    settings = _DummySettings(
        news_index_dir=str(tmp_path / "news"),
        feature_store_dir=str(tmp_path / "features"),
        external_cache_dir=str(tmp_path / "external"),
        model_artifacts_dir=str(tmp_path / "models"),
    )

    result = tasks.build_defense_report(profile="offline-safe", settings=settings)

    assert result["overall_status"] == "ok"
    assert result["artifacts"]["pdf"].endswith("defense-report.pdf")
