from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.integrations.news.types import NormalizedNewsItem


class NewsCacheManager:
    def __init__(self, root_dir: str | Path) -> None:
        self._root = Path(root_dir)
        self._cache_root = self._root / "cache"
        self._last_good_root = self._root / "last_good"
        self._cache_root.mkdir(parents=True, exist_ok=True)
        self._last_good_root.mkdir(parents=True, exist_ok=True)

    @property
    def root_dir(self) -> Path:
        return self._root

    def cache_key(self, *, provider_name: str) -> str:
        return f"cache/{provider_name.strip().lower()}.json"

    def write_cache(
        self,
        *,
        provider_name: str,
        items: list[NormalizedNewsItem],
        fetched_at: datetime,
    ) -> str:
        path = self._cache_path(provider_name=provider_name)
        self._write_items_file(path=path, items=items, fetched_at=fetched_at)
        return self.cache_key(provider_name=provider_name)

    def read_cache(
        self,
        *,
        provider_name: str,
        lookback_days: int,
        ttl_seconds: int,
    ) -> tuple[list[NormalizedNewsItem], datetime] | None:
        path = self._cache_path(provider_name=provider_name)
        payload = self._read_items_file(path)
        if payload is None:
            return None
        fetched_at = payload[1]
        if datetime.now(UTC) - fetched_at > timedelta(seconds=max(ttl_seconds, 1)):
            return None
        return self._filter_items(payload[0], lookback_days=lookback_days), fetched_at

    def write_last_good(
        self,
        *,
        provider_name: str,
        items: list[NormalizedNewsItem],
        fetched_at: datetime,
    ) -> str:
        path = self._last_good_path(provider_name=provider_name)
        self._write_items_file(path=path, items=items, fetched_at=fetched_at)
        return str(path)

    def read_last_good(
        self,
        *,
        provider_name: str,
        lookback_days: int,
    ) -> tuple[list[NormalizedNewsItem], datetime] | None:
        path = self._last_good_path(provider_name=provider_name)
        payload = self._read_items_file(path)
        if payload is None:
            return None
        return self._filter_items(payload[0], lookback_days=lookback_days), payload[1]

    def _cache_path(self, *, provider_name: str) -> Path:
        return self._cache_root / f"{provider_name.strip().lower()}.json"

    def _last_good_path(self, *, provider_name: str) -> Path:
        return self._last_good_root / f"{provider_name.strip().lower()}.json"

    def _read_items_file(self, path: Path) -> tuple[list[NormalizedNewsItem], datetime] | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        fetched_at_raw = payload.get("fetched_at")
        if not isinstance(fetched_at_raw, str):
            return None
        try:
            fetched_at = datetime.fromisoformat(fetched_at_raw)
        except ValueError:
            return None
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        else:
            fetched_at = fetched_at.astimezone(UTC)

        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            return [], fetched_at
        items: list[NormalizedNewsItem] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            item = NormalizedNewsItem.from_json_dict(raw_item)
            if item is not None:
                items.append(item)
        return items, fetched_at

    def _write_items_file(
        self,
        *,
        path: Path,
        items: list[NormalizedNewsItem],
        fetched_at: datetime,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched_at": fetched_at.astimezone(UTC).isoformat(),
            "items": [item.to_json_dict() for item in items],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _filter_items(
        items: list[NormalizedNewsItem],
        *,
        lookback_days: int,
    ) -> list[NormalizedNewsItem]:
        if lookback_days <= 0:
            return list(items)
        threshold = datetime.now(UTC) - timedelta(days=lookback_days)
        return [item for item in items if item.published_at >= threshold]
