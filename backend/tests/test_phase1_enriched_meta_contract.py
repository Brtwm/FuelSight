from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.dependencies.analytics import get_analytics_service
from app.dependencies.auth import get_auth_service
from app.dependencies.forecast import get_forecast_service
from app.dependencies.kpi import get_kpi_service
from app.dependencies.news import get_news_service
from app.main import app
from app.services.analytics_service import (
    MarginAnalyticsResult,
    SalesAnalyticsResult,
)
from app.services.auth_service import AuthenticatedUser
from app.services.forecast_service import LatestForecastResult
from app.services.kpi_service import SnapshotResult, SummaryResult

_SHARED_META_KEYS = {
    "business_summary",
    "chart_annotations",
    "reference_overlays",
    "supporting_refs",
    "data_freshness",
    "model_freshness",
    "news_freshness",
    "external_indicators_mode",
    "provider_mode",
    "llm_mode",
}


@dataclass(frozen=True)
class FakeUserRecord:
    user: AuthenticatedUser
    password: str


class FakeAuthService:
    def __init__(self) -> None:
        self._records = [
            FakeUserRecord(
                user=AuthenticatedUser(
                    id=uuid4(),
                    email="analyst@fuelsight.local",
                    role="analyst",
                    display_name="FuelSight Analyst",
                    is_active=True,
                ),
                password="analyst12345",
            )
        ]

    def authenticate(self, email: str, password: str) -> AuthenticatedUser | None:
        for record in self._records:
            if record.user.email == email and record.password == password:
                return record.user
        return None

    def get_user_by_id(self, user_id: UUID) -> AuthenticatedUser | None:
        for record in self._records:
            if record.user.id == user_id:
                return record.user
        return None


class FakeKpiService:
    def get_summary(
        self, *, date_from: date | None, date_to: date | None, product_code: str | None
    ) -> SummaryResult:
        return SummaryResult(
            data={
                "sales_volume_liters": 1000.0,
                "revenue_rub": 60000.0,
                "gross_margin_rub": 5200.0,
                "gross_margin_pct": 8.6,
                "low_margin_days": 1,
                "anomaly_count": 2,
            },
            meta={"margin_coverage_days": 20, "margin_missing_days": 2},
        )

    def get_alerts(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str | None,
        severity: str | None,
    ):
        return type("AlertsResult", (), {"data": [], "meta": {"count": 0}})()

    def get_snapshot(
        self, *, date_from: date | None, date_to: date | None, product_code: str | None
    ) -> SnapshotResult:
        return SnapshotResult(
            data=[
                {
                    "date": date(2026, 4, 7),
                    "volume_liters": 1000.0,
                    "avg_retail_price_rub": 60.0,
                }
            ],
            meta={"points": 1},
        )


class FakeAnalyticsService:
    def get_sales(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
        granularity: str,
    ) -> SalesAnalyticsResult:
        return SalesAnalyticsResult(
            data={
                "product_code": product_code,
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 4, 7),
                        "volume_liters": 1000.0,
                        "avg_retail_price_rub": 60.0,
                    }
                ],
                "seasonality": {"by_weekday": [], "by_month": []},
                "comparisons": {"mom_pct": None, "yoy_pct": None},
            },
            meta={"data_mode": "cached", "provider_mode": "cached"},
        )

    def get_margin(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
        granularity: str,
    ) -> MarginAnalyticsResult:
        return MarginAnalyticsResult(
            data={
                "product_code": product_code,
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 4, 7),
                        "avg_purchase_price_rub": 50.0,
                        "avg_retail_price_rub": 60.0,
                        "gross_margin_rub": 1000.0,
                        "gross_margin_rub_per_liter": 4.0,
                        "gross_margin_pct": 6.5,
                        "purchase_data_missing": False,
                    }
                ],
                "threshold_rub_per_liter": 3.0,
                "below_threshold_days": 0,
                "low_margin_days": [],
            },
            meta={"threshold_info": "Порог 3.0 руб/л"},
        )

    def get_anomalies(
        self,
        *,
        metric: str,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
    ):
        return type("AnomaliesResult", (), {"data": [], "meta": {"count": 0}})()


