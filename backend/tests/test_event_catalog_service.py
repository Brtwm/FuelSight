from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.services.event_catalog_service import EventCatalogService


class _FakeRepository:
    def __init__(self, rows):
        self._rows = rows

    def list_active(self):  # noqa: ANN201
        return self._rows


def test_event_catalog_falls_back_to_seed_when_db_is_empty() -> None:
    service = EventCatalogService(
        session=SimpleNamespace(),
        repository=_FakeRepository([]),
    )

    events = service.list_curated_events()
    assert events
    assert all(item.source_mode == "fallback_seed" for item in events)

    overlays = service.build_event_overlays(
        start_date=date(2026, 3, 1),
        end_date=date(2026, 4, 30),
    )
    assert overlays
    assert overlays[0]["code"].startswith("event:")
    assert overlays[0]["provider_mode"] == "manual_snapshot"


def test_event_catalog_uses_db_rows_when_available() -> None:
    service = EventCatalogService(
        session=SimpleNamespace(),
        repository=_FakeRepository(
            [
                {
                    "event_code": "test_event",
                    "title": "Тестовое событие",
                    "start_month": 4,
                    "start_day": 10,
                    "end_month": 4,
                    "end_day": 12,
                    "pressure_score": 0.42,
                    "demand_delta_pct": 1.5,
                    "purchase_delta_pct": 2.1,
                    "source_mode": "db",
                    "metadata_json": {},
                }
            ]
        ),
    )

    context = service.build_event_context(
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 30),
    )
    assert context
    assert context[0]["event_code"] == "test_event"
    assert context[0]["source_mode"] == "db"
