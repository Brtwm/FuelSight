from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from uuid import UUID, uuid5

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.news import NewsCacheManager, NewsProvidersRegistry, NormalizedNewsItem
from app.integrations.news.base import NewsIngestAdapter
from app.models import NewsDigest, NewsRaw
from app.services.event_catalog_service import EventCatalogService
from app.services.external_context_service import ExternalContextService

_VALID_NEWS_MODES = {"auto", "live", "cached", "manual_snapshot"}


@dataclass(frozen=True)
class ProviderRefreshDiagnostics:
    provider_name: str
    provider_mode: str
    fetched_at: datetime
    items_count: int
    cache_key: str | None = None
    last_good_path: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class NewsRefreshResult:
    status: str
    imported_news_count: int
    created_digests: int
    provider_mode: str | None = None
    news_freshness: str | None = None
    quality_status: str = "warning"
    provider_mode_counts: dict[str, int] = field(default_factory=dict)
    written_news_count: int = 0
    coverage_ratio: float = 0.0
    cache_dir: str | None = None
    last_success_at: str | None = None
    provider_diagnostics: list[dict[str, Any]] = field(default_factory=list)


class NewsService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._event_catalog_service = EventCatalogService(session)
        self._external_context_service = ExternalContextService(self._settings)
        self._cache = NewsCacheManager(self._settings.news_index_dir)
        self._registry = NewsProvidersRegistry()

    def refresh_news(
        self,
        *,
        provider_mode: str = "auto",
        lookback_days: int = 14,
    ) -> NewsRefreshResult:
        normalized_mode = provider_mode.strip().lower()
        if normalized_mode not in _VALID_NEWS_MODES:
            raise ValueError("provider_mode must be one of auto, live, cached, manual_snapshot")
        if lookback_days <= 0:
            raise ValueError("lookback_days must be greater than 0")

        provider_items: list[NormalizedNewsItem] = []
        diagnostics: list[ProviderRefreshDiagnostics] = []
        adapters = self._registry.all()
        for adapter in adapters:
            result = self._refresh_provider(
                adapter=adapter,
                provider_mode=normalized_mode,
                lookback_days=lookback_days,
            )
            diagnostics.append(result[0])
            provider_items.extend(result[1])

        imported_news_count = self._upsert_news_rows(provider_items)
        created_digests = self._rebuild_latest_digests()
        self._session.commit()

        provider_mode_counts = Counter(item.provider_mode for item in provider_items)
        coverage_ratio = round(
            len([entry for entry in diagnostics if entry.items_count > 0]) / max(len(adapters), 1),
            6,
        )
        dominant_mode = _dominant_provider_mode(provider_mode_counts)
        latest_digest = self.get_latest_digest(period_type="daily")
        news_freshness = latest_digest.get("news_freshness") if latest_digest else None
        quality_status = _classify_quality_status(
            coverage_ratio=coverage_ratio,
            provider_mode_counts=provider_mode_counts,
        )
        status = "ok" if imported_news_count > 0 and quality_status == "ok" else quality_status
        last_success_at = max(
            (entry.fetched_at for entry in diagnostics if entry.items_count > 0),
            default=None,
        )
        return NewsRefreshResult(
            status=status,
            imported_news_count=imported_news_count,
            created_digests=created_digests,
            provider_mode=dominant_mode,
            news_freshness=news_freshness,
            quality_status=quality_status,
            provider_mode_counts=dict(provider_mode_counts),
            written_news_count=imported_news_count,
            coverage_ratio=coverage_ratio,
            cache_dir=str(self._cache.root_dir),
            last_success_at=last_success_at.astimezone(UTC).isoformat()
            if last_success_at
            else None,
            provider_diagnostics=[
                {
                    "provider_name": entry.provider_name,
                    "provider_mode": entry.provider_mode,
                    "fetched_at": entry.fetched_at.astimezone(UTC).isoformat(),
                    "items_count": entry.items_count,
                    "cache_key": entry.cache_key,
                    "last_good_path": entry.last_good_path,
                    "error_message": entry.error_message,
                }
                for entry in diagnostics
            ],
        )

    def get_latest_digest(self, *, period_type: str) -> dict[str, object] | None:
        normalized_period = period_type.strip().lower()
        if normalized_period not in {"daily", "weekly"}:
            raise ValueError("period_type must be one of daily, weekly")

        row = self._session.scalar(
            select(NewsDigest)
            .where(NewsDigest.period_type == normalized_period)
            .order_by(NewsDigest.digest_date.desc(), NewsDigest.created_at.desc())
            .limit(1)
        )
        if row is None:
            return None
        if normalized_period == "weekly":
            context_start = row.digest_date - timedelta(days=6)
        else:
            context_start = row.digest_date
        context_story = self._build_context_story(
            start_date=context_start, end_date=row.digest_date
        )
        rows = self._load_digest_source_rows(source_ids=list(row.source_ids_json))
        provider_mode = _dominant_provider_mode(Counter(item.provider_mode for item in rows))
        return {
            "digest_date": row.digest_date,
            "period_type": row.period_type,
            "summary_text": row.summary_text,
            "bullet_points": list(row.bullet_points_json),
            "source_ids": list(row.source_ids_json),
            "llm_mode": row.llm_mode,
            "provider_mode": provider_mode
            or context_story["external_context"].get("provider_mode"),
            "news_freshness": self._resolve_news_freshness(digest_date=row.digest_date),
            "context_story": context_story,
        }

    def search_news(
        self,
        *,
        q: str | None,
        date_from: date | None,
        date_to: date | None,
        topic: str | None,
        limit: int = 20,
    ) -> list[dict[str, object]]:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")

        normalized_limit = min(max(limit, 1), 100)
        statement = select(NewsRaw).order_by(NewsRaw.published_at.desc())

        if q and q.strip():
            pattern = f"%{q.strip()}%"
            statement = statement.where(
                or_(
                    NewsRaw.title.ilike(pattern),
                    NewsRaw.snippet.ilike(pattern),
                    NewsRaw.full_text.ilike(pattern),
                    NewsRaw.external_ref.ilike(pattern),
                )
            )

        if date_from is not None:
            statement = statement.where(func.date(NewsRaw.published_at) >= date_from)
        if date_to is not None:
            statement = statement.where(func.date(NewsRaw.published_at) <= date_to)

        if topic and topic.strip():
            normalized_topic = topic.strip().lower()
            statement = statement.where(
                and_(
                    NewsRaw.topic_tags.is_not(None),
                    NewsRaw.topic_tags.contains([normalized_topic]),
                )
            )

        rows = list(self._session.scalars(statement.limit(normalized_limit)))
        return [
            {
                "id": row.id,
                "ref_id": self._build_ref_id(row.id, row.external_ref),
                "source_name": row.source_name,
                "provider_name": row.provider_name,
                "published_at": row.published_at,
                "title": row.title,
                "url": row.url,
                "snippet": row.snippet,
                "topic_tags": row.topic_tags,
                "impact_hint": row.impact_hint,
                "provider_mode": row.provider_mode,
                "confidence": row.confidence,
                "cached_at": row.cached_at,
            }
            for row in rows
        ]

    def _refresh_provider(
        self,
        *,
        adapter: NewsIngestAdapter,
        provider_mode: str,
        lookback_days: int,
    ) -> tuple[ProviderRefreshDiagnostics, list[NormalizedNewsItem]]:
        error_message: str | None = None
        if provider_mode in {"auto", "live"}:
            try:
                live_items = adapter.fetch_live(lookback_days=lookback_days)
                fetched_at = datetime.now(UTC)
                live_items = [
                    _normalize_item(item=item, provider_mode="live", cached_at=None)
                    for item in live_items
                ]
                cache_key = self._cache.write_cache(
                    provider_name=adapter.provider_name,
                    items=live_items,
                    fetched_at=fetched_at,
                )
                last_good_path = self._cache.write_last_good(
                    provider_name=adapter.provider_name,
                    items=live_items,
                    fetched_at=fetched_at,
                )
                return (
                    ProviderRefreshDiagnostics(
                        provider_name=adapter.provider_name,
                        provider_mode="live",
                        fetched_at=fetched_at,
                        items_count=len(live_items),
                        cache_key=cache_key,
                        last_good_path=last_good_path,
                    ),
                    live_items,
                )
            except (HTTPError, URLError, OSError, ValueError) as exc:
                error_message = str(exc)

        if provider_mode in {"auto", "live", "cached"}:
            cached = self._cache.read_cache(
                provider_name=adapter.provider_name,
                lookback_days=lookback_days,
                ttl_seconds=adapter.ttl_seconds,
            )
            if cached is not None:
                items, fetched_at = cached
                normalized_items = [
                    _normalize_item(item=item, provider_mode="cached", cached_at=fetched_at)
                    for item in items
                ]
                return (
                    ProviderRefreshDiagnostics(
                        provider_name=adapter.provider_name,
                        provider_mode="cached",
                        fetched_at=fetched_at,
                        items_count=len(normalized_items),
                        cache_key=self._cache.cache_key(provider_name=adapter.provider_name),
                        error_message=error_message,
                    ),
                    normalized_items,
                )

        if provider_mode in {"auto", "live", "cached", "manual_snapshot"}:
            last_good = self._cache.read_last_good(
                provider_name=adapter.provider_name,
                lookback_days=lookback_days,
            )
            if last_good is not None:
                items, fetched_at = last_good
                normalized_items = [
                    _normalize_item(
                        item=item, provider_mode="manual_snapshot", cached_at=fetched_at
                    )
                    for item in items
                ]
                return (
                    ProviderRefreshDiagnostics(
                        provider_name=adapter.provider_name,
                        provider_mode="manual_snapshot",
                        fetched_at=fetched_at,
                        items_count=len(normalized_items),
                        last_good_path=str(
                            self._cache.root_dir
                            / "last_good"
                            / f"{adapter.provider_name.lower()}.json"
                        ),
                        error_message=error_message,
                    ),
                    normalized_items,
                )

            snapshot_items = adapter.fetch_manual_snapshot(lookback_days=lookback_days)
            if snapshot_items:
                fetched_at = datetime.now(UTC)
                normalized_items = [
                    _normalize_item(
                        item=item, provider_mode="manual_snapshot", cached_at=fetched_at
                    )
                    for item in snapshot_items
                ]
                last_good_path = self._cache.write_last_good(
                    provider_name=adapter.provider_name,
                    items=normalized_items,
                    fetched_at=fetched_at,
                )
                return (
                    ProviderRefreshDiagnostics(
                        provider_name=adapter.provider_name,
                        provider_mode="manual_snapshot",
                        fetched_at=fetched_at,
                        items_count=len(normalized_items),
                        last_good_path=last_good_path,
                        error_message=error_message,
                    ),
                    normalized_items,
                )

        fallback_time = datetime.now(UTC)
        return (
            ProviderRefreshDiagnostics(
                provider_name=adapter.provider_name,
                provider_mode="manual_snapshot" if provider_mode == "manual_snapshot" else "cached",
                fetched_at=fallback_time,
                items_count=0,
                error_message=error_message,
            ),
            [],
        )

    def _upsert_news_rows(self, items: list[NormalizedNewsItem]) -> int:
        if not items:
            return 0
        provider_names = sorted({item.provider_name for item in items})
        urls = sorted({item.url for item in items})
        existing_rows = list(
            self._session.scalars(
                select(NewsRaw).where(
                    NewsRaw.provider_name.in_(provider_names),
                    NewsRaw.url.in_(urls),
                )
            )
        )
        existing_by_key = {(row.provider_name, row.url): row for row in existing_rows}
        written = 0
        for item in items:
            row = existing_by_key.get((item.provider_name, item.url))
            if row is None:
                row = NewsRaw(
                    id=self._build_news_id(provider_name=item.provider_name, url=item.url),
                    external_ref=item.external_ref,
                    source_name=item.provider_name,
                    provider_name=item.provider_name,
                    provider_mode=item.provider_mode,
                    published_at=item.published_at,
                    title=item.title,
                    url=item.url,
                    snippet=item.snippet,
                    full_text=item.full_text,
                    language=item.language,
                    topic_tags=item.topic_tags,
                    impact_hint=_derive_impact_hint(item.topic_tags),
                    confidence=item.confidence,
                    cached_at=item.cached_at,
                    metadata_json=item.metadata,
                )
                self._session.add(row)
                existing_by_key[(item.provider_name, item.url)] = row
            else:
                row.external_ref = item.external_ref
                row.source_name = item.provider_name
                row.provider_name = item.provider_name
                row.provider_mode = item.provider_mode
                row.published_at = item.published_at
                row.title = item.title
                row.url = item.url
                row.snippet = item.snippet
                row.full_text = item.full_text
                row.language = item.language
                row.topic_tags = item.topic_tags
                row.impact_hint = _derive_impact_hint(item.topic_tags)
                row.confidence = item.confidence
                row.cached_at = item.cached_at
                row.metadata_json = item.metadata
            written += 1
        return written

    def _rebuild_latest_digests(self) -> int:
        latest_day = self._session.scalar(select(func.max(func.date(NewsRaw.published_at))))
        if latest_day is None:
            return 0
        latest_day = date.fromisoformat(str(latest_day))
        daily_rows = self._load_rows_for_window(start_date=latest_day, end_date=latest_day, limit=3)
        weekly_rows = self._load_rows_for_window(
            start_date=latest_day - timedelta(days=6),
            end_date=latest_day,
            limit=5,
        )
        self._session.execute(delete(NewsDigest))
        llm_mode = "template_rag" if self._settings.enable_llm else "off"
        created = 0
        for period_type, rows in (("daily", daily_rows), ("weekly", weekly_rows)):
            if not rows:
                continue
            self._session.add(
                NewsDigest(
                    digest_date=latest_day,
                    period_type=period_type,
                    summary_text=self._build_summary_text(rows),
                    bullet_points_json=self._build_bullet_points(rows),
                    source_ids_json=[
                        self._build_ref_id(item.id, item.external_ref) for item in rows
                    ],
                    llm_mode=llm_mode,
                )
            )
            created += 1
        return created

    def _load_rows_for_window(
        self, *, start_date: date, end_date: date, limit: int
    ) -> list[NewsRaw]:
        statement = (
            select(NewsRaw)
            .where(
                func.date(NewsRaw.published_at) >= start_date,
                func.date(NewsRaw.published_at) <= end_date,
            )
            .order_by(NewsRaw.published_at.desc())
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def _load_digest_source_rows(self, *, source_ids: list[str]) -> list[NewsRaw]:
        rows: list[NewsRaw] = []
        for source_id in source_ids:
            row = self._session.scalar(select(NewsRaw).where(NewsRaw.external_ref == source_id))
            if row is not None:
                rows.append(row)
        return rows

    @staticmethod
    def _build_summary_text(rows: list[NewsRaw]) -> str:
        if not rows:
            return "В выбранном периоде новости не найдены."
        tags_counter: Counter[str] = Counter()
        for row in rows:
            tags_counter.update(row.topic_tags or [])
        summary_parts: list[str] = []
        if tags_counter["logistics"] or tags_counter["diesel"]:
            summary_parts.append("давление на закупочные цены")
        if tags_counter["gasoline"] or tags_counter["demand"]:
            summary_parts.append("рост спроса на бензин")
        if tags_counter["fx"] or tags_counter["oil"]:
            summary_parts.append("внешний макрофон по нефти и валюте")
        if not summary_parts:
            summary_parts.append("смешанный новостной фон")
        return (
            "По последним материалам наблюдаются: " + ", ".join(dict.fromkeys(summary_parts)) + "."
        )

    @staticmethod
    def _build_bullet_points(rows: list[NewsRaw]) -> list[str]:
        if not rows:
            return ["Новостных сигналов за период не обнаружено."]
        points: list[str] = []
        for row in rows[:3]:
            snippet = (row.snippet or "").strip()
            points.append(snippet or row.title.strip())
        return points

    @staticmethod
    def _build_news_id(*, provider_name: str, url: str) -> UUID:
        return uuid5(UUID("7d9f5838-cf48-440d-9b7d-6030b93e95b4"), f"{provider_name}:{url}")

    @staticmethod
    def _build_ref_id(news_id: UUID, external_ref: str | None) -> str:
        if external_ref and external_ref.strip():
            return external_ref.strip()
        return f"news_{news_id.hex[:12]}"

    def _build_context_story(self, *, start_date: date, end_date: date) -> dict[str, object]:
        event_context = self._event_catalog_service.build_event_context(
            start_date=start_date, end_date=end_date
        )
        external_context = self._external_context_service.build_external_context_quality()
        indicator_refs = external_context.get("source_refs") or []
        event_refs = [
            {
                "type": "event",
                "ref_id": f"event:{item['event_code']}:{item['start_date']}",
                "title": (
                    f"{item['title']} ({item['start_date']} - {item['end_date']}), "
                    f"pressure={item['pressure_score']:.2f}"
                ),
                "source_type": "event_catalog",
                "confidence": 0.9 if item.get("source_mode") == "db" else 0.75,
            }
            for item in event_context
        ]
        return {
            "window": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "external_context": external_context,
            "event_context": event_context,
            "indicator_refs": indicator_refs,
            "event_refs": event_refs,
        }

    @staticmethod
    def _resolve_news_freshness(*, digest_date: date) -> str:
        age_days = (datetime.now(UTC).date() - digest_date).days
        if age_days <= 1:
            return "fresh"
        if age_days <= 3:
            return "warning"
        return "degraded"


def _normalize_item(
    *,
    item: NormalizedNewsItem,
    provider_mode: str,
    cached_at: datetime | None,
) -> NormalizedNewsItem:
    return NormalizedNewsItem(
        provider_name=item.provider_name,
        provider_mode=provider_mode,  # type: ignore[arg-type]
        published_at=item.published_at,
        title=item.title,
        url=item.url,
        snippet=item.snippet,
        full_text=item.full_text or item.snippet,
        language=item.language or "ru",
        topic_tags=item.topic_tags,
        confidence=item.confidence,
        cached_at=cached_at,
        external_ref=item.external_ref,
        metadata=item.metadata,
    )


def _derive_impact_hint(topic_tags: list[str]) -> str | None:
    tags = set(topic_tags)
    if "logistics" in tags or "diesel" in tags or "wholesale" in tags:
        return "purchase_up"
    if "gasoline" in tags or "demand" in tags:
        return "demand_up"
    if "fx" in tags:
        return "risk_down"
    return None


def _dominant_provider_mode(counter: Counter[str] | dict[str, int]) -> str | None:
    if not counter:
        return None
    normalized = Counter(counter)
    if normalized["live"] > 0:
        return "live"
    if normalized["cached"] > 0:
        return "cached"
    if normalized["manual_snapshot"] > 0:
        return "manual_snapshot"
    return None


def _classify_quality_status(
    *,
    coverage_ratio: float,
    provider_mode_counts: Counter[str],
) -> str:
    if coverage_ratio >= 0.75 and provider_mode_counts.get("live", 0) > 0:
        return "ok"
    if coverage_ratio >= 0.5 and (
        provider_mode_counts.get("cached", 0) > 0
        or provider_mode_counts.get("manual_snapshot", 0) > 0
    ):
        return "warning"
    return "degraded"
