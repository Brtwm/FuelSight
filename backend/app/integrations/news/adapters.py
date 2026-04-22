from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Final
from urllib.parse import quote
from urllib.request import urlopen
from xml.etree import ElementTree

from app.integrations.news.base import NewsIngestAdapter
from app.integrations.news.types import NormalizedNewsItem

FUEL_KEYWORDS: Final[tuple[str, ...]] = (
    "топлив",
    "нефт",
    "бензин",
    "дизел",
    "аи-92",
    "аи-95",
    "газойл",
    "азс",
    "маржа",
    "оптов",
    "нпз",
    "логист",
    "брент",
    "fuel",
    "diesel",
    "gasoline",
    "oil",
    "refinery",
)


@dataclass(frozen=True)
class ManualSnapshotSeed:
    title: str
    url: str
    published_at: str
    snippet: str
    full_text: str
    topic_tags: tuple[str, ...]
    confidence: float
    external_ref: str


class BaseRssNewsAdapter(NewsIngestAdapter):
    feed_url: str
    language: str = "ru"
    live_confidence: float = 0.78
    snapshot_confidence: float = 0.62
    snapshot_items: tuple[ManualSnapshotSeed, ...] = ()

    def fetch_live(self, *, lookback_days: int) -> list[NormalizedNewsItem]:
        with urlopen(self.feed_url, timeout=10) as response:  # noqa: S310
            body = response.read()
        root = ElementTree.fromstring(body)
        items = self._parse_rss_items(root=root, lookback_days=lookback_days)
        return items

    def fetch_manual_snapshot(self, *, lookback_days: int) -> list[NormalizedNewsItem]:
        threshold = datetime.now(UTC) - timedelta(days=max(lookback_days, 1))
        items: list[NormalizedNewsItem] = []
        for seed in self.snapshot_items:
            published_at = datetime.fromisoformat(seed.published_at)
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)
            else:
                published_at = published_at.astimezone(UTC)
            if published_at < threshold:
                continue
            items.append(
                NormalizedNewsItem(
                    provider_name=self.provider_name,
                    provider_mode="manual_snapshot",
                    published_at=published_at,
                    title=seed.title,
                    url=seed.url,
                    snippet=seed.snippet,
                    full_text=seed.full_text,
                    language=self.language,
                    topic_tags=list(seed.topic_tags),
                    confidence=seed.confidence,
                    cached_at=published_at,
                    external_ref=seed.external_ref,
                    metadata={"source_type": "manual_snapshot"},
                )
            )
        return items

    def _parse_rss_items(
        self,
        *,
        root: ElementTree.Element,
        lookback_days: int,
    ) -> list[NormalizedNewsItem]:
        threshold = datetime.now(UTC) - timedelta(days=max(lookback_days, 1))
        results: list[NormalizedNewsItem] = []
        for node in root.findall(".//item"):
            title = _node_text(node, "title")
            link = _node_text(node, "link")
            description = _node_text(node, "description")
            pub_date = _parse_pub_date(_node_text(node, "pubDate"))
            if not title or not link or pub_date is None:
                continue
            if pub_date < threshold:
                continue
            haystack = " ".join(part for part in (title, description) if part).lower()
            if not any(keyword in haystack for keyword in FUEL_KEYWORDS):
                continue
            topic_tags = _infer_topic_tags(title=title, snippet=description)
            external_ref = _node_text(node, "guid") or f"{self.provider_name}:{link}"
            results.append(
                NormalizedNewsItem(
                    provider_name=self.provider_name,
                    provider_mode="live",
                    published_at=pub_date,
                    title=title,
                    url=link,
                    snippet=description,
                    full_text=description,
                    language=self.language,
                    topic_tags=topic_tags,
                    confidence=self.live_confidence,
                    external_ref=external_ref,
                    metadata={"source_type": "rss"},
                )
            )
        results.sort(key=lambda item: item.published_at, reverse=True)
        deduped: list[NormalizedNewsItem] = []
        seen_urls: set[str] = set()
        for item in results:
            if item.url in seen_urls:
                continue
            deduped.append(item)
            seen_urls.add(item.url)
        return deduped[:50]


