from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest

from app.services.analytics_service import AnalyticsService


def _build_service(*, threshold: float = 3.0) -> AnalyticsService:
    settings = SimpleNamespace(kpi_low_margin_threshold_rub_per_liter=threshold)
    return AnalyticsService(session=SimpleNamespace(), settings=settings)  # type: ignore[arg-type]


def test_sales_week_aggregation_and_comparisons(monkeypatch) -> None:
    service = _build_service()

    monkeypatch.setattr(service, "_assert_product_exists", lambda _: None)
    monkeypatch.setattr(
        service,
        "_query_sales_daily",
        lambda **_: [
            {"date": date(2026, 3, 2), "volume_liters": 100.0, "revenue_rub": 6000.0},
            {"date": date(2026, 3, 3), "volume_liters": 200.0, "revenue_rub": 12400.0},
        ],
    )

    def fake_total(*, date_range, product_code):  # noqa: ANN001
        assert product_code == "AI_95"
        key = (date_range.date_from, date_range.date_to)
        if key == (date(2026, 3, 2), date(2026, 3, 3)):
            return 300.0
        if key == (date(2026, 2, 28), date(2026, 3, 1)):
            return 200.0
        if key == (date(2025, 3, 2), date(2025, 3, 3)):
            return None
        return None

    monkeypatch.setattr(service, "_query_sales_total", fake_total)

    result = service.get_sales(
        date_from=date(2026, 3, 2),
        date_to=date(2026, 3, 3),
        product_code="ai_95",
        granularity="week",
    )

    assert result.data["product_code"] == "AI_95"
    assert result.data["granularity"] == "week"
    assert len(result.data["series"]) == 1
    assert result.data["series"][0]["period_start"] == date(2026, 3, 2)
    assert result.data["series"][0]["volume_liters"] == 300.0
    assert result.data["series"][0]["avg_retail_price_rub"] == 61.3333
    assert result.data["comparisons"]["mom_pct"] == 50.0
    assert result.data["comparisons"]["yoy_pct"] is None


def test_margin_keeps_missing_purchase_and_low_margin_days(monkeypatch) -> None:
    service = _build_service(threshold=6.0)

    monkeypatch.setattr(service, "_assert_product_exists", lambda _: None)
    monkeypatch.setattr(
        service,
        "_query_margin_daily",
        lambda **_: [
            {
                "date": date(2026, 3, 1),
                "volume_liters": 100.0,
                "revenue_rub": 6000.0,
                "purchase_volume_liters": 100.0,
                "avg_retail_price_rub": 60.0,
                "avg_purchase_price_rub": 55.0,
                "purchase_data_missing": False,
                "gross_margin_rub": 500.0,
                "gross_margin_rub_per_liter": 5.0,
                "gross_margin_pct": 8.3,
            },
            {
                "date": date(2026, 3, 2),
                "volume_liters": 120.0,
                "revenue_rub": 7200.0,
                "purchase_volume_liters": 0.0,
                "avg_retail_price_rub": 60.0,
                "avg_purchase_price_rub": None,
                "purchase_data_missing": True,
                "gross_margin_rub": None,
                "gross_margin_rub_per_liter": None,
                "gross_margin_pct": None,
            },
        ],
    )

    result = service.get_margin(
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 2),
        product_code="AI_95",
        granularity="day",
    )

    assert result.data["below_threshold_days"] == 1
    assert len(result.data["low_margin_days"]) == 1
    assert result.data["low_margin_days"][0]["date"] == date(2026, 3, 1)
    assert result.data["series"][0]["purchase_data_missing"] is False
    assert result.data["series"][1]["purchase_data_missing"] is True
    assert result.data["series"][1]["gross_margin_rub"] is None


def test_anomalies_sales_purchase_and_margin(monkeypatch) -> None:
    service = _build_service(threshold=3.0)
    monkeypatch.setattr(service, "_assert_product_exists", lambda _: None)

    monkeypatch.setattr(
        service,
        "_query_sales_daily",
        lambda **_: [
            {"date": date(2026, 3, 1), "volume_liters": 1000.0},
            {"date": date(2026, 3, 2), "volume_liters": 980.0},
            {"date": date(2026, 3, 3), "volume_liters": 995.0},
            {"date": date(2026, 3, 4), "volume_liters": 1010.0},
            {"date": date(2026, 3, 5), "volume_liters": 1005.0},
            {"date": date(2026, 3, 6), "volume_liters": 990.0},
            {"date": date(2026, 3, 7), "volume_liters": 1002.0},
            {"date": date(2026, 3, 8), "volume_liters": 1350.0},
        ],
    )
    monkeypatch.setattr(
        service,
        "_query_purchase_daily",
        lambda **_: [
            {"date": date(2026, 3, 1), "avg_purchase_price_rub": 50.0},
            {"date": date(2026, 3, 2), "avg_purchase_price_rub": 60.0},
        ],
    )
    monkeypatch.setattr(
        service,
        "_query_margin_daily",
        lambda **_: [
            {
                "date": date(2026, 3, 1),
                "avg_purchase_price_rub": 57.0,
                "avg_retail_price_rub": 58.0,
                "purchase_data_missing": False,
                "gross_margin_rub_per_liter": 1.0,
            }
        ],
    )

    sales = service.get_anomalies(
        metric="sales",
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 8),
        product_code="AI_92",
    )
    purchase = service.get_anomalies(
        metric="purchase_price",
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 2),
        product_code="AI_92",
    )
    margin = service.get_anomalies(
        metric="margin",
        date_from=date(2026, 3, 1),
        date_to=date(2026, 3, 2),
        product_code="AI_92",
    )

    assert sales.data
    assert sales.data[0]["metric"] == "sales"
    assert sales.data[0]["possible_reasons"]

    assert purchase.data
    assert purchase.data[0]["metric"] == "purchase_price"
    assert purchase.data[0]["target_path"] == "/analytics/margin"

    assert margin.data
    assert margin.data[0]["metric"] == "margin"
    assert margin.data[0]["expected_range"] == (3.0, 4.5)


def test_rejects_invalid_granularity(monkeypatch) -> None:
    service = _build_service()
    monkeypatch.setattr(service, "_assert_product_exists", lambda _: None)
    with pytest.raises(ValueError, match="granularity"):
        service.get_sales(
            date_from=date(2026, 3, 1),
            date_to=date(2026, 3, 2),
            product_code="AI_95",
            granularity="quarter",
        )
