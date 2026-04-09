from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.external_indicators import (
    ExternalIndicatorFetchResult,
    ExternalIndicatorPoint,
    ExternalIndicatorsCacheManager,
    ExternalIndicatorsRegistry,
)
from app.repositories import ExternalIndicatorUpsertRow, ExternalIndicatorsRepository
from app.schemas.common import DataProviderMode

DEFAULT_EXTERNAL_INDICATORS = [
    "crude_brent_usd",
    "usd_rub",
    "wholesale_gasoline_index",
    "wholesale_diesel_index",
    "holiday_flag",
    "event_pressure_score",
]


@dataclass(frozen=True)
class IndicatorIngestSummary:
    indicator_code: str
    provider_name: str
    provider_mode: DataProviderMode
    expected_points: int
    written_points: int
    coverage_ratio: float
    cache_key: str | None
    freshness_status: str
    degradation_status: str
    quality_status: str
    latest_date: date | None = None
    latest_mode: str | None = None


@dataclass(frozen=True)
class ExternalIndicatorsIngestResult:
    run_id: str
    run_date: date
    start_date: date
    end_date: date
    expected_points: int
    written_points: int
    coverage_ratio: float
    fallback_ratio: float
    provider_mode_counts: dict[str, int] = field(default_factory=dict)
    indicator_coverage: list[IndicatorIngestSummary] = field(default_factory=list)
    cache_dir: str = ""

    def to_manifest(self, *, manifest_path: str) -> dict[str, Any]:
        window = {"start_date": self.start_date.isoformat(), "end_date": self.end_date.isoformat()}
        return {
            "run_id": self.run_id,
            "run_date": self.run_date.isoformat(),
            "window": window,
            "status": "ok" if self.written_points > 0 else "degraded",
            "expected_points": self.expected_points,
            "written_points": self.written_points,
            "coverage_ratio": round(self.coverage_ratio, 6),
            "provider_mode_counts": self.provider_mode_counts,
            "fallback_ratio": round(self.fallback_ratio, 6),
            "indicator_coverage": [
                {
                    "indicator_code": item.indicator_code,
                    "provider_name": item.provider_name,
                    "provider_mode": item.provider_mode,
                    "expected_points": item.expected_points,
                    "written_points": item.written_points,
                    "coverage_ratio": round(item.coverage_ratio, 6),
                    "latest_date": item.latest_date.isoformat() if item.latest_date else None,
                    "latest_mode": item.latest_mode,
                    "freshness_status": item.freshness_status,
                    "degradation_status": item.degradation_status,
                    "quality_status": item.quality_status,
                    "cache_key": item.cache_key,
                }
                for item in self.indicator_coverage
            ],
            "artifacts": {"manifest_path": manifest_path, "cache_dir": self.cache_dir},
        }