class GdeltFuelNewsAdapter(BaseRssNewsAdapter):
    provider_name = "GDELT"
    feed_url = (
        "https://api.gdeltproject.org/api/v2/doc/doc?"
        f"query={quote('(топливо OR бензин OR дизель OR нефтепродукты OR refinery OR fuel)')}"
        "&mode=ArtList&format=rss&maxrecords=50&sort=datedesc"
    )
    snapshot_items = (
        ManualSnapshotSeed(
            title="Логистические ограничения на южных маршрутах усиливают риск по ДТ",
            url="https://example.local/manual/gdelt-logistics-risk",
            published_at="2026-04-20T08:30:00+00:00",
            snippet="Логистическая нагрузка повышает риск роста закупочных цен на дизель.",
            full_text="Логистическая нагрузка на маршруты поставок усиливает риск роста закупочной цены по дизелю.",
            topic_tags=("logistics", "diesel", "supply"),
            confidence=0.64,
            external_ref="gdelt_manual_2026_04_20_01",
        ),
        ManualSnapshotSeed(
            title="Оптовые индикативы по бензину остаются повышенными вторую неделю подряд",
            url="https://example.local/manual/gdelt-wholesale-benzin",
            published_at="2026-04-19T09:10:00+00:00",
            snippet="Умеренный рост оптовых индикативов продолжает давить на маржу бензина.",
            full_text="Рост оптовых индикативов по бензину сохраняется, что давит на валовую маржу розничных продаж.",
            topic_tags=("gasoline", "wholesale", "margin"),
            confidence=0.65,
            external_ref="gdelt_manual_2026_04_19_02",
        ),
    )


class RbcEconomyNewsAdapter(BaseRssNewsAdapter):
    provider_name = "RBC"
    feed_url = "https://rssexport.rbc.ru/rbcnews/news/30/full.rss"
    snapshot_items = (
        ManualSnapshotSeed(
            title="Нефтяные котировки и курс рубля остаются ключевыми факторами закупочной цены",
            url="https://example.local/manual/rbc-fx-oil",
            published_at="2026-04-18T10:15:00+00:00",
            snippet="Внешние макрофакторы усиливают волатильность цен закупки для нефтепродуктов.",
            full_text="Изменение курса рубля и нефтяных котировок остается значимым фоном для закупочной цены нефтепродуктов.",
            topic_tags=("fx", "oil", "purchase_price"),
            confidence=0.63,
            external_ref="rbc_manual_2026_04_18_01",
        ),
    )


class KommersantEconomyNewsAdapter(BaseRssNewsAdapter):
    provider_name = "Kommersant"
    feed_url = "https://www.kommersant.ru/RSS/news.xml"
    snapshot_items = (
        ManualSnapshotSeed(
            title="Плановые ремонты НПЗ поддерживают риск по предложению топлива",
            url="https://example.local/manual/kommersant-refinery",
            published_at="2026-04-17T07:55:00+00:00",
            snippet="Ремонтная кампания на НПЗ может ограничить предложение топлива в отдельных неделях.",
            full_text="Плановые ремонты на НПЗ усиливают риск локального сокращения предложения и роста закупочной нагрузки.",
            topic_tags=("refinery", "supply", "diesel"),
            confidence=0.61,
            external_ref="kommersant_manual_2026_04_17_01",
        ),
    )


class PrimeEnergyNewsAdapter(BaseRssNewsAdapter):
    provider_name = "Prime"
    feed_url = "https://1prime.ru/export/rss2/index.xml"
    snapshot_items = (
        ManualSnapshotSeed(
            title="Рынок топлива оценивает рост сезонного спроса перед длинными выходными",
            url="https://example.local/manual/prime-seasonal-demand",
            published_at="2026-04-16T06:45:00+00:00",
            snippet="Рост мобильности поддерживает спрос на бензин и смягчает часть маржинального давления.",
            full_text="Сезонный рост мобильности поддерживает спрос на бензин и частично компенсирует давление на маржу.",
            topic_tags=("demand", "gasoline", "seasonality"),
            confidence=0.6,
            external_ref="prime_manual_2026_04_16_01",
        ),
    )


def _node_text(node: ElementTree.Element, tag_name: str) -> str | None:
    target = node.find(tag_name)
    if target is None or target.text is None:
        return None
    value = target.text.strip()
    return value or None


def _parse_pub_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _infer_topic_tags(*, title: str, snippet: str | None) -> list[str]:
    haystack = f"{title} {snippet or ''}".lower()
    inferred: list[str] = []
    if any(token in haystack for token in ("дизел", "diesel")):
        inferred.append("diesel")
    if any(token in haystack for token in ("бензин", "gasoline", "аи-92", "аи-95")):
        inferred.append("gasoline")
    if any(token in haystack for token in ("логист", "supply")):
        inferred.append("logistics")
    if any(token in haystack for token in ("оптов", "маржа", "wholesale")):
        inferred.append("wholesale")
    if any(token in haystack for token in ("рубл", "валют", "fx")):
        inferred.append("fx")
    if any(token in haystack for token in ("нефт", "брент", "oil")):
        inferred.append("oil")
    if not inferred:
        inferred.append("market")
    return inferred
