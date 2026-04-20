from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.event_catalog import EventCatalog


@dataclass(frozen=True)
class EventCatalogUpsertRow:
    event_code: str
    title: str
    start_month: int
    start_day: int
    end_month: int
    end_day: int
    pressure_score: float
    demand_delta_pct: float
    purchase_delta_pct: float
    source_mode: str
    is_active: bool
    metadata_json: dict[str, Any]


class EventCatalogRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_active(self) -> list[dict[str, Any]]:
        if not hasattr(self._session, "scalars"):
            return []
        statement: Select[tuple[EventCatalog]] = (
            select(EventCatalog)
            .where(EventCatalog.is_active.is_(True))
            .order_by(EventCatalog.event_code.asc())
        )
        try:
            rows = list(self._session.scalars(statement))
        except Exception:
            return []
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "event_code": row.event_code,
                    "title": row.title,
                    "start_month": int(row.start_month),
                    "start_day": int(row.start_day),
                    "end_month": int(row.end_month),
                    "end_day": int(row.end_day),
                    "pressure_score": _to_float(row.pressure_score),
                    "demand_delta_pct": _to_float(row.demand_delta_pct),
                    "purchase_delta_pct": _to_float(row.purchase_delta_pct),
                    "source_mode": row.source_mode,
                    "metadata_json": row.metadata_json or {},
                    "updated_at": row.updated_at,
                }
            )
        return result

    def upsert_many(self, rows: list[EventCatalogUpsertRow]) -> int:
        if not rows:
            return 0
        payload = [
            {
                "event_code": item.event_code,
                "title": item.title,
                "start_month": item.start_month,
                "start_day": item.start_day,
                "end_month": item.end_month,
                "end_day": item.end_day,
                "pressure_score": item.pressure_score,
                "demand_delta_pct": item.demand_delta_pct,
                "purchase_delta_pct": item.purchase_delta_pct,
                "source_mode": item.source_mode,
                "is_active": item.is_active,
                "metadata_json": item.metadata_json,
            }
            for item in rows
        ]
        statement = insert(EventCatalog).values(payload)
        statement = statement.on_conflict_do_update(
            index_elements=["event_code"],
            set_={
                "title": statement.excluded.title,
                "start_month": statement.excluded.start_month,
                "start_day": statement.excluded.start_day,
                "end_month": statement.excluded.end_month,
                "end_day": statement.excluded.end_day,
                "pressure_score": statement.excluded.pressure_score,
                "demand_delta_pct": statement.excluded.demand_delta_pct,
                "purchase_delta_pct": statement.excluded.purchase_delta_pct,
                "source_mode": statement.excluded.source_mode,
                "is_active": statement.excluded.is_active,
                "metadata_json": statement.excluded.metadata_json,
                "updated_at": datetime.now(UTC),
            },
        )
        self._session.execute(statement)
        self._session.flush()
        return len(rows)


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, int):
        return float(value)
    return value
