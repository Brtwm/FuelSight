from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.schemas.common import DataProviderMode, DegradationStatus, FreshnessStatus, QualityStatus


@dataclass(frozen=True)
class IntegrationResult:
    provider_name: str
    provider_mode: DataProviderMode
    freshness_status: FreshnessStatus
    degradation_status: DegradationStatus
    quality_status: QualityStatus
    cache_key: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
