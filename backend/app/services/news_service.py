from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import NewsDigest, NewsRaw

FIXTURE_NEWS: tuple[dict[str, object], ...] = (
    {
        "external_ref": "gdelt_2026_03_24_01",
        "source_name": "GDELT",
        "published_at": "2026-03-24T08:30:00+00:00",
        "title": "Логистические ограничения по южному направлению поставок ДТ",
        "url": "https://example.local/news/gdelt_2026_03_24_01",
        "snippet": "Логистические узкие места повышают риск роста закупочных цен на ДТ.",
        "full_text": (
            "Ограничения в логистике по южному направлению усиливают давление "
            "на закупочные цены и создают риски дефицита объема."
        ),
        "language": "ru",
        "topic_tags": ["logistics", "diesel", "supply"],
        "impact_hint": "purchase_up",
    },
    {
        "external_ref": "gdelt_2026_03_25_02",
        "source_name": "GDELT",
        "published_at": "2026-03-25T11:00:00+00:00",
        "title": "Индикативы оптовых цен на бензин показывают умеренный рост",
        "url": "https://example.local/news/gdelt_2026_03_25_02",
        "snippet": "Оптовые индикативы AI-92 и AI-95 растут вторую неделю подряд.",
        "full_text": (
            "Умеренный рост индикативов на бензин сохраняется в недельном горизонте. "
            "Для розницы это формирует давление на маржу."
        ),
        "language": "ru",
        "topic_tags": ["wholesale", "gasoline", "prices"],
        "impact_hint": "purchase_up",
    },
    {
        "external_ref": "gdelt_2026_03_26_03",
        "source_name": "GDELT",
        "published_at": "2026-03-26T09:20:00+00:00",
        "title": "Курс валюты стабилизировался, ценовой риск краткосрочно снижен",
        "url": "https://example.local/news/gdelt_2026_03_26_03",
        "snippet": "Стабилизация валюты снижает волатильность закупочной цены.",
        "full_text": (
            "Стабильный курс валюты уменьшает краткосрочный риск резкого роста "
            "закупочной цены для импортозависимых компонентов."
        ),
        "language": "ru",
        "topic_tags": ["fx", "risk", "pricing"],
        "impact_hint": "risk_down",
    },
    {
        "external_ref": "gdelt_2026_03_27_04",
        "source_name": "GDELT",
        "published_at": "2026-03-27T14:10:00+00:00",
        "title": "Плановые ремонты НПЗ усиливают сезонный риск по ДТ",
        "url": "https://example.local/news/gdelt_2026_03_27_04",
        "snippet": "Ремонтные работы могут ограничить предложение ДТ в отдельные недели.",
        "full_text": (
            "Плановые ремонты на части НПЗ в ближайшие недели создают "
            "дополнительный риск дефицита предложения ДТ."
        ),
        "language": "ru",
        "topic_tags": ["diesel", "refinery", "seasonality"],
        "impact_hint": "purchase_up",
    },
    {
        "external_ref": "gdelt_2026_03_28_05",
        "source_name": "GDELT",
        "published_at": "2026-03-28T07:40:00+00:00",
        "title": "Спрос на бензин растет перед началом отпускного сезона",
        "url": "https://example.local/news/gdelt_2026_03_28_05",
        "snippet": "Ожидается рост спроса на AI-92/AI-95 в выходные и праздничные периоды.",
        "full_text": (
            "Предсезонный рост мобильности поддерживает спрос на бензин, "
            "что может частично компенсировать давление на маржу."
        ),
        "language": "ru",
        "topic_tags": ["demand", "gasoline", "seasonality"],
        "impact_hint": "demand_up",
    },
)


@dataclass(frozen=True)
class NewsRefreshResult:
    status: str
    imported_news_count: int
    created_digests: int


