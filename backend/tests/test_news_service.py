from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4
from xml.etree import ElementTree

from app.integrations.news.base import NewsIngestAdapter
from app.integrations.news.types import NormalizedNewsItem
from app.models.news_raw import NewsRaw
from app.services.news_service import NewsService


def test_digest_text_and_bullets_for_empty_rows() -> None:
    assert NewsService._build_summary_text([]) == "В выбранном периоде новости не найдены."
    assert NewsService._build_bullet_points([]) == ["Новостных сигналов за период не обнаружено."]


def test_digest_text_uses_normalized_topic_tags() -> None:
    rows = [
        NewsRaw(
            id=uuid4(),
            external_ref="news-1",
            source_name="GDELT",
            provider_name="GDELT",
            provider_mode="cached",
            published_at=datetime(2026, 4, 20, 8, 0, tzinfo=UTC),
            title="Логистика и дизель",
            url="https://example.local/1",
            snippet="Логистика давит на дизель",
            full_text="Логистика давит на дизель",
            language="ru",
            topic_tags=["logistics", "diesel"],
            impact_hint="purchase_up",
            confidence=0.7,
            cached_at=datetime(2026, 4, 20, 9, 0, tzinfo=UTC),
            metadata_json={},
        ),
        NewsRaw(
            id=uuid4(),
            external_ref="news-2",
            source_name="RBC",
            provider_name="RBC",
            provider_mode="live",
            published_at=datetime(2026, 4, 20, 10, 0, tzinfo=UTC),
            title="Спрос на бензин",
            url="https://example.local/2",
            snippet="Спрос на бензин растет",
            full_text="Спрос на бензин растет",
            language="ru",
            topic_tags=["gasoline", "demand"],
            impact_hint="demand_up",
            confidence=0.8,
            cached_at=None,
            metadata_json={},
        ),
    ]

    summary = NewsService._build_summary_text(rows)
    bullets = NewsService._build_bullet_points(rows)

    assert "давление на закупочные цены" in summary
    assert "рост спроса на бензин" in summary
    assert bullets == ["Логистика давит на дизель", "Спрос на бензин растет"]


def test_context_story_contains_external_and_event_context() -> None:
    service = NewsService(
        session=None, settings=SimpleNamespace(news_index_dir=".", enable_llm=False)
    )  # type: ignore[arg-type]
    context_story = service._build_context_story(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 7),
    )

    assert "external_context" in context_story
    assert "event_context" in context_story
    assert "indicator_refs" in context_story
    assert "event_refs" in context_story


def test_refresh_provider_falls_back_when_live_rss_is_malformed(tmp_path) -> None:
    class MalformedRssAdapter(NewsIngestAdapter):
        provider_name = "BrokenRSS"

        def fetch_live(self, *, lookback_days: int) -> list[NormalizedNewsItem]:
            raise ElementTree.ParseError("not well-formed")

        def fetch_manual_snapshot(self, *, lookback_days: int) -> list[NormalizedNewsItem]:
            return [
                NormalizedNewsItem(
                    provider_name=self.provider_name,
                    provider_mode="manual_snapshot",
                    published_at=datetime.now(UTC),
                    title="Fallback news item",
                    url="https://example.local/fallback",
                    snippet="Manual snapshot fallback",
                    full_text="Manual snapshot fallback",
                    language="ru",
                    topic_tags=["market"],
                    confidence=0.6,
                )
            ]

    service = NewsService(
        session=None,
        settings=SimpleNamespace(news_index_dir=str(tmp_path), enable_llm=False),
    )  # type: ignore[arg-type]

    diagnostics, items = service._refresh_provider(
        adapter=MalformedRssAdapter(),
        provider_mode="auto",
        lookback_days=14,
    )

    assert diagnostics.provider_mode == "manual_snapshot"
    assert diagnostics.error_message == "not well-formed"
    assert len(items) == 1
    assert items[0].provider_mode == "manual_snapshot"
