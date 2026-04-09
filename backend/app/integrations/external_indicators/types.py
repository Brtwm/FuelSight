from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from app.schemas.common import DataProviderMode, DegradationStatus, FreshnessStatus, QualityStatus


@dataclass(frozen=True)
class ExternalIndicatorPoint:
    indicator_date: date
    value_numeric: float
    unit: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExternalIndicatorFetchResult:
    indicator_code: str
    provider_name: str
    provider_mode: DataProviderMode
    freshness_status: FreshnessStatus
    degradation_status: DegradationStatus
    quality_status: QualityStatus
    points: list[ExternalIndicatorPoint] = field(default_factory=list)
    cache_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))

