from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import DataProviderMode, FreshnessStatus

DigestPeriodType = Literal["daily", "weekly"]


class NewsDigestPayload(BaseModel):
    digest_date: date
    period_type: DigestPeriodType
    summary_text: str
    bullet_points: list[str]
    source_ids: list[str]
    llm_mode: str
    provider_mode: DataProviderMode | None = None
    news_freshness: FreshnessStatus | None = None
    context_story: dict[str, Any] | None = None


class NewsSearchItem(BaseModel):
    id: UUID
    ref_id: str
    source_name: str
    provider_name: str | None = None
    published_at: datetime
    title: str
    url: str
    snippet: str | None = None
    topic_tags: list[str] = Field(default_factory=list)
    impact_hint: str | None = None
    provider_mode: DataProviderMode | None = None
    confidence: float | None = None
    cached_at: datetime | None = None


class NewsRefreshPayload(BaseModel):
    status: str
    imported_news_count: int
    created_digests: int
    provider_mode: DataProviderMode | None = None
    news_freshness: FreshnessStatus | None = None
    quality_status: str | None = None
    provider_mode_counts: dict[str, int] = Field(default_factory=dict)
    written_news_count: int = 0
    coverage_ratio: float | None = None
    cache_dir: str | None = None
    last_success_at: datetime | None = None
