from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.schemas.common import DataProviderMode, FreshnessStatus, QualityStatus


@dataclass(frozen=True)
class NormalizedNewsItem:
    provider_name: str
    provider_mode: DataProviderMode
    published_at: datetime
    title: str
    url: str
    snippet: str | None = None
    full_text: str | None = None
    language: str | None = None
    topic_tags: list[str] = field(default_factory=list)
    confidence: float | None = None
    cached_at: datetime | None = None
    external_ref: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("published_at", "cached_at"):
            value = payload.get(key)
            if isinstance(value, datetime):
                payload[key] = value.astimezone(UTC).isoformat()
        return payload

    @classmethod
    def from_json_dict(cls, payload: dict[str, Any]) -> "NormalizedNewsItem | None":
        try:
            published_at = _parse_datetime(payload.get("published_at"))
        except ValueError:
            return None
        if published_at is None:
            return None
        cached_at = None
        cached_at_raw = payload.get("cached_at")
        if cached_at_raw is not None:
            try:
                cached_at = _parse_datetime(cached_at_raw)
            except ValueError:
                cached_at = None
        provider_name = str(payload.get("provider_name", "")).strip()
        provider_mode = str(payload.get("provider_mode", "")).strip()
        title = str(payload.get("title", "")).strip()
        url = str(payload.get("url", "")).strip()
        if not provider_name or not provider_mode or not title or not url:
            return None
        raw_topic_tags = payload.get("topic_tags")
        topic_tags = [
            str(item).strip().lower()
            for item in raw_topic_tags
            if isinstance(item, str) and item.strip()
        ] if isinstance(raw_topic_tags, list) else []
        confidence_raw = payload.get("confidence")
        confidence = None
        if confidence_raw is not None:
            try:
                confidence = float(confidence_raw)
            except (TypeError, ValueError):
                confidence = None
        metadata = payload.get("metadata")
        return cls(
            provider_name=provider_name,
            provider_mode=provider_mode,  # type: ignore[arg-type]
            published_at=published_at,
            title=title,
            url=url,
            snippet=_normalize_optional_text(payload.get("snippet")),
            full_text=_normalize_optional_text(payload.get("full_text")),
            language=_normalize_optional_text(payload.get("language")),
            topic_tags=topic_tags,
            confidence=confidence,
            cached_at=cached_at,
            external_ref=_normalize_optional_text(payload.get("external_ref")),
            metadata=metadata if isinstance(metadata, dict) else {},
        )


@dataclass(frozen=True)
class NewsProviderResult:
    provider_name: str
    provider_mode: DataProviderMode
    freshness_status: FreshnessStatus
    quality_status: QualityStatus
    items: list[NormalizedNewsItem]
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    cache_key: str | None = None
    last_good_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _normalize_optional_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
