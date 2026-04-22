from __future__ import annotations

from abc import ABC

from app.integrations.news.types import NormalizedNewsItem


class NewsIngestAdapter(ABC):
    provider_name: str
    ttl_seconds: int = 6 * 60 * 60

    @property
    def supports_live(self) -> bool:
        return True

    def fetch_live(self, *, lookback_days: int) -> list[NormalizedNewsItem]:
        raise NotImplementedError

    def fetch_manual_snapshot(self, *, lookback_days: int) -> list[NormalizedNewsItem]:
        return []
