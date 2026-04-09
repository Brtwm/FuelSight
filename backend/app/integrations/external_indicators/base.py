from __future__ import annotations

from abc import ABC
from collections.abc import Sequence
from datetime import date

from app.integrations.external_indicators.types import ExternalIndicatorPoint


class ExternalIndicatorsAdapter(ABC):
    provider_name: str
    indicator_codes: tuple[str, ...]
    ttl_seconds: int = 24 * 60 * 60

    def supports(self, indicator_code: str) -> bool:
        return indicator_code in self.indicator_codes

    @property
    def supports_live(self) -> bool:
        return True

    def fetch_live_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        raise NotImplementedError

    def fetch_manual_snapshot_range(
        self,
        *,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        return []

    @staticmethod
    def validate_indicator_code(indicator_code: str, allowed_codes: Sequence[str]) -> str:
        normalized = indicator_code.strip().lower()
        if normalized not in allowed_codes:
            raise ValueError(f"Unsupported indicator_code={indicator_code}")
        return normalized
