from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from app.integrations.external_indicators.adapters import (
    BrentEiaAdapter,
    CuratedWholesaleAdapter,
    EventPressureAdapter,
    HolidayFlagAdapter,
    UsdRubCbrAdapter,
)
from app.integrations.external_indicators.cache import ExternalIndicatorsCacheManager
from app.integrations.external_indicators.types import ExternalIndicatorPoint


def test_usd_rub_cbr_adapter_parses_and_forward_fills(monkeypatch) -> None:
    xml = (
        '<?xml version="1.0" encoding="windows-1251"?>'
        '<ValCurs><Record Date="01.01.2025"><Value>90,10</Value></Record>'
        '<Record Date="03.01.2025"><Value>91,00</Value></Record></ValCurs>'
    )
    monkeypatch.setattr(
        "app.integrations.external_indicators.adapters._read_text_from_url",
        lambda _: xml,
    )
    adapter = UsdRubCbrAdapter()
    points = adapter.fetch_live_range(
        indicator_code="usd_rub",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 4),
    )

    assert len(points) == 4
    assert points[1].value_numeric == points[0].value_numeric
    assert points[-1].value_numeric == 91.0


def test_brent_eia_adapter_parses_and_forward_fills(monkeypatch) -> None:
    payload = {
        "response": {
            "data": [
                {"period": "2025-01-01", "value": "81.2"},
                {"period": "2025-01-03", "value": "82.7"},
            ]
        }
    }
    monkeypatch.setattr(
        "app.integrations.external_indicators.adapters._read_json_from_url",
        lambda _: payload,
    )
    adapter = BrentEiaAdapter()
    points = adapter.fetch_live_range(
        indicator_code="crude_brent_usd",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 4),
    )

    assert len(points) == 4
    assert points[1].value_numeric == points[0].value_numeric
    assert points[-1].value_numeric == 82.7


def test_cache_manager_respects_ttl_and_last_good(tmp_path: Path) -> None:
    manager = ExternalIndicatorsCacheManager(tmp_path / "external")
    points = [
        ExternalIndicatorPoint(
            indicator_date=date(2025, 1, 1), value_numeric=81.0, unit="usd_per_bbl"
        ),
        ExternalIndicatorPoint(
            indicator_date=date(2025, 1, 2), value_numeric=82.0, unit="usd_per_bbl"
        ),
    ]
    manager.write_cache(
        provider_name="eia",
        indicator_code="crude_brent_usd",
        points=points,
        fetched_at=datetime.now(UTC),
    )
    cached = manager.read_cache(
        provider_name="eia",
        indicator_code="crude_brent_usd",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        ttl_seconds=24 * 60 * 60,
    )
    assert cached is not None and len(cached) == 2

    manager.write_cache(
        provider_name="eia",
        indicator_code="crude_brent_usd",
        points=points,
        fetched_at=datetime.now(UTC) - timedelta(days=3),
    )
    expired = manager.read_cache(
        provider_name="eia",
        indicator_code="crude_brent_usd",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
        ttl_seconds=24 * 60 * 60,
    )
    assert expired is None

    manager.write_last_good(
        provider_name="eia",
        indicator_code="crude_brent_usd",
        points=points,
        fetched_at=datetime.now(UTC),
    )
    last_good = manager.read_last_good(
        provider_name="eia",
        indicator_code="crude_brent_usd",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2),
    )
    assert last_good is not None and len(last_good) == 2


def test_curated_adapters_produce_manual_points() -> None:
    adapters = [
        CuratedWholesaleAdapter(),
        HolidayFlagAdapter(),
        EventPressureAdapter(),
    ]
    for adapter in adapters:
        assert adapter.supports_live is False
        indicator_code = adapter.indicator_codes[0]
        points = adapter.fetch_manual_snapshot_range(
            indicator_code=indicator_code,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 3),
        )
        assert len(points) == 3
