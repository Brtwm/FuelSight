from __future__ import annotations

from collections.abc import Callable
from collections.abc import Sequence
from datetime import date

from app.integrations.external_indicators.adapters import (
    BrentEiaAdapter,
    CuratedWholesaleAdapter,
    EventPressureAdapter,
    HolidayFlagAdapter,
    UsdRubCbrAdapter,
)
from app.integrations.external_indicators.base import ExternalIndicatorsAdapter


class ExternalIndicatorsRegistry:
    def __init__(
        self,
        adapters: Sequence[ExternalIndicatorsAdapter] | None = None,
        *,
        event_pressure_provider: Callable[[date], float] | None = None,
    ) -> None:
        resolved_adapters = (
            list(adapters)
            if adapters is not None
            else _default_adapters(event_pressure_provider=event_pressure_provider)
        )
        self._by_indicator: dict[str, ExternalIndicatorsAdapter] = {}
        for adapter in resolved_adapters:
            for indicator_code in adapter.indicator_codes:
                self._by_indicator[indicator_code] = adapter

    def resolve(self, indicator_code: str) -> ExternalIndicatorsAdapter:
        normalized = indicator_code.strip().lower()
        if normalized not in self._by_indicator:
            raise KeyError(f"external indicator adapter is not registered for indicator_code={indicator_code}")
        return self._by_indicator[normalized]

    def supported_indicator_codes(self) -> list[str]:
        return sorted(self._by_indicator.keys())


def _default_adapters(
    *,
    event_pressure_provider: Callable[[date], float] | None = None,
) -> list[ExternalIndicatorsAdapter]:
    return [
        BrentEiaAdapter(),
        UsdRubCbrAdapter(),
        CuratedWholesaleAdapter(),
        HolidayFlagAdapter(),
        EventPressureAdapter(event_pressure_provider=event_pressure_provider),
    ]
