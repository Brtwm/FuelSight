from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.api.v1 import imports as imports_api
from app.dependencies.analytics import get_analytics_service
from app.dependencies.auth import get_auth_service
from app.dependencies.forecast import get_forecast_service
from app.dependencies.imports import get_import_service
from app.dependencies.kpi import get_kpi_service
from app.main import app
from app.services.auth_service import AuthenticatedUser


@dataclass(frozen=True)
class FakeUserRecord:
    user: AuthenticatedUser
    password: str


@dataclass
class FakeImportJob:
    id: UUID
    entity_type: str
    source_type: str
    file_name: str | None
    status: str
    rows_total: int
    rows_success: int
    rows_failed: int
    error_report_path: str | None
    started_by: UUID
    started_at: datetime
    finished_at: datetime | None


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


class FakeImportService:
    def __init__(self) -> None:
        self._jobs: dict[UUID, FakeImportJob] = {}

    def create_job(
        self,
        *,
        entity_type: str,
        source_type: str,
        file_name: str | None,
        started_by: UUID,
    ) -> FakeImportJob:
        job = FakeImportJob(
            id=uuid4(),
            entity_type=entity_type,
            source_type=source_type,
            file_name=file_name,
            status="queued",
            rows_total=0,
            rows_success=0,
            rows_failed=0,
            error_report_path=None,
            started_by=started_by,
            started_at=datetime.now(UTC),
            finished_at=None,
        )
        self._jobs[job.id] = job
        return job


class FakeKpiService:
    def get_summary(self, *, date_from, date_to, product_code):
        return SimpleNamespace(
            data={
                "sales_volume_liters": 155240.0,
                "revenue_rub": 9050040.0,
                "gross_margin_rub": 944004.0,
                "gross_margin_pct": 10.43,
                "low_margin_days": 2,
                "anomaly_count": 1,
            },
            meta={
                "date_from": "2026-03-01",
                "date_to": "2026-03-31",
                "product_code": product_code,
            },
        )


class FakeAnalyticsService:
    def get_sales(self, *, date_from, date_to, product_code, granularity):
        return SimpleNamespace(
            data={
                "product_code": product_code,
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 3, 1),
                        "volume_liters": 10200.0,
                        "avg_retail_price_rub": 59.8,
                    },
                    {
                        "period_start": date(2026, 3, 2),
                        "volume_liters": 10400.0,
                        "avg_retail_price_rub": 60.0,
                    },
                ],
                "seasonality": {
                    "by_weekday": [{"weekday": "Mon", "avg_volume_liters": 10120.0}],
                    "by_month": [{"month": 3, "avg_volume_liters": 10300.0}],
                },
                "comparisons": {"mom_pct": 2.4, "yoy_pct": None},
            },
            meta={"points": 2},
        )

    def get_margin(self, *, date_from, date_to, product_code, granularity):
        return SimpleNamespace(
            data={
                "product_code": product_code,
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 3, 1),
                        "avg_purchase_price_rub": 55.0,
                        "avg_retail_price_rub": 59.8,
                        "gross_margin_rub": 48960.0,
                        "gross_margin_rub_per_liter": 4.8,
                        "gross_margin_pct": 8.0,
                        "purchase_data_missing": False,
                    }
                ],
                "threshold_rub_per_liter": 3.0,
                "below_threshold_days": 0,
                "low_margin_days": [],
            },
            meta={"points": 1},
        )


class FakeForecastService:
    def run_forecast(self, *, product_code: str, horizon_days: int, scenario: dict | None):
        return SimpleNamespace(
            data={
                "product_code": product_code,
                "horizon_days": horizon_days,
                "model_type": "catboost",
                "model_status": "active",
                "scenario_name": "base" if scenario is None else "what_if_price",
                "scenario_params": scenario,
                "forecast_points": [
                    {
                        "target_date": date(2026, 4, 1),
                        "y_hat": 12100.0,
                        "y_lo": 11650.0,
                        "y_hi": 12560.0,
                    }
                ],
                "drivers": ["Лаг 7 дней задаёт базовый тренд."],
            },
            meta={"points": 1},
        )

    def get_latest_backtest(self, *, product_code: str, horizon_days: int):
        return SimpleNamespace(
            data={
                "product_code": product_code,
                "horizon_days": horizon_days,
                "model_type": "catboost",
                "window_type": "rolling",
                "metrics": {"mae": 410.2, "rmse": 552.1, "smape": 4.8},
                "comparison": {
                    "seasonal_naive": {"mae": 520.0, "rmse": 690.0, "smape": 5.6},
                    "catboost": {"mae": 410.2, "rmse": 552.1, "smape": 4.8},
                },
                "trained_at": datetime(2026, 4, 5, 20, 0, tzinfo=UTC),
                "model_version": "20260405200000",
            },
            meta={"folds": 8},
        )


def _setup_overrides(monkeypatch) -> None:
    fake_auth = FakeAuthService()
    fake_import = FakeImportService()
    fake_kpi = FakeKpiService()
    fake_analytics = FakeAnalyticsService()
    fake_forecast = FakeForecastService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_import_service] = lambda: fake_import
    app.dependency_overrides[get_kpi_service] = lambda: fake_kpi
    app.dependency_overrides[get_analytics_service] = lambda: fake_analytics
    app.dependency_overrides[get_forecast_service] = lambda: fake_forecast
    monkeypatch.setattr(imports_api, "_process_generate_demo_job_in_background", lambda **_: None)


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_import_service, None)
    app.dependency_overrides.pop(get_kpi_service, None)
    app.dependency_overrides.pop(get_analytics_service, None)
    app.dependency_overrides.pop(get_forecast_service, None)


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@fuelsight.local", "password": "admin12345"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_phase9_core_mvp_api_flow(monkeypatch) -> None:
    _setup_overrides(monkeypatch)
    client = TestClient(app)
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    generate_demo_response = client.post(
        "/api/v1/import/generate-demo",
        headers=headers,
        json={
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "products": ["AI_92", "AI_95", "DT_S", "DT_W"],
            "seed": 42,
            "replace_existing": True,
        },
    )
    kpi_response = client.get("/api/v1/kpi/summary?product_code=AI_95", headers=headers)
    sales_response = client.get(
        "/api/v1/analytics/sales?product_code=AI_95&granularity=day",
        headers=headers,
    )
    margin_response = client.get(
        "/api/v1/analytics/margin?product_code=AI_95&granularity=day",
        headers=headers,
    )
    forecast_response = client.post(
        "/api/v1/forecasts/run",
        headers=headers,
        json={
            "product_code": "AI_95",
            "horizon_days": 7,
            "scenario": {"retail_price_delta_pct": 2.5},
        },
    )
    backtest_response = client.get(
        "/api/v1/backtests/latest?product_code=AI_95&horizon_days=7",
        headers=headers,
    )
    _cleanup_overrides()

    assert generate_demo_response.status_code == 202
    assert kpi_response.status_code == 200
    assert sales_response.status_code == 200
    assert margin_response.status_code == 200
    assert forecast_response.status_code == 200
    assert backtest_response.status_code == 200

    assert generate_demo_response.json()["error"] is None
    assert kpi_response.json()["data"]["gross_margin_pct"] == 10.43
    assert sales_response.json()["data"]["product_code"] == "AI_95"
    assert margin_response.json()["data"]["threshold_rub_per_liter"] == 3.0
    assert forecast_response.json()["data"]["scenario_name"] == "what_if_price"
    assert backtest_response.json()["data"]["metrics"]["smape"] == 4.8
