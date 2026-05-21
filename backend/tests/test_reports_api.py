from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_auth_service
from app.dependencies.reports import get_executive_report_service
from app.main import app
from app.services.auth_service import AuthenticatedUser

DEMO_USERS = {
    "admin": ("admin@fuelsight.local", "admin12345", "FuelSight Admin"),
    "sales": ("sales@fuelsight.local", "sales12345", "FuelSight Sales"),
    "accounting": (
        "accounting@fuelsight.local",
        "accounting12345",
        "FuelSight Accounting",
    ),
    "analyst": ("analyst@fuelsight.local", "analyst12345", "FuelSight Analyst"),
    "director": ("director@fuelsight.local", "director12345", "FuelSight Director"),
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
                    email=email,
                    role=role,
                    display_name=display_name,
                    is_active=True,
                ),
                password=password,
            )
            for role, (email, password, display_name) in DEMO_USERS.items()
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


def _report_payload(*, warnings: list[str] | None = None) -> dict[str, object]:
    return {
        "report_id": "test-report",
        "generated_at": datetime.now(UTC).isoformat(),
        "period": {"date_from": date(2026, 3, 1), "date_to": date(2026, 3, 31)},
        "executive_summary": "Маржа и спрос стабильны.",
        "kpi": {
            "revenue_rub": 60000.0,
            "sales_volume_liters": 1000.0,
            "gross_margin_rub": 5000.0,
            "gross_margin_pct": 8.33,
        },
        "problem_products": [],
        "demand_forecast": [],
        "margin_risks": [],
        "market_context": [],
        "recommendations": ["Продолжить мониторинг маржи."],
        "data_quality": {
            "has_sales_data": True,
            "has_purchase_data": True,
            "has_forecast_data": False,
            "has_news_data": False,
            "warnings": warnings or [],
        },
    }


class FakeExecutiveReportService:
    def __init__(self, *, empty: bool = False) -> None:
        self.empty = empty

    def build_report(self, **_kwargs):  # noqa: ANN003, ANN201
        warnings = ["Нет данных продаж за выбранный период."] if self.empty else []
        payload = _report_payload(warnings=warnings)
        if self.empty:
            payload["executive_summary"] = "Данных недостаточно для управленческих выводов."
            payload["kpi"] = {
                "revenue_rub": 0.0,
                "sales_volume_liters": 0.0,
                "gross_margin_rub": 0.0,
                "gross_margin_pct": 0.0,
            }
            payload["data_quality"] = {
                "has_sales_data": False,
                "has_purchase_data": False,
                "has_forecast_data": False,
                "has_news_data": False,
                "warnings": warnings,
            }
        return SimpleNamespace(data=payload, meta={"source": "fake"})


def _setup_overrides(*, empty: bool = False) -> None:
    fake_auth = FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_executive_report_service] = lambda: FakeExecutiveReportService(
        empty=empty,
    )


def _cleanup_overrides() -> None:
    for dependency in (get_auth_service, get_executive_report_service):
        app.dependency_overrides.pop(dependency, None)


def _client(*, empty: bool = False) -> TestClient:
    _setup_overrides(empty=empty)
    return TestClient(app)


def _login(client: TestClient, role: str) -> str:
    email, password, _display_name = DEMO_USERS[role]
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def _headers(client: TestClient, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, role)}"}


@pytest.mark.parametrize("role", ["admin", "analyst", "director"])
def test_executive_report_allowed_roles(role: str) -> None:
    client = _client()
    response = client.post(
        "/api/v1/reports/executive",
        headers=_headers(client, role),
        json={"date_from": "2026-03-01", "date_to": "2026-03-31"},
    )
    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["period"] == {"date_from": "2026-03-01", "date_to": "2026-03-31"}


@pytest.mark.parametrize("role", ["sales", "accounting"])
def test_executive_report_rejects_non_executive_roles(role: str) -> None:
    client = _client()
    response = client.post("/api/v1/reports/executive", headers=_headers(client, role), json={})
    _cleanup_overrides()

    assert response.status_code == 403


def test_executive_report_contains_required_sections() -> None:
    client = _client()
    response = client.post(
        "/api/v1/reports/executive",
        headers=_headers(client, "director"),
        json={},
    )
    _cleanup_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    for key in (
        "executive_summary",
        "kpi",
        "problem_products",
        "demand_forecast",
        "margin_risks",
        "market_context",
        "recommendations",
        "data_quality",
    ):
        assert key in data


def test_executive_report_empty_dataset_returns_structured_warning() -> None:
    client = _client(empty=True)
    response = client.post(
        "/api/v1/reports/executive",
        headers=_headers(client, "director"),
        json={},
    )
    _cleanup_overrides()

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["kpi"]["revenue_rub"] == 0.0
    assert data["data_quality"]["has_sales_data"] is False
    assert data["data_quality"]["warnings"]
