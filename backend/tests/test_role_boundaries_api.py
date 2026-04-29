from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_auth_service
from app.dependencies.forecast import get_forecast_service
from app.dependencies.imports import get_import_service
from app.dependencies.kpi import get_kpi_service
from app.dependencies.news import get_news_service
from app.main import app
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
    def get_summary(self, *, date_from, date_to, product_code):  # noqa: ANN001
        return SimpleNamespace(
            data={
                "sales_volume_liters": 1000.0,
                "revenue_rub": 60000.0,
                "gross_margin_rub": 5000.0,
                "gross_margin_pct": 8.33,
                "low_margin_days": 0,
                "anomaly_count": 0,
            },
            meta={"product_code": product_code},
        )


class GuardedWriteService:
    def create_job(self, **_kwargs):  # noqa: ANN003, ANN201
        raise AssertionError("analyst must not reach import job creation")

    def refresh_news(self):  # noqa: ANN201
        raise AssertionError("analyst must not reach news refresh")

    def run_backtest(self, **_kwargs):  # noqa: ANN003, ANN201
        raise AssertionError("analyst must not reach backtest run")


def _setup_overrides() -> None:
    fake_auth = FakeAuthService()
    guarded = GuardedWriteService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_kpi_service] = lambda: FakeKpiService()
    app.dependency_overrides[get_import_service] = lambda: guarded
    app.dependency_overrides[get_news_service] = lambda: guarded
    app.dependency_overrides[get_forecast_service] = lambda: guarded


def _cleanup_overrides() -> None:
    for dependency in (
        get_auth_service,
        get_kpi_service,
        get_import_service,
        get_news_service,
        get_forecast_service,
    ):
        app.dependency_overrides.pop(dependency, None)


def _analyst_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@fuelsight.local", "password": "analyst12345"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_analyst_can_read_kpi_but_cannot_run_admin_operations() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _analyst_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    kpi_response = client.get("/api/v1/kpi/summary?product_code=AI_95", headers=headers)
    import_response = client.post(
        "/api/v1/import/generate-demo",
        headers=headers,
        json={
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "products": ["AI_95"],
            "seed": 42,
            "replace_existing": False,
        },
    )
    news_refresh_response = client.post("/api/v1/news/refresh", headers=headers)
    backtest_response = client.post(
        "/api/v1/backtests/run",
        headers=headers,
        json={"product_code": "AI_95", "horizon_days": 7, "window_type": "rolling"},
    )

    _cleanup_overrides()

    assert kpi_response.status_code == 200
    assert kpi_response.json()["data"]["gross_margin_pct"] == 8.33
    assert import_response.status_code == 403
    assert news_refresh_response.status_code == 403
    assert backtest_response.status_code == 403
