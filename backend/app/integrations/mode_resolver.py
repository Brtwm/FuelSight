from __future__ import annotations

from dataclasses import dataclass

from app.schemas.common import DataProviderMode


@dataclass(frozen=True)
class IntegrationModeResolution:
    mode: DataProviderMode
    reason: str


def resolve_integration_mode(
    *,
    prefer_live: bool,
    live_available: bool,
    cache_available: bool,
) -> IntegrationModeResolution:
    if prefer_live and live_available:
        return IntegrationModeResolution(mode="live", reason="live_provider_available")
    if cache_available:
        return IntegrationModeResolution(mode="cached", reason="cache_snapshot_available")
    return IntegrationModeResolution(mode="manual_snapshot", reason="fallback_manual_snapshot")

