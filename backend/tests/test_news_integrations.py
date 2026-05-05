from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.integrations.news.adapters import GdeltFuelNewsAdapter
from app.integrations.news.cache import NewsCacheManager
from app.integrations.news.types import NormalizedNewsItem


def test_news_cache_roundtrip_and_ttl(tmp_path: Path) -> None:
    cache = NewsCacheManager(tmp_path)
    item = NormalizedNewsItem(
        provider_name="GDELT",
        provider_mode="live",
        published_at=datetime(2026, 4, 20, 8, 30, tzinfo=UTC),
        title="Логистические ограничения",
        url="https://example.local/news/1",
        snippet="Риск по поставкам",
        full_text="Риск по поставкам",
        language="ru",
        topic_tags=["logistics"],
        confidence=0.72,
    )
    fetched_at = datetime(2026, 4, 20, 9, 0, tzinfo=UTC)

    cache.write_cache(provider_name="GDELT", items=[item], fetched_at=fetched_at)
    cached = cache.read_cache(provider_name="GDELT", lookback_days=30, ttl_seconds=10**9)

    assert cached is not None
    cached_items, cached_fetched_at = cached
    assert len(cached_items) == 1
    assert cached_items[0].title == "Логистические ограничения"
    assert cached_fetched_at == fetched_at


def test_manual_snapshot_adapter_returns_normalized_items() -> None:
    adapter = GdeltFuelNewsAdapter()

    items = adapter.fetch_manual_snapshot(lookback_days=30)

    assert items
    assert all(item.provider_name == "GDELT" for item in items)
    assert all(item.provider_mode == "manual_snapshot" for item in items)
    assert all(item.title and item.url for item in items)


def test_manual_snapshot_adapter_rebases_stale_fixture_dates() -> None:
    adapter = GdeltFuelNewsAdapter()

    items = adapter.fetch_manual_snapshot(lookback_days=1)

    assert items
    assert all(item.published_at >= datetime.now(UTC) - timedelta(days=1, minutes=1) for item in items)
