from __future__ import annotations

from datetime import UTC, date, datetime
from types import SimpleNamespace
from typing import Any

from app.services.kpi_service import KpiService


class _FakeMappingsResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def mappings(self) -> "_FakeMappingsResult":
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows


class _RecordingSession:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def execute(self, statement, params=None):  # noqa: ANN001, ANN201
        self.queries.append(str(statement))
        return _FakeMappingsResult([])


def _build_service() -> KpiService:
    settings = SimpleNamespace(kpi_low_margin_threshold_rub_per_liter=3.0)
    return KpiService(session=SimpleNamespace(), settings=settings)  # type: ignore[arg-type]


def test_summary_respects_margin_coverage_for_partial_purchases(monkeypatch) -> None:
    service = _build_service()

    monkeypatch.setattr(
        service,
        "_query_sales_daily",
        lambda **_: [
            {
                "date": date(2026, 3, 1),
                "volume_liters": 1000.0,
                "revenue_rub": 58000.0,
                "avg_retail_price_rub": 58.0,
            },
            {
                "date": date(2026, 3, 2),
                "volume_liters": 900.0,
                "revenue_rub": 53100.0,
                "avg_retail_price_rub": 59.0,
            },
        ],
    )
    monkeypatch.setattr(
        service,
        "_query_margin_daily",
        lambda **_: [
            {
                "date": date(2026, 3, 1),
                "product_code": "AI_95",
                "volume_liters": 1000.0,
                "revenue_rub": 58000.0,
                "gross_margin_rub": 2000.0,
                "gross_margin_rub_per_liter": 2.0,
                "purchase_data_missing": False,
            },
            {
                "date": date(2026, 3, 2),
                "product_code": "AI_95",
                "volume_liters": 900.0,
                "revenue_rub": 53100.0,
                "gross_margin_rub": None,
                "gross_margin_rub_per_liter": None,
                "purchase_data_missing": True,
            },
        ],
    )
    monkeypatch.setattr(service, "_query_purchase_daily", lambda **_: [])
    monkeypatch.setattr(
        service,
        "_query_sales_by_product_daily",
        lambda **_: [
            {"date": date(2026, 3, 1), "product_code": "AI_95", "volume_liters": 1000.0},
            {"date": date(2026, 3, 2), "product_code": "AI_95", "volume_liters": 900.0},
        ],
    )

    result = service.get_summary(
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 2),
        product_code="AI_95",
    )

    assert result.data is not None
    assert result.data["gross_margin_rub"] == 2000.0
    assert result.data["low_margin_days"] == 1
    assert result.data["anomaly_count"] == 1
    assert result.meta["margin_coverage_days"] == 1
    assert result.meta["margin_missing_days"] == 1
    assert result.meta["data_freshness"] in {"fresh", "warning", "degraded"}
    assert result.meta["business_summary"]["title"]


def test_alerts_include_purchase_spike_and_demand_zscore(monkeypatch) -> None:
    service = _build_service()

    monkeypatch.setattr(service, "_query_margin_daily", lambda **_: [])
    monkeypatch.setattr(
        service,
        "_query_purchase_daily",
        lambda **_: [
            {
                "date": date(2026, 3, 1),
                "product_code": "AI_92",
                "avg_purchase_price_rub": 50.0,
            },
            {
                "date": date(2026, 3, 2),
                "product_code": "AI_92",
                "avg_purchase_price_rub": 60.0,
            },
        ],
    )
    monkeypatch.setattr(
        service,
        "_query_sales_by_product_daily",
        lambda **_: [
            {"date": date(2026, 3, 1), "product_code": "AI_92", "volume_liters": 1000.0},
            {"date": date(2026, 3, 2), "product_code": "AI_92", "volume_liters": 1010.0},
            {"date": date(2026, 3, 3), "product_code": "AI_92", "volume_liters": 995.0},
            {"date": date(2026, 3, 4), "product_code": "AI_92", "volume_liters": 1020.0},
            {"date": date(2026, 3, 5), "product_code": "AI_92", "volume_liters": 980.0},
            {"date": date(2026, 3, 6), "product_code": "AI_92", "volume_liters": 1005.0},
            {"date": date(2026, 3, 7), "product_code": "AI_92", "volume_liters": 990.0},
            {"date": date(2026, 3, 8), "product_code": "AI_92", "volume_liters": 1400.0},
        ],
    )

    result = service.get_alerts(
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 8),
        product_code="AI_92",
        severity=None,
    )

    alert_types = {item["type"] for item in result.data}
    assert "purchase_spike" in alert_types
    assert "demand_anomaly" in alert_types

    high_only = service.get_alerts(
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 8),
        product_code="AI_92",
        severity="high",
    )
    assert all(item["severity"] == "high" for item in high_only.data)


def test_snapshot_returns_points_in_query_order(monkeypatch) -> None:
    service = _build_service()

    monkeypatch.setattr(
        service,
        "_query_sales_daily",
        lambda **_: [
            {
                "date": date(2026, 3, 10),
                "volume_liters": 1000.1234,
                "revenue_rub": 60000.0,
                "avg_retail_price_rub": 59.99999,
            },
            {
                "date": date(2026, 3, 11),
                "volume_liters": 950.0,
                "revenue_rub": 57000.0,
                "avg_retail_price_rub": 60.0,
            },
        ],
    )

    result = service.get_snapshot(
        date_from=date(2026, 3, 10),
        date_to=date(2026, 3, 11),
        product_code="AI_95",
    )

    assert result.meta["points"] == 2
    assert result.data[0]["date"] == date(2026, 3, 10)
    assert result.data[0]["volume_liters"] == 1000.123
    assert result.data[0]["avg_retail_price_rub"] == 60.0
    assert isinstance(result.meta["chart_annotations"], list)
    assert isinstance(result.meta["reference_overlays"], list)
    assert result.meta["business_summary"]["title"]


def test_query_margin_daily_uses_margin_view() -> None:
    session = _RecordingSession()
    settings = SimpleNamespace(kpi_low_margin_threshold_rub_per_liter=3.0)
    service = KpiService(session=session, settings=settings)  # type: ignore[arg-type]

    service._query_margin_daily(
        date_range=service._resolve_date_range(
            date_from=date(2026, 3, 1),
            date_to=date(2026, 3, 31),
        ),
        product_code=None,
    )

    assert any("vw_margin_daily" in query for query in session.queries)


def test_summary_default_date_range_uses_last_30_days(monkeypatch) -> None:
    service = _build_service()
    captured = {}

    def fake_sales_daily(*, date_range, product_code):  # noqa: ANN001
        captured["date_from"] = date_range.date_from
        captured["date_to"] = date_range.date_to
        return []

    monkeypatch.setattr(service, "_query_sales_daily", fake_sales_daily)
    result = service.get_summary(date_from=None, date_to=None, product_code=None)

    assert result.data is None
    today = datetime.now(UTC).date()
    assert captured["date_to"] == today
    assert (captured["date_to"] - captured["date_from"]).days == 29
