from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_auth_service
from app.dependencies.kpi import get_kpi_service
from app.main import app
from app.services.auth_service import AuthenticatedUser
from app.services.kpi_service import AlertsResult, SnapshotResult, SummaryResult


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
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str | None,
    ) -> SummaryResult:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")

        if date_from == date(2026, 1, 1):
            return SummaryResult(
                data=None,
                meta={
                    "date_from": "2026-01-01",
                    "date_to": "2026-01-31",
                    "product_code": product_code,
                    "empty_state": "Нет данных",
                },
            )

        return SummaryResult(
            data={
                "sales_volume_liters": 12000.0,
                "revenue_rub": 780000.0,
                "gross_margin_rub": 54000.0,
                "gross_margin_pct": 6.92,
                "low_margin_days": 2,
                "anomaly_count": 3,
            },
            meta={
                "date_from": "2026-02-01",
                "date_to": "2026-03-01",
                "product_code": product_code,
                "margin_coverage_days": 20,
                "margin_missing_days": 3,
            },
        )

    def get_alerts(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str | None,
        severity: str | None,
    ) -> AlertsResult:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")

        alerts = [
            {
                "type": "low_margin",
                "severity": "high",
                "date": date(2026, 3, 20),
                "product_code": product_code or "AI_95",
                "message": "Маржа ниже порога",
                "metric": "margin",
                "actual_value": 2.2,
                "expected_range": (3.0, 4.5),
                "target_path": "/analytics/margin",
            },
            {
                "type": "demand_anomaly",
                "severity": "medium",
                "date": date(2026, 3, 21),
                "product_code": product_code or "AI_95",
                "message": "Спрос выше ожиданий",
                "metric": "sales",
                "actual_value": 15000.0,
                "expected_range": (9000.0, 12000.0),
                "target_path": "/analytics/sales",
            },
        ]
        if severity is not None:
            alerts = [item for item in alerts if item["severity"] == severity]

        return AlertsResult(
            data=alerts,
            meta={
                "date_from": "2026-03-01",
                "date_to": "2026-03-31",
                "product_code": product_code,
                "severity": severity,
                "count": len(alerts),
            },
        )

    def get_snapshot(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str | None,
    ) -> SnapshotResult:
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")

        return SnapshotResult(
            data=[
                {
                    "date": date(2026, 3, 28),
                    "volume_liters": 12450.0,
                    "avg_retail_price_rub": 59.8,
                },
                {
                    "date": date(2026, 3, 29),
                    "volume_liters": 12100.0,
                    "avg_retail_price_rub": 60.1,
                },
            ],
            meta={
                "date_from": "2026-03-01",
                "date_to": "2026-03-31",
                "product_code": product_code,
                "points": 2,
            },
        )


def _setup_overrides(fake_auth: FakeAuthService, fake_kpi: FakeKpiService) -> None:
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_kpi_service] = lambda: fake_kpi


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_kpi_service, None)


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_summary_returns_data_for_admin() -> None:
    fake_auth = FakeAuthService()
    fake_kpi = FakeKpiService()
    _setup_overrides(fake_auth, fake_kpi)
    client = TestClient(app)

    token = _login(client, "admin@fuelsight.local", "admin12345")
    response = client.get("/api/v1/kpi/summary", headers={"Authorization": f"Bearer {token}"})

    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["gross_margin_pct"] == 6.92
    assert payload["meta"]["margin_coverage_days"] == 20


def test_summary_empty_state_for_analyst() -> None:
    fake_auth = FakeAuthService()
    fake_kpi = FakeKpiService()
    _setup_overrides(fake_auth, fake_kpi)
    client = TestClient(app)

    token = _login(client, "analyst@fuelsight.local", "analyst12345")
    response = client.get(
        "/api/v1/kpi/summary?date_from=2026-01-01&date_to=2026-01-31",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None
    assert payload["meta"]["empty_state"]


def test_alerts_severity_filter_works() -> None:
    fake_auth = FakeAuthService()
    fake_kpi = FakeKpiService()
    _setup_overrides(fake_auth, fake_kpi)
    client = TestClient(app)

    token = _login(client, "analyst@fuelsight.local", "analyst12345")
    response = client.get(
        "/api/v1/kpi/alerts?severity=high",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["data"]) == 1
    assert payload["data"][0]["severity"] == "high"


def test_snapshot_returns_points() -> None:
    fake_auth = FakeAuthService()
    fake_kpi = FakeKpiService()
    _setup_overrides(fake_auth, fake_kpi)
    client = TestClient(app)

    token = _login(client, "admin@fuelsight.local", "admin12345")
    response = client.get("/api/v1/kpi/snapshot", headers={"Authorization": f"Bearer {token}"})

    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["meta"]["points"] == 2
    assert payload["data"][0]["date"] == "2026-03-28"


def test_invalid_date_range_returns_422() -> None:
    fake_auth = FakeAuthService()
    fake_kpi = FakeKpiService()
    _setup_overrides(fake_auth, fake_kpi)
    client = TestClient(app)

    token = _login(client, "admin@fuelsight.local", "admin12345")
    response = client.get(
        "/api/v1/kpi/summary?date_from=2026-04-01&date_to=2026-03-01",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
