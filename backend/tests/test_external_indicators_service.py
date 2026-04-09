from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from app.integrations.external_indicators.base import ExternalIndicatorsAdapter
from app.integrations.external_indicators.cache import ExternalIndicatorsCacheManager
from app.integrations.external_indicators.registry import ExternalIndicatorsRegistry
from app.integrations.external_indicators.types import ExternalIndicatorPoint
from app.repositories import ExternalIndicatorUpsertRow
from app.services.external_indicators_service import ExternalIndicatorsService


@dataclass
class _DummySettings:
    external_cache_dir: str
    external_indicators_mode: str = "live"
    enable_external_indicators: bool = True


class _InMemoryRepo:
    def __init__(self) -> None:
        self.rows: list[ExternalIndicatorUpsertRow] = []

    def upsert_many(self, rows: list[ExternalIndicatorUpsertRow]) -> int:
        self.rows.extend(rows)
        return len(rows)

    def get_coverage_summary(self, *, start_date: date, end_date: date, indicator_codes: list[str]):
        expected = (end_date - start_date).days + 1
        result: list[dict] = []
        for code in indicator_codes:
            dates = sorted(
                {
                    item.indicator_date
                    for item in self.rows
                    if item.indicator_code == code and start_date <= item.indicator_date <= end_date
                }
            )
            latest = None
            for item in reversed(self.rows):
                if item.indicator_code == code:
                    latest = item
                    break
            result.append(
                {
                    "indicator_code": code,
                    "expected_days": expected,
                    "actual_days": len(dates),
                    "coverage_ratio": (len(dates) / expected) if expected > 0 else 0.0,
                    "latest_date": latest.indicator_date if latest else None,
                    "latest_mode": latest.provider_mode if latest else None,
                }
            )
        return result

    def get_series(self, *, start_date: date, end_date: date, indicator_codes: list[str]):
        by_code: dict[str, dict[date, float]] = {code: {} for code in indicator_codes}
        for row in self.rows:
            if row.indicator_code not in by_code:
                continue
            if start_date <= row.indicator_date <= end_date:
                by_code[row.indicator_code][row.indicator_date] = row.value_numeric
        return by_code


class _LiveAdapter(ExternalIndicatorsAdapter):
    provider_name = "live_provider"
    indicator_codes = ("crude_brent_usd",)

    def fetch_live_range(self, *, indicator_code: str, start_date: date, end_date: date):
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        return [
            ExternalIndicatorPoint(
                indicator_date=start_date + timedelta(days=offset),
                value_numeric=80 + offset,
                unit="usd_per_bbl",
            )
            for offset in range((end_date - start_date).days + 1)
        ]

    def fetch_manual_snapshot_range(self, *, indicator_code: str, start_date: date, end_date: date):
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        return []


class _FailingLiveAdapter(ExternalIndicatorsAdapter):
    provider_name = "fail_provider"
    indicator_codes = ("usd_rub",)

    def fetch_live_range(self, *, indicator_code: str, start_date: date, end_date: date):
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        raise RuntimeError("network down")

    def fetch_manual_snapshot_range(self, *, indicator_code: str, start_date: date, end_date: date):
        _ = self.validate_indicator_code(indicator_code, self.indicator_codes)
        return [
            ExternalIndicatorPoint(
                indicator_date=start_date + timedelta(days=offset),
                value_numeric=90.0,
                unit="rub_per_usd",
            )
            for offset in range((end_date - start_date).days + 1)
        ]


def _build_service(
    *,
    tmp_path: Path,
    adapters: list[ExternalIndicatorsAdapter],
    repo: _InMemoryRepo,
) -> ExternalIndicatorsService:
    class _NoopSession:
        def commit(self) -> None:
            return None

    settings = _DummySettings(external_cache_dir=str(tmp_path / "external"))
    cache = ExternalIndicatorsCacheManager(settings.external_cache_dir)
    registry = ExternalIndicatorsRegistry(adapters=adapters)
    return ExternalIndicatorsService(
        session=_NoopSession(),  # type: ignore[arg-type]
        settings=settings,  # type: ignore[arg-type]
        repository=repo,  # type: ignore[arg-type]
        registry=registry,
        cache_manager=cache,
    )


def test_service_prefers_live_and_writes_full_coverage(tmp_path: Path) -> None:
    repo = _InMemoryRepo()
    service = _build_service(tmp_path=tmp_path, adapters=[_LiveAdapter()], repo=repo)
    start = date(2025, 1, 1)
    end = date(2025, 1, 5)

    result = service.ingest_range(
        start_date=start,
        end_date=end,
        indicator_codes=["crude_brent_usd"],
        prefer_live=True,
        run_date=end,
    )

    assert result.written_points == 5
    assert result.coverage_ratio == 1.0
    assert result.fallback_ratio == 0.0
    assert result.provider_mode_counts["live"] == 5
    assert repo.rows[0].provider_mode == "live"


def test_service_uses_cache_when_live_fails(tmp_path: Path) -> None:
    repo = _InMemoryRepo()
    adapter = _FailingLiveAdapter()
    service = _build_service(tmp_path=tmp_path, adapters=[adapter], repo=repo)
    start = date(2025, 2, 1)
    end = date(2025, 2, 3)
    fetched_at = datetime.now(UTC)
    service._cache.write_cache(
        provider_name=adapter.provider_name,
        indicator_code="usd_rub",
        points=[
            ExternalIndicatorPoint(indicator_date=start + timedelta(days=offset), value_numeric=92.0, unit="rub_per_usd")
            for offset in range((end - start).days + 1)
        ],
        fetched_at=fetched_at,
    )

    result = service.ingest_range(
        start_date=start,
        end_date=end,
        indicator_codes=["usd_rub"],
        prefer_live=True,
        run_date=end,
    )

    assert result.provider_mode_counts["cached"] == 3
    assert result.fallback_ratio == 1.0
    assert repo.rows[0].provider_mode == "cached"


def test_service_uses_last_good_when_cache_expired(tmp_path: Path) -> None:
    repo = _InMemoryRepo()
    adapter = _FailingLiveAdapter()
    service = _build_service(tmp_path=tmp_path, adapters=[adapter], repo=repo)
    start = date(2025, 3, 1)
    end = date(2025, 3, 3)
    service._cache.write_cache(
        provider_name=adapter.provider_name,
        indicator_code="usd_rub",
        points=[
            ExternalIndicatorPoint(indicator_date=start + timedelta(days=offset), value_numeric=93.0, unit="rub_per_usd")
            for offset in range((end - start).days + 1)
        ],
        fetched_at=datetime.now(UTC) - timedelta(days=3),
    )
    service._cache.write_last_good(
        provider_name=adapter.provider_name,
        indicator_code="usd_rub",
        points=[
            ExternalIndicatorPoint(indicator_date=start + timedelta(days=offset), value_numeric=91.0, unit="rub_per_usd")
            for offset in range((end - start).days + 1)
        ],
        fetched_at=datetime.now(UTC) - timedelta(days=2),
    )

    result = service.ingest_range(
        start_date=start,
        end_date=end,
        indicator_codes=["usd_rub"],
        prefer_live=True,
        run_date=end,
    )

    assert result.provider_mode_counts["manual_snapshot"] == 3
    assert repo.rows[0].provider_mode == "manual_snapshot"
