from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.integrations.external_indicators.types import ExternalIndicatorPoint


class ExternalIndicatorsCacheManager:
    def __init__(self, root_dir: str | Path) -> None:
        self._root = Path(root_dir)
        self._cache_root = self._root / "cache"
        self._last_good_root = self._root / "last_good"
        self._cache_root.mkdir(parents=True, exist_ok=True)
        self._last_good_root.mkdir(parents=True, exist_ok=True)

    @property
    def root_dir(self) -> Path:
        return self._root

    def cache_key(self, *, provider_name: str, indicator_code: str) -> str:
        return f"cache/{provider_name.strip().lower()}/{indicator_code.strip().lower()}.json"

    def write_cache(
        self,
        *,
        provider_name: str,
        indicator_code: str,
        points: list[ExternalIndicatorPoint],
        fetched_at: datetime,
    ) -> str:
        path = self._cache_path(provider_name=provider_name, indicator_code=indicator_code)
        self._write_points_file(path=path, points=points, fetched_at=fetched_at)
        return self.cache_key(provider_name=provider_name, indicator_code=indicator_code)

    def read_cache(
        self,
        *,
        provider_name: str,
        indicator_code: str,
        start_date: date,
        end_date: date,
        ttl_seconds: int,
    ) -> list[ExternalIndicatorPoint] | None:
        path = self._cache_path(provider_name=provider_name, indicator_code=indicator_code)
        payload = self._read_points_file(path)
        if payload is None:
            return None
        fetched_at = self._parse_datetime(payload.get("fetched_at"))
        if fetched_at is None:
            return None
        if datetime.now(UTC) - fetched_at > timedelta(seconds=max(ttl_seconds, 1)):
            return None

        points = self._deserialize_points(payload.get("points"))
        filtered = self._filter_points(points=points, start_date=start_date, end_date=end_date)
        if not filtered:
            return None
        return filtered

    def write_last_good(
        self,
        *,
        provider_name: str,
        indicator_code: str,
        points: list[ExternalIndicatorPoint],
        fetched_at: datetime,
    ) -> str:
        path = self._last_good_path(provider_name=provider_name, indicator_code=indicator_code)
        self._write_points_file(path=path, points=points, fetched_at=fetched_at)
        return str(path)

    def read_last_good(
        self,
        *,
        provider_name: str,
        indicator_code: str,
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint] | None:
        path = self._last_good_path(provider_name=provider_name, indicator_code=indicator_code)
        payload = self._read_points_file(path)
        if payload is None:
            return None
        points = self._deserialize_points(payload.get("points"))
        filtered = self._filter_points(points=points, start_date=start_date, end_date=end_date)
        if not filtered:
            return None
        return filtered

    def _cache_path(self, *, provider_name: str, indicator_code: str) -> Path:
        return (
            self._cache_root
            / provider_name.strip().lower()
            / f"{indicator_code.strip().lower()}.json"
        )

    def _last_good_path(self, *, provider_name: str, indicator_code: str) -> Path:
        return (
            self._last_good_root
            / provider_name.strip().lower()
            / f"{indicator_code.strip().lower()}.json"
        )

    @staticmethod
    def _filter_points(
        *,
        points: list[ExternalIndicatorPoint],
        start_date: date,
        end_date: date,
    ) -> list[ExternalIndicatorPoint]:
        return [item for item in points if start_date <= item.indicator_date <= end_date]

    @staticmethod
    def _read_points_file(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not isinstance(value, str):
            return None
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    def _write_points_file(
        self,
        *,
        path: Path,
        points: list[ExternalIndicatorPoint],
        fetched_at: datetime,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        serializable_points = [asdict(point) for point in points]
        for item in serializable_points:
            item["indicator_date"] = item["indicator_date"].isoformat()
        payload = {
            "fetched_at": fetched_at.astimezone(UTC).isoformat(),
            "points": serializable_points,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _deserialize_points(raw_items: Any) -> list[ExternalIndicatorPoint]:
        if not isinstance(raw_items, list):
            return []
        points: list[ExternalIndicatorPoint] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            raw_date = item.get("indicator_date")
            if not isinstance(raw_date, str):
                continue
            try:
                parsed_date = date.fromisoformat(raw_date)
            except ValueError:
                continue
            try:
                value_numeric = float(item.get("value_numeric"))
            except (TypeError, ValueError):
                continue
            unit = item.get("unit")
            if not isinstance(unit, str) or not unit:
                continue
            metadata = item.get("metadata")
            points.append(
                ExternalIndicatorPoint(
                    indicator_date=parsed_date,
                    value_numeric=value_numeric,
                    unit=unit,
                    metadata=metadata if isinstance(metadata, dict) else {},
                )
            )
        return points