class ExternalIndicatorsService:
    def __init__(
        self,
        session: Session,
        *,
        settings: Settings | None = None,
        repository: ExternalIndicatorsRepository | None = None,
        registry: ExternalIndicatorsRegistry | None = None,
        cache_manager: ExternalIndicatorsCacheManager | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._repository = repository or ExternalIndicatorsRepository(session)
        self._registry = registry or ExternalIndicatorsRegistry()
        self._cache = cache_manager or ExternalIndicatorsCacheManager(self._settings.external_cache_dir)

    def ingest_range(
        self,
        *,
        start_date: date,
        end_date: date,
        indicator_codes: list[str] | None = None,
        prefer_live: bool | None = None,
        run_date: date | None = None,
        commit: bool = True,
    ) -> ExternalIndicatorsIngestResult:
        normalized_codes = self._normalize_indicator_codes(indicator_codes)
        if end_date < start_date:
            raise ValueError("end_date must be greater than or equal to start_date")

        should_prefer_live = self._resolve_live_preference(prefer_live=prefer_live)
        expected_days = (end_date - start_date).days + 1
        report_items: list[ExternalIndicatorFetchResult] = []
        upsert_rows: list[ExternalIndicatorUpsertRow] = []

        for indicator_code in normalized_codes:
            adapter = self._registry.resolve(indicator_code)
            fetched = self._fetch_with_fallback(
                indicator_code=indicator_code,
                start_date=start_date,
                end_date=end_date,
                prefer_live=should_prefer_live,
                adapter=adapter,
            )
            report_items.append(fetched)
            for point in fetched.points:
                metadata = dict(point.metadata)
                metadata.update(
                    {
                        "freshness_status": fetched.freshness_status,
                        "degradation_status": fetched.degradation_status,
                        "quality_status": fetched.quality_status,
                        "provider_mode": fetched.provider_mode,
                    }
                )
                upsert_rows.append(
                    ExternalIndicatorUpsertRow(
                        indicator_date=point.indicator_date,
                        indicator_code=indicator_code,
                        value_numeric=point.value_numeric,
                        unit=point.unit,
                        provider_name=fetched.provider_name,
                        provider_mode=fetched.provider_mode,
                        cache_key=fetched.cache_key,
                        metadata_json=metadata,
                    )
                )

        written_points = self._repository.upsert_many(upsert_rows)
        if commit:
            self._session.commit()

        coverage_summary = self._repository.get_coverage_summary(
            start_date=start_date,
            end_date=end_date,
            indicator_codes=normalized_codes,
        )
        coverage_by_code = {item["indicator_code"]: item for item in coverage_summary}

        mode_counter: Counter[str] = Counter()
        fallback_points = 0
        indicator_rows: list[IndicatorIngestSummary] = []
        for item in report_items:
            points_count = len(item.points)
            mode_counter[item.provider_mode] += points_count
            if item.provider_mode != "live":
                fallback_points += points_count
            coverage = coverage_by_code.get(item.indicator_code, {})
            indicator_rows.append(
                IndicatorIngestSummary(
                    indicator_code=item.indicator_code,
                    provider_name=item.provider_name,
                    provider_mode=item.provider_mode,
                    expected_points=expected_days,
                    written_points=points_count,
                    coverage_ratio=float(coverage.get("coverage_ratio", 0.0)),
                    cache_key=item.cache_key,
                    freshness_status=item.freshness_status,
                    degradation_status=item.degradation_status,
                    quality_status=item.quality_status,
                    latest_date=coverage.get("latest_date"),
                    latest_mode=coverage.get("latest_mode"),
                )
            )

        expected_points = expected_days * len(normalized_codes)
        coverage_ratio = (written_points / expected_points) if expected_points > 0 else 0.0
        fallback_ratio = (fallback_points / written_points) if written_points > 0 else 1.0
        return ExternalIndicatorsIngestResult(
            run_id=str(uuid4()),
            run_date=run_date or datetime.now(UTC).date(),
            start_date=start_date,
            end_date=end_date,
            expected_points=expected_points,
            written_points=written_points,
            coverage_ratio=coverage_ratio,
            fallback_ratio=fallback_ratio,
            provider_mode_counts=dict(mode_counter),
            indicator_coverage=indicator_rows,
            cache_dir=str(Path(self._cache.root_dir)),
        )

    def get_context_for_range(
        self,
        *,
        start_date: date,
        end_date: date,
        indicator_codes: list[str] | None = None,
        prefer_live: bool | None = None,
        commit: bool = True,
    ) -> dict[str, dict[date, float]]:
        normalized_codes = self._normalize_indicator_codes(indicator_codes)
        self.ingest_range(
            start_date=start_date,
            end_date=end_date,
            indicator_codes=normalized_codes,
            prefer_live=prefer_live,
            run_date=end_date,
            commit=commit,
        )
        return self._repository.get_series(
            start_date=start_date,
            end_date=end_date,
            indicator_codes=normalized_codes,
        )

    def _fetch_with_fallback(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
        prefer_live: bool,
        adapter,
    ) -> ExternalIndicatorFetchResult:
        fetched_at = datetime.now(UTC)
        live_error: str | None = None
        cache_key = self._cache.cache_key(
            provider_name=adapter.provider_name,
            indicator_code=indicator_code,
        )

        if prefer_live and adapter.supports_live:
            try:
                points = adapter.fetch_live_range(
                    indicator_code=indicator_code,
                    start_date=start_date,
                    end_date=end_date,
                )
                if points:
                    self._cache.write_cache(
                        provider_name=adapter.provider_name,
                        indicator_code=indicator_code,
                        points=points,
                        fetched_at=fetched_at,
                    )
                    self._cache.write_last_good(
                        provider_name=adapter.provider_name,
                        indicator_code=indicator_code,
                        points=points,
                        fetched_at=fetched_at,
                    )
                    return ExternalIndicatorFetchResult(
                        indicator_code=indicator_code,
                        provider_name=adapter.provider_name,
                        provider_mode="live",
                        freshness_status="fresh",
                        degradation_status="ok",
                        quality_status="ok",
                        points=points,
                        cache_key=cache_key,
                        metadata={"source": "live"},
                    )
            except Exception as exc:
                live_error = str(exc)

        cached_points = self._cache.read_cache(
            provider_name=adapter.provider_name,
            indicator_code=indicator_code,
            start_date=start_date,
            end_date=end_date,
            ttl_seconds=adapter.ttl_seconds,
        )
        if cached_points:
            return ExternalIndicatorFetchResult(
                indicator_code=indicator_code,
                provider_name=adapter.provider_name,
                provider_mode="cached",
                freshness_status="warning",
                degradation_status="warning",
                quality_status="warning",
                points=cached_points,
                cache_key=cache_key,
                metadata={"source": "cache", "live_error": live_error},
            )

        last_good_points = self._cache.read_last_good(
            provider_name=adapter.provider_name,
            indicator_code=indicator_code,
            start_date=start_date,
            end_date=end_date,
        )
        if last_good_points:
            return ExternalIndicatorFetchResult(
                indicator_code=indicator_code,
                provider_name=adapter.provider_name,
                provider_mode="manual_snapshot",
                freshness_status="warning",
                degradation_status="degraded",
                quality_status="warning",
                points=last_good_points,
                cache_key=cache_key,
                metadata={"source": "last_good", "live_error": live_error},
            )

        manual_points = adapter.fetch_manual_snapshot_range(
            indicator_code=indicator_code,
            start_date=start_date,
            end_date=end_date,
        )
        if manual_points:
            self._cache.write_last_good(
                provider_name=adapter.provider_name,
                indicator_code=indicator_code,
                points=manual_points,
                fetched_at=fetched_at,
            )
            return ExternalIndicatorFetchResult(
                indicator_code=indicator_code,
                provider_name=adapter.provider_name,
                provider_mode="manual_snapshot",
                freshness_status="warning",
                degradation_status="degraded",
                quality_status="warning",
                points=manual_points,
                cache_key=cache_key,
                metadata={"source": "manual_snapshot", "live_error": live_error},
            )

        synthetic_points = self._build_zero_points(start_date=start_date, end_date=end_date)
        return ExternalIndicatorFetchResult(
            indicator_code=indicator_code,
            provider_name=adapter.provider_name,
            provider_mode="manual_snapshot",
            freshness_status="degraded",
            degradation_status="failed",
            quality_status="failed",
            points=synthetic_points,
            cache_key=cache_key,
            metadata={"source": "synthetic_zero", "live_error": live_error},
        )

    def _resolve_live_preference(self, *, prefer_live: bool | None) -> bool:
        if prefer_live is not None:
            return prefer_live
        configured_mode = self._settings.external_indicators_mode.strip().lower()
        if configured_mode == "live" and self._settings.enable_external_indicators:
            return True
        return False

    @staticmethod
    def _build_zero_points(*, start_date: date, end_date: date) -> list[ExternalIndicatorPoint]:
        points: list[ExternalIndicatorPoint] = []
        for offset in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=offset)
            points.append(
                ExternalIndicatorPoint(
                    indicator_date=current_date,
                    value_numeric=0.0,
                    unit="unknown",
                    metadata={"synthetic": True},
                )
            )
        return points

    @staticmethod
    def _normalize_indicator_codes(indicator_codes: list[str] | None) -> list[str]:
        source = indicator_codes or DEFAULT_EXTERNAL_INDICATORS
        normalized: list[str] = []
        for item in source:
            value = item.strip().lower()
            if value and value not in normalized:
                normalized.append(value)
        return normalized
