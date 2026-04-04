from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.dependencies.analytics import get_analytics_service
from app.dependencies.auth import get_auth_service
from app.main import app
from app.services.analytics_service import (
    AnomaliesResult,
    MarginAnalyticsResult,
    SalesAnalyticsResult,
)
from app.services.auth_service import AuthenticatedUser


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
                    email="admin@fuelsight.local",
                    role="admin",
                    display_name="FuelSight Admin",
                    is_active=True,
                ),
                password="admin12345",
            ),
            FakeUserRecord(
                user=AuthenticatedUser(
                    id=uuid4(),
                    email="analyst@fuelsight.local",
                    role="analyst",
                    display_name="FuelSight Analyst",
                    is_active=True,
                ),
                password="analyst12345",
            ),
            FakeUserRecord(
                user=AuthenticatedUser(
                    id=uuid4(),
                    email="viewer@fuelsight.local",
                    role="viewer",
                    display_name="FuelSight Viewer",
                    is_active=True,
                ),
                password="viewer12345",
            ),
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


class FakeAnalyticsService:
    def get_sales(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
        granularity: str,
    ) -> SalesAnalyticsResult:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")
        return SalesAnalyticsResult(
            data={
                "product_code": product_code.upper(),
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 3, 1),
                        "volume_liters": 12000.0,
                        "avg_retail_price_rub": 59.8,
                    }
                ],
                "seasonality": {
                    "by_weekday": [{"weekday": "Mon", "avg_volume_liters": 11800.0}],
                    "by_month": [{"month": 3, "avg_volume_liters": 12150.0}],
                },
                "comparisons": {"mom_pct": 2.4, "yoy_pct": None},
            },
            meta={"points": 1},
        )

    def get_margin(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
        granularity: str,
    ) -> MarginAnalyticsResult:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")
        return MarginAnalyticsResult(
            data={
                "product_code": product_code.upper(),
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 3, 1),
                        "avg_purchase_price_rub": 52.1,
                        "avg_retail_price_rub": 58.7,
                        "gross_margin_rub": 4300.0,
                        "gross_margin_rub_per_liter": 4.3,
                        "gross_margin_pct": 7.3,
                        "purchase_data_missing": False,
                    }
                ],
                "threshold_rub_per_liter": 3.0,
                "below_threshold_days": 1,
                "low_margin_days": [
                    {
                        "date": date(2026, 3, 5),
                        "gross_margin_rub_per_liter": 2.1,
                        "purchase_data_missing": False,
                    }
                ],
            },
            meta={"points": 1},
        )

    def get_anomalies(
        self,
        *,
        metric: str,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
    ) -> AnomaliesResult:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")
        return AnomaliesResult(
            data=[
                {
                    "date": date(2026, 3, 10),
                    "product_code": product_code.upper(),
                    "metric": metric,
                    "severity": "high",
                    "actual_value": 1.34,
                    "expected_range": (3.4, 5.1),
                    "possible_reasons": ["Рост закупочной цены"],
                    "target_path": "/analytics/margin",
                }
            ],
            meta={"count": 1},
        )


def _setup_overrides(fake_auth: FakeAuthService, fake_analytics: FakeAnalyticsService) -> None:
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_analytics_service] = lambda: fake_analytics


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_analytics_service, None)


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_sales_analytics_is_available_for_admin() -> None:
    _setup_overrides(FakeAuthService(), FakeAnalyticsService())
    client = TestClient(app)
    token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.get(
        "/api/v1/analytics/sales?product_code=AI_95&granularity=week",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["granularity"] == "week"
    assert payload["data"]["series"][0]["period_start"] == "2026-03-01"


def test_margin_analytics_is_available_for_analyst() -> None:
    _setup_overrides(FakeAuthService(), FakeAnalyticsService())
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.get(
        "/api/v1/analytics/margin?product_code=DT_S&granularity=month",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["product_code"] == "DT_S"
    assert payload["data"]["below_threshold_days"] == 1


def test_anomalies_returns_list() -> None:
    _setup_overrides(FakeAuthService(), FakeAnalyticsService())
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.get(
        "/api/v1/analytics/anomalies?metric=sales&product_code=AI_92",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]
    assert payload["data"][0]["metric"] == "sales"


def test_invalid_date_range_returns_422() -> None:
    _setup_overrides(FakeAuthService(), FakeAnalyticsService())
    client = TestClient(app)
    token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.get(
        "/api/v1/analytics/sales?product_code=AI_95&date_from=2026-04-01&date_to=2026-03-01",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"


def test_forbidden_role_gets_403() -> None:
    _setup_overrides(FakeAuthService(), FakeAnalyticsService())
    client = TestClient(app)
    token = _login(client, "viewer@fuelsight.local", "viewer12345")

    response = client.get(
        "/api/v1/analytics/sales?product_code=AI_95",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()
    assert response.status_code == 403


def test_missing_token_gets_401() -> None:
    _setup_overrides(FakeAuthService(), FakeAnalyticsService())
    client = TestClient(app)

    response = client.get("/api/v1/analytics/sales?product_code=AI_95")

    _cleanup_overrides()
    assert response.status_code == 401