class NewsService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    def refresh_news(self) -> NewsRefreshResult:
        fixture_news = self._build_fixture_news()
        if not fixture_news:
            return NewsRefreshResult(status="noop", imported_news_count=0, created_digests=0)

        self._session.execute(delete(NewsDigest))
        self._session.execute(delete(NewsRaw))

        for row in fixture_news:
            self._session.add(
                NewsRaw(
                    id=row["id"],
                    external_ref=row["external_ref"],
                    source_name=row["source_name"],
                    published_at=row["published_at"],
                    title=row["title"],
                    url=row["url"],
                    snippet=row["snippet"],
                    full_text=row["full_text"],
                    language=row["language"],
                    topic_tags=row["topic_tags"],
                    impact_hint=row["impact_hint"],
                )
            )

        latest_day = max(item["published_at"].date() for item in fixture_news)
        day_rows = [
            item for item in fixture_news if item["published_at"].date() == latest_day
        ][:3]
        week_start = latest_day - timedelta(days=6)
        week_rows = [
            item
            for item in fixture_news
            if week_start <= item["published_at"].date() <= latest_day
        ][:5]

        llm_mode = "template_rag" if self._settings.enable_llm else "off"

        self._session.add(
            NewsDigest(
                digest_date=latest_day,
                period_type="daily",
                summary_text=self._build_summary_text(day_rows),
                bullet_points_json=self._build_bullet_points(day_rows),
                source_ids_json=[item["ref_id"] for item in day_rows],
                llm_mode=llm_mode,
            )
        )
        self._session.add(
            NewsDigest(
                digest_date=latest_day,
                period_type="weekly",
                summary_text=self._build_summary_text(week_rows),
                bullet_points_json=self._build_bullet_points(week_rows),
                source_ids_json=[item["ref_id"] for item in week_rows],
                llm_mode=llm_mode,
            )
        )
        self._session.commit()
        return NewsRefreshResult(
            status="ok",
            imported_news_count=len(fixture_news),
            created_digests=2,
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
        return {
            "digest_date": row.digest_date,
            "period_type": row.period_type,
            "summary_text": row.summary_text,
            "bullet_points": list(row.bullet_points_json),
            "source_ids": list(row.source_ids_json),
            "llm_mode": row.llm_mode,
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
        statement = select(NewsRaw).order_by(NewsRaw.published_at.desc()).limit(normalized_limit)

        if q and q.strip():
            pattern = f"%{q.strip()}%"
            statement = statement.where(
                or_(
                    NewsRaw.title.ilike(pattern),
                    NewsRaw.snippet.ilike(pattern),
                    NewsRaw.full_text.ilike(pattern),
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

        rows = list(self._session.scalars(statement))
        return [
            {
                "id": row.id,
                "ref_id": self._build_ref_id(row.id, row.external_ref),
                "source_name": row.source_name,
                "published_at": row.published_at,
                "title": row.title,
                "url": row.url,
                "snippet": row.snippet,
                "topic_tags": row.topic_tags,
                "impact_hint": row.impact_hint,
            }
            for row in rows
        ]

    def _build_fixture_news(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for item in FIXTURE_NEWS:
            external_ref = str(item["external_ref"])
            source_name = str(item["source_name"])
            published_at = datetime.fromisoformat(str(item["published_at"]))
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=UTC)
            topic_tags = [str(tag).strip().lower() for tag in list(item["topic_tags"])]
            row_id = uuid5(NAMESPACE_URL, f"fuelsight-news:{external_ref}")
            rows.append(
                {
                    "id": row_id,
                    "ref_id": self._build_ref_id(row_id, external_ref),
                    "external_ref": external_ref,
                    "source_name": source_name,
                    "published_at": published_at,
                    "title": str(item["title"]),
                    "url": str(item["url"]),
                    "snippet": str(item["snippet"]),
                    "full_text": str(item["full_text"]),
                    "language": str(item["language"]),
                    "topic_tags": topic_tags,
                    "impact_hint": str(item["impact_hint"]),
                }
            )
        rows.sort(key=lambda row: row["published_at"], reverse=True)
        return rows

    @staticmethod
    def _build_summary_text(rows: list[dict[str, object]]) -> str:
        if not rows:
            return "В выбранном периоде новости не найдены."
        impact_map = {
            "purchase_up": "давление на закупочные цены",
            "demand_up": "рост спроса",
            "risk_down": "снижение краткосрочных рисков",
        }
        impacts = []
        for row in rows:
            key = str(row.get("impact_hint", "")).strip()
            if key in impact_map:
                impacts.append(impact_map[key])
        unique_impacts = list(dict.fromkeys(impacts))
        if not unique_impacts:
            unique_impacts = ["смешанный новостной фон"]
        return (
            "По последним материалам наблюдаются: "
            + ", ".join(unique_impacts[:3])
            + "."
        )

    @staticmethod
    def _build_bullet_points(rows: list[dict[str, object]]) -> list[str]:
        if not rows:
            return ["Новостных сигналов за период не обнаружено."]
        points: list[str] = []
        for row in rows[:3]:
            snippet = str(row.get("snippet", "")).strip()
            if snippet:
                points.append(snippet)
            else:
                points.append(str(row.get("title", "")).strip())
        return points

    @staticmethod
    def _build_ref_id(news_id: UUID, external_ref: str | None) -> str:
        if external_ref and external_ref.strip():
            return external_ref.strip()
        return f"news_{news_id.hex[:12]}"
