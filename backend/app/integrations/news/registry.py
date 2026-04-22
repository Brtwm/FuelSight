from __future__ import annotations

from collections.abc import Sequence

from app.integrations.news.adapters import (
    GdeltFuelNewsAdapter,
    KommersantEconomyNewsAdapter,
    PrimeEnergyNewsAdapter,
    RbcEconomyNewsAdapter,
)
from app.integrations.news.base import NewsIngestAdapter


class NewsProvidersRegistry:
    def __init__(self, adapters: Sequence[NewsIngestAdapter] | None = None) -> None:
        self._adapters = list(adapters) if adapters is not None else _default_adapters()

    def all(self) -> list[NewsIngestAdapter]:
        return list(self._adapters)


def _default_adapters() -> list[NewsIngestAdapter]:
    return [
        GdeltFuelNewsAdapter(),
        RbcEconomyNewsAdapter(),
        KommersantEconomyNewsAdapter(),
        PrimeEnergyNewsAdapter(),
    ]
