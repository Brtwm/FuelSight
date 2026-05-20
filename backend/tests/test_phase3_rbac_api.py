from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.dependencies.analytics import get_analytics_service
from app.dependencies.auth import get_auth_service
from app.dependencies.chat import get_chat_service
from app.dependencies.forecast import get_forecast_service
from app.dependencies.kpi import get_kpi_service
from app.dependencies.news import get_news_service
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


class FakeKpiService:
    def get_summary(self, **_kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(
            data={
                "sales_volume_liters": 1000.0,
                "revenue_rub": 60000.0,
                "gross_margin_rub": 5000.0,
                "gross_margin_pct": 8.33,
                "low_margin_days": 0,
                "anomaly_count": 0,
            },
            meta={},
        )

    def get_alerts(self, **_kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(data=[], meta={})

    def get_snapshot(self, **_kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(
            data=[
                {
                    "date": date(2026, 3, 1),
                    "volume_liters": 1000.0,
                    "avg_retail_price_rub": 60.0,
                }
            ],
            meta={},
        )


class FakeAnalyticsService:
    def get_sales(self, **kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(
            data={
                "product_code": kwargs["product_code"],
                "granularity": kwargs["granularity"],
                "series": [],
                "seasonality": {"by_weekday": [], "by_month": []},
                "comparisons": {"mom_pct": None, "yoy_pct": None},
            },
            meta={},
        )

    def get_margin(self, **kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(
            data={
                "product_code": kwargs["product_code"],
                "granularity": kwargs["granularity"],
                "series": [],
                "threshold_rub_per_liter": 3.0,
                "below_threshold_days": 0,
                "low_margin_days": [],
            },
            meta={},
        )

    def get_anomalies(self, **kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(
            data=[
                {
                    "date": date(2026, 3, 1),
                    "product_code": kwargs["product_code"],
                    "metric": kwargs["metric"],
                    "severity": "medium",
                    "actual_value": 1.0,
                    "expected_range": (2.0, 3.0),
                    "possible_reasons": [],
                    "target_path": "/analytics/margin",
                }
            ],
            meta={},
        )


class FakeForecastService:
    def run_forecast(self, **kwargs):  # noqa: ANN003, ANN201
        return self.get_latest_forecast(**kwargs)

    def get_latest_forecast(self, **kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(
            data={
                "product_code": kwargs["product_code"],
                "horizon_days": kwargs["horizon_days"],
                "model_type": "seasonal_naive",
                "model_status": "baseline_fallback",
                "scenario_name": "base",
                "scenario_params": None,
                "forecast_points": [
                    {
                        "target_date": date(2026, 3, 2),
                        "y_hat": 1000.0,
                        "y_lo": 900.0,
                        "y_hi": 1100.0,
                    }
                ],
                "drivers": [],
            },
            meta={},
        )

    def get_latest_backtest(self, **kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(
            data={
                "product_code": kwargs["product_code"],
                "horizon_days": kwargs["horizon_days"],
                "model_type": "seasonal_naive",
                "window_type": "rolling",
                "metrics": {"mae": 1.0, "rmse": 1.0, "smape": 1.0},
                "comparison": {"seasonal_naive": {"mae": 1.0, "rmse": 1.0, "smape": 1.0}},
                "trained_at": datetime.now(UTC),
            },
            meta={},
        )

    def run_backtest(self, **_kwargs):  # noqa: ANN003, ANN201
        raise AssertionError("forbidden roles must not reach backtest run")


class FakeNewsService:
    def get_latest_digest(self, *, period_type):  # noqa: ANN001, ANN201
        return {
            "digest_date": date(2026, 3, 1),
            "created_at": datetime.now(UTC),
            "period_type": period_type,
            "summary_text": "ok",
            "bullet_points": [],
            "source_ids": [],
            "llm_mode": "retrieval_only",
        }

    def search_news(self, **_kwargs):  # noqa: ANN003, ANN201
        return []

    def refresh_news(self):  # noqa: ANN201
        return SimpleNamespace(
            status="ok",
            imported_news_count=0,
            created_digests=0,
            provider_mode=None,
            news_freshness=None,
            quality_status=None,
            provider_mode_counts={},
            written_news_count=0,
            coverage_ratio=None,
            cache_dir=None,
            last_success_at=None,
        )


class FakeChatService:
    def create_session(self, *, user_id, title):  # noqa: ANN001, ANN201
        now = datetime.now(UTC)
        return SimpleNamespace(id=uuid4(), title=title, created_at=now, updated_at=now)


def _setup_overrides() -> None:
    fake_auth = FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_kpi_service] = lambda: FakeKpiService()
    app.dependency_overrides[get_analytics_service] = lambda: FakeAnalyticsService()
    app.dependency_overrides[get_forecast_service] = lambda: FakeForecastService()
    app.dependency_overrides[get_news_service] = lambda: FakeNewsService()
    app.dependency_overrides[get_chat_service] = lambda: FakeChatService()


def _cleanup_overrides() -> None:
    for dependency in (
        get_auth_service,
        get_kpi_service,
        get_analytics_service,
        get_forecast_service,
        get_news_service,
        get_chat_service,
    ):
        app.dependency_overrides.pop(dependency, None)


def _client() -> TestClient:
    _setup_overrides()
    return TestClient(app)


def _login(client: TestClient, role: str) -> str:
    email, password, _display_name = DEMO_USERS[role]
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def _headers(client: TestClient, role: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, role)}"}


@pytest.mark.parametrize("role", DEMO_USERS)
def test_auth_me_all_roles(role: str) -> None:
    client = _client()
    response = client.get("/api/v1/auth/me", headers=_headers(client, role))
    _cleanup_overrides()

    assert response.status_code == 200
    assert response.json()["data"]["role"] == role


@pytest.mark.parametrize("role", DEMO_USERS)
@pytest.mark.parametrize("path", ["/summary", "/alerts", "/snapshot"])
def test_kpi_read_roles(role: str, path: str) -> None:
    client = _client()
    response = client.get(f"/api/v1/kpi{path}?product_code=AI_95", headers=_headers(client, role))
    _cleanup_overrides()

    assert response.status_code == 200


@pytest.mark.parametrize("role", ["admin", "sales", "analyst"])
def test_sales_analytics_allowed_roles(role: str) -> None:
    client = _client()
    response = client.get(
        "/api/v1/analytics/sales?product_code=AI_95",
        headers=_headers(client, role),
    )
    _cleanup_overrides()

    assert response.status_code == 200


@pytest.mark.parametrize("role", ["accounting", "director"])
def test_sales_analytics_rejects_non_sales_roles(role: str) -> None:
    client = _client()
    response = client.get(
        "/api/v1/analytics/sales?product_code=AI_95",
        headers=_headers(client, role),
    )
    _cleanup_overrides()

    assert response.status_code == 403


@pytest.mark.parametrize("role", ["admin", "accounting", "analyst", "director"])
def test_margin_analytics_allowed_roles(role: str) -> None:
    client = _client()
    response = client.get(
        "/api/v1/analytics/margin?product_code=AI_95",
        headers=_headers(client, role),
    )
    _cleanup_overrides()

    assert response.status_code == 200


def test_anomalies_metric_based_roles() -> None:
    client = _client()

    sales_on_sales = client.get(
        "/api/v1/analytics/anomalies?metric=sales&product_code=AI_95",
        headers=_headers(client, "sales"),
    )
    sales_on_margin = client.get(
        "/api/v1/analytics/anomalies?metric=margin&product_code=AI_95",
        headers=_headers(client, "sales"),
    )
    director_on_sales = client.get(
        "/api/v1/analytics/anomalies?metric=sales&product_code=AI_95",
        headers=_headers(client, "director"),
    )
    director_on_purchase = client.get(
        "/api/v1/analytics/anomalies?metric=purchase_price&product_code=AI_95",
        headers=_headers(client, "director"),
    )
    _cleanup_overrides()

    assert sales_on_sales.status_code == 200
    assert sales_on_margin.status_code == 403
    assert director_on_sales.status_code == 403
    assert director_on_purchase.status_code == 200


@pytest.mark.parametrize("role", ["admin", "sales", "analyst", "director"])
def test_forecast_and_backtest_read_roles(role: str) -> None:
    client = _client()
    headers = _headers(client, role)

    forecast_response = client.get(
        "/api/v1/forecasts/latest?product_code=AI_95&horizon_days=7",
        headers=headers,
    )
    backtest_response = client.get(
        "/api/v1/backtests/latest?product_code=AI_95&horizon_days=7",
        headers=headers,
    )
    _cleanup_overrides()

    assert forecast_response.status_code == 200
    assert backtest_response.status_code == 200


@pytest.mark.parametrize("role", ["sales", "accounting", "analyst", "director"])
def test_generate_demo_admin_only(role: str) -> None:
    client = _client()
    response = client.post(
        "/api/v1/import/generate-demo",
        headers=_headers(client, role),
        json={
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
            "products": ["AI_95"],
            "seed": 42,
            "replace_existing": False,
        },
    )
    _cleanup_overrides()

    assert response.status_code == 403


@pytest.mark.parametrize("role", ["sales", "accounting", "analyst", "director"])
def test_news_refresh_admin_only(role: str) -> None:
    client = _client()
    response = client.post("/api/v1/news/refresh", headers=_headers(client, role))
    _cleanup_overrides()

    assert response.status_code == 403


@pytest.mark.parametrize("role", ["admin", "analyst"])
def test_chat_analyst_admin_only_allows_chat_roles(role: str) -> None:
    client = _client()
    response = client.post(
        "/api/v1/chat/sessions",
        headers=_headers(client, role),
        json={"title": "RBAC smoke"},
    )
    _cleanup_overrides()

    assert response.status_code == 200


@pytest.mark.parametrize("role", ["sales", "accounting", "director"])
def test_chat_analyst_admin_only_rejects_business_roles(role: str) -> None:
    client = _client()
    response = client.post(
        "/api/v1/chat/sessions",
        headers=_headers(client, role),
        json={"title": "RBAC smoke"},
    )
    _cleanup_overrides()

    assert response.status_code == 403


def test_director_can_read_executive_data() -> None:
    client = _client()
    headers = _headers(client, "director")

    kpi_response = client.get("/api/v1/kpi/summary?product_code=AI_95", headers=headers)
    margin_response = client.get("/api/v1/analytics/margin?product_code=AI_95", headers=headers)
    forecast_response = client.get(
        "/api/v1/forecasts/latest?product_code=AI_95&horizon_days=7",
        headers=headers,
    )
    news_response = client.get("/api/v1/news/digests/latest?period_type=daily", headers=headers)
    import_response = client.get("/api/v1/import/jobs", headers=headers)
    _cleanup_overrides()

    assert kpi_response.status_code == 200
    assert margin_response.status_code == 200
    assert forecast_response.status_code == 200
    assert news_response.status_code == 200
    assert import_response.status_code == 403
