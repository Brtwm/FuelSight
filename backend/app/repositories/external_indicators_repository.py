from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.external_indicator_daily import ExternalIndicatorDaily

VALID_PROVIDER_MODES = {"live", "cached", "manual_snapshot"}


@dataclass(frozen=True)
class ExternalIndicatorUpsertRow:
    indicator_date: date
    indicator_code: str
    value_numeric: float
    unit: str
    provider_name: str
    provider_mode: str
    cache_key: str | None
    metadata_json: dict[str, Any]


class ExternalIndicatorsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def upsert_many(self, rows: list[ExternalIndicatorUpsertRow]) -> int:
        if not rows:
            return 0
        values = [
            {
                "indicator_date": item.indicator_date,
                "indicator_code": item.indicator_code,
                "value_numeric": item.value_numeric,
                "unit": item.unit,
                "provider_name": item.provider_name,
                "provider_mode": item.provider_mode,
                "cache_key": item.cache_key,
                "metadata_json": item.metadata_json,
            }
            for item in rows
        ]
        statement = insert(ExternalIndicatorDaily).values(values)
        statement = statement.on_conflict_do_update(
            index_elements=["indicator_date", "indicator_code", "provider_name"],
            set_={
                "value_numeric": statement.excluded.value_numeric,
                "unit": statement.excluded.unit,
                "provider_mode": statement.excluded.provider_mode,
                "cache_key": statement.excluded.cache_key,
                "metadata_json": statement.excluded.metadata_json,
                "ingested_at": func.now(),
            },
        )
        self._session.execute(statement)
        self._session.flush()
        return len(rows)

    def get_latest_value(self, indicator_code: str) -> dict[str, Any] | None:
        normalized = indicator_code.strip().lower()
        statement: Select[tuple[ExternalIndicatorDaily]] = (
            select(ExternalIndicatorDaily)
            .where(ExternalIndicatorDaily.indicator_code == normalized)
            .order_by(
                ExternalIndicatorDaily.indicator_date.desc(),
                ExternalIndicatorDaily.ingested_at.desc(),
            )
            .limit(1)
        )
        row = self._session.scalar(statement)
        if row is None:
            return None
        return {
            "indicator_code": row.indicator_code,
            "indicator_date": row.indicator_date,
            "value_numeric": float(row.value_numeric),
            "unit": row.unit,
            "provider_name": row.provider_name,
            "provider_mode": row.provider_mode,
            "cache_key": row.cache_key,
            "metadata_json": row.metadata_json or {},
            "ingested_at": row.ingested_at,
        }

    def get_latest_good_snapshot(
        self, indicator_codes: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        normalized_codes = _normalize_indicator_codes(indicator_codes)
        snapshots: dict[str, dict[str, Any] | None] = {code: None for code in normalized_codes}
        for indicator_code in normalized_codes:
            statement: Select[tuple[ExternalIndicatorDaily]] = (
                select(ExternalIndicatorDaily)
                .where(
                    ExternalIndicatorDaily.indicator_code == indicator_code,
                    ExternalIndicatorDaily.provider_mode.in_(VALID_PROVIDER_MODES),
                )
                .order_by(
                    ExternalIndicatorDaily.indicator_date.desc(),
                    ExternalIndicatorDaily.ingested_at.desc(),
                )
                .limit(1)
            )
            row = self._session.scalar(statement)
            if row is None:
                continue
            snapshots[indicator_code] = {
                "indicator_code": row.indicator_code,
                "indicator_date": row.indicator_date,
                "value_numeric": float(row.value_numeric),
                "unit": row.unit,
                "provider_name": row.provider_name,
                "provider_mode": row.provider_mode,
                "cache_key": row.cache_key,
                "metadata_json": row.metadata_json or {},
                "ingested_at": row.ingested_at,
            }
        return snapshots

    def get_coverage_summary(
        self,
        *,
        start_date: date,
        end_date: date,
        indicator_codes: list[str],
    ) -> list[dict[str, Any]]:
        normalized_codes = _normalize_indicator_codes(indicator_codes)
        expected_days = max((end_date - start_date).days + 1, 0)
        summary: list[dict[str, Any]] = []
        for indicator_code in normalized_codes:
            count_statement = select(
                func.count(func.distinct(ExternalIndicatorDaily.indicator_date))
            ).where(
                ExternalIndicatorDaily.indicator_code == indicator_code,
                ExternalIndicatorDaily.indicator_date >= start_date,
                ExternalIndicatorDaily.indicator_date <= end_date,
            )
            actual_days = int(self._session.scalar(count_statement) or 0)
            latest_value = self.get_latest_value(indicator_code)
            summary.append(
                {
                    "indicator_code": indicator_code,
                    "expected_days": expected_days,
                    "actual_days": actual_days,
                    "coverage_ratio": (actual_days / expected_days) if expected_days > 0 else 0.0,
                    "latest_date": latest_value["indicator_date"] if latest_value else None,
                    "latest_mode": latest_value["provider_mode"] if latest_value else None,
                }
            )
        return summary

    def get_series(
        self,
        *,
        start_date: date,
        end_date: date,
        indicator_codes: list[str],
    ) -> dict[str, dict[date, float]]:
        normalized_codes = _normalize_indicator_codes(indicator_codes)
        if not normalized_codes:
            return {}

        statement: Select[tuple[ExternalIndicatorDaily]] = (
            select(ExternalIndicatorDaily)
            .where(
                ExternalIndicatorDaily.indicator_code.in_(normalized_codes),
                ExternalIndicatorDaily.indicator_date >= start_date,
                ExternalIndicatorDaily.indicator_date <= end_date,
            )
            .order_by(
                ExternalIndicatorDaily.indicator_code.asc(),
                ExternalIndicatorDaily.indicator_date.asc(),
                ExternalIndicatorDaily.ingested_at.desc(),
            )
        )
        rows = self._session.scalars(statement)

        by_indicator: dict[str, dict[date, float]] = {code: {} for code in normalized_codes}
        for item in rows:
            indicator_map = by_indicator[item.indicator_code]
            if item.indicator_date in indicator_map:
                continue
            indicator_map[item.indicator_date] = float(item.value_numeric)
        return by_indicator

    def get_points_with_mode(
        self,
        *,
        start_date: date,
        end_date: date,
        indicator_codes: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        normalized_codes = _normalize_indicator_codes(indicator_codes)
        if not normalized_codes:
            return {}

        statement: Select[tuple[ExternalIndicatorDaily]] = (
            select(ExternalIndicatorDaily)
            .where(
                ExternalIndicatorDaily.indicator_code.in_(normalized_codes),
                ExternalIndicatorDaily.indicator_date >= start_date,
                ExternalIndicatorDaily.indicator_date <= end_date,
            )
            .order_by(
                ExternalIndicatorDaily.indicator_code.asc(),
                ExternalIndicatorDaily.indicator_date.asc(),
                ExternalIndicatorDaily.ingested_at.desc(),
            )
        )
        rows = self._session.scalars(statement)
        by_indicator: dict[str, list[dict[str, Any]]] = {code: [] for code in normalized_codes}
        seen: set[tuple[str, date]] = set()
        for item in rows:
            pair = (item.indicator_code, item.indicator_date)
            if pair in seen:
                continue
            seen.add(pair)
            by_indicator[item.indicator_code].append(
                {
                    "indicator_date": item.indicator_date,
                    "value_numeric": float(item.value_numeric),
                    "unit": item.unit,
                    "provider_mode": item.provider_mode,
                    "metadata_json": item.metadata_json or {},
                }
            )
        return by_indicator


def _normalize_indicator_codes(indicator_codes: list[str]) -> list[str]:
    normalized: list[str] = []
    for indicator_code in indicator_codes:
        value = indicator_code.strip().lower()
        if value and value not in normalized:
            normalized.append(value)
    return normalized