class FakeForecastService:
    def get_latest_forecast(
        self, *, product_code: str, horizon_days: int
    ) -> LatestForecastResult:
        return LatestForecastResult(
            data={
                "product_code": product_code,
                "horizon_days": horizon_days,
                "model_type": "catboost",
                "model_status": "active",
                "scenario_name": "base",
                "scenario_params": None,
                "forecast_points": [
                    {
                        "target_date": date(2026, 4, 8),
                        "y_hat": 1000.0,
                        "y_lo": 900.0,
                        "y_hi": 1100.0,
                    }
                ],
                "drivers": ["trend"],
            },
            meta={"points": 1},
        )

    def run_forecast(self, *, product_code: str, horizon_days: int, scenario: dict | None):
        raise NotImplementedError

    def run_backtest(self, *, product_code: str, horizon_days: int, window_type: str):
        raise NotImplementedError

    def get_latest_backtest(self, *, product_code: str, horizon_days: int):
        raise NotImplementedError


class FakeNewsService:
    def get_latest_digest(self, *, period_type: str):
        return {
            "digest_date": date(2026, 4, 7),
            "period_type": period_type,
            "summary_text": "summary",
            "bullet_points": ["a"],
            "source_ids": ["news_1"],
            "llm_mode": "off",
            "provider_mode": "cached",
            "news_freshness": "warning",
        }

    def search_news(self, *, q, date_from, date_to, topic, limit):
        return []

    def refresh_news(self):
        return type("RefreshResult", (), {"status": "ok", "imported_news_count": 0, "created_digests": 0})()


def _setup_overrides() -> None:
    auth_service = FakeAuthService()
    kpi_service = FakeKpiService()
    analytics_service = FakeAnalyticsService()
    forecast_service = FakeForecastService()
    news_service = FakeNewsService()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    app.dependency_overrides[get_kpi_service] = lambda: kpi_service
    app.dependency_overrides[get_analytics_service] = lambda: analytics_service
    app.dependency_overrides[get_forecast_service] = lambda: forecast_service
    app.dependency_overrides[get_news_service] = lambda: news_service


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_kpi_service, None)
    app.dependency_overrides.pop(get_analytics_service, None)
    app.dependency_overrides.pop(get_forecast_service, None)
    app.dependency_overrides.pop(get_news_service, None)


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@fuelsight.local", "password": "analyst12345"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_phase1_enriched_meta_shape_is_consistent_across_domains() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    responses = [
        client.get("/api/v1/kpi/summary", headers=headers),
        client.get("/api/v1/kpi/snapshot", headers=headers),
        client.get("/api/v1/analytics/sales?product_code=AI_95", headers=headers),
        client.get("/api/v1/analytics/margin?product_code=AI_95", headers=headers),
        client.get("/api/v1/forecasts/latest?product_code=AI_95&horizon_days=7", headers=headers),
        client.get("/api/v1/news/digests/latest?period_type=daily", headers=headers),
    ]

    _cleanup_overrides()

    for response in responses:
        assert response.status_code == 200
        payload = response.json()
        meta = payload["meta"]
        assert _SHARED_META_KEYS.issubset(meta.keys())
        assert isinstance(meta["chart_annotations"], list)
        assert isinstance(meta["reference_overlays"], list)
        assert isinstance(meta["supporting_refs"], list)
        assert meta["business_summary"] is None or isinstance(meta["business_summary"], dict)


def test_phase1_meta_keeps_existing_domain_fields() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    kpi_summary = client.get("/api/v1/kpi/summary", headers=headers).json()
    analytics_sales = client.get(
        "/api/v1/analytics/sales?product_code=AI_95", headers=headers
    ).json()
    news_digest = client.get(
        "/api/v1/news/digests/latest?period_type=daily", headers=headers
    ).json()

    _cleanup_overrides()

    assert kpi_summary["meta"]["margin_coverage_days"] == 20
    assert kpi_summary["meta"]["margin_missing_days"] == 2
    assert analytics_sales["meta"]["data_mode"] == "cached"
    assert news_digest["meta"]["provider_mode"] == "cached"
