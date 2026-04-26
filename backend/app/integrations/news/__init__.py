from app.integrations.news.adapters import (
    GdeltFuelNewsAdapter,
    KommersantEconomyNewsAdapter,
    PrimeEnergyNewsAdapter,
    RbcEconomyNewsAdapter,
)
from app.integrations.news.base import NewsIngestAdapter
from app.integrations.news.cache import NewsCacheManager
from app.integrations.news.registry import NewsProvidersRegistry
from app.integrations.news.types import NewsProviderResult, NormalizedNewsItem

__all__ = [
    "GdeltFuelNewsAdapter",
    "KommersantEconomyNewsAdapter",
    "NewsCacheManager",
    "NewsIngestAdapter",
    "NewsProviderResult",
    "NewsProvidersRegistry",
    "NormalizedNewsItem",
    "PrimeEnergyNewsAdapter",
    "RbcEconomyNewsAdapter",
]
