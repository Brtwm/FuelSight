from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.event_catalog_repository import EventCatalogRepository
from app.services.data_generator_config import CURATED_EVENT_CATALOG, CuratedEvent


@dataclass(frozen=True)
class EventWindow:
    event_code: str
    title: str
    start_date: date
    end_date: date
    pressure_score: float
    demand_delta_pct: float
    purchase_delta_pct: float
    source_mode: str


class EventCatalogService:
    def __init__(
        self,
        session: Session,
        *,
        repository: EventCatalogRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or EventCatalogRepository(session)

    def list_curated_events(self) -> tuple[CuratedEvent, ...]:
        rows = self._repository.list_active()
        if not rows:
            return CURATED_EVENT_CATALOG
        events: list[CuratedEvent] = []
        for item in rows:
            events.append(
                CuratedEvent(
                    code=str(item["event_code"]),
                    title=str(item["title"]),
                    start_month=int(item["start_month"]),
                    start_day=int(item["start_day"]),
                    end_month=int(item["end_month"]),
                    end_day=int(item["end_day"]),
                    pressure_score=float(item["pressure_score"]),
                    demand_delta_pct=float(item["demand_delta_pct"]),
                    purchase_delta_pct=float(item["purchase_delta_pct"]),
                    source_mode=str(item.get("source_mode") or "db"),
                )
            )
        return tuple(events)

    def pressure_for_day(self, day_value: date) -> float:
        score = 0.0
        for event in self.list_curated_events():
            if _is_active_on_day(event=event, day_value=day_value):
                score += event.pressure_score
        return max(-1.0, min(1.0, score))

    def effect_for_day(self, day_value: date) -> tuple[float, float]:
        demand_delta_pct = 0.0
        purchase_delta_pct = 0.0
        for event in self.list_curated_events():
            if _is_active_on_day(event=event, day_value=day_value):
                demand_delta_pct += event.demand_delta_pct
                purchase_delta_pct += event.purchase_delta_pct
        return demand_delta_pct, purchase_delta_pct

    def list_event_windows(
        self,
        *,
        start_date: date,
        end_date: date,
        limit: int = 8,
    ) -> list[EventWindow]:
        windows: list[EventWindow] = []
        for event in self.list_curated_events():
            active_days = [
                day_value
                for day_value in _date_range(start_date=start_date, end_date=end_date)
                if _is_active_on_day(event=event, day_value=day_value)
            ]
            if not active_days:
                continue
            windows.append(
                EventWindow(
                    event_code=event.code,
                    title=event.title,
                    start_date=active_days[0],
                    end_date=active_days[-1],
                    pressure_score=event.pressure_score,
                    demand_delta_pct=event.demand_delta_pct,
                    purchase_delta_pct=event.purchase_delta_pct,
                    source_mode=event.source_mode,
                )
            )

        windows.sort(
            key=lambda item: (
                item.start_date.toordinal(),
                -item.pressure_score,
                item.event_code,
            )
        )
        return windows[: max(limit, 1)]

    def build_event_overlays(
        self,
        *,
        start_date: date,
        end_date: date,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        overlays: list[dict[str, Any]] = []
        for window in self.list_event_windows(start_date=start_date, end_date=end_date, limit=limit):
            points = [
                {
                    "date": day_value.isoformat(),
                    "value": window.pressure_score,
                    "label": window.title if day_value == window.start_date else None,
                }
                for day_value in _date_range(start_date=window.start_date, end_date=window.end_date)
            ]
            overlays.append(
                {
                    "code": f"event:{window.event_code}",
                    "label": window.title,
                    "unit": "score",
                    "provider_mode": "manual_snapshot",
                    "points": points,
                }
            )
        return overlays

    def build_event_context(
        self,
        *,
        start_date: date,
        end_date: date,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        context: list[dict[str, Any]] = []
        for window in self.list_event_windows(start_date=start_date, end_date=end_date, limit=limit):
            context.append(
                {
                    "event_code": window.event_code,
                    "title": window.title,
                    "start_date": window.start_date.isoformat(),
                    "end_date": window.end_date.isoformat(),
                    "pressure_score": round(window.pressure_score, 4),
                    "demand_delta_pct": round(window.demand_delta_pct, 4),
                    "purchase_delta_pct": round(window.purchase_delta_pct, 4),
                    "source_mode": window.source_mode,
                }
            )
        return context


def _is_active_on_day(*, event: CuratedEvent, day_value: date) -> bool:
    month_day = day_value.month * 100 + day_value.day
    start_key = event.start_month * 100 + event.start_day
    end_key = event.end_month * 100 + event.end_day
    if start_key <= end_key:
        return start_key <= month_day <= end_key
    return month_day >= start_key or month_day <= end_key


def _date_range(*, start_date: date, end_date: date) -> list[date]:
    days = (end_date - start_date).days
    return [start_date + timedelta(days=index) for index in range(days + 1)]
