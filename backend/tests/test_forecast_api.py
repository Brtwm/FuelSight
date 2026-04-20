from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_auth_service
from app.dependencies.forecast import get_forecast_service
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


class FakeForecastService:
    def run_forecast(self, *, product_code: str, horizon_days: int, scenario: dict | None):
        if horizon_days not in {1, 7, 30}:
            raise ValueError("horizon_days must be one of 1, 7, 30")
        return type(
            "ForecastResult",
            (),
            {
                "data": {
                    "product_code": product_code.upper(),
                    "horizon_days": horizon_days,
                    "model_type": "catboost",
                    "model_status": "active",
                    "scenario_name": "base" if not scenario else "what_if_price",
                    "scenario_params": scenario,
                    "forecast_points": [
                        {
                            "target_date": "2026-04-10",
                            "y_hat": 12000.0,
                            "y_lo": 11500.0,
                            "y_hi": 12500.0,
                        }
                    ],
                    "drivers": ["Лаг 7 дней задаёт базовый тренд."],
                    "model_freshness": "fresh",
                    "training_window": {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31",
                    },
                    "baseline_comparison": {
                        "winner": {"smape": 4.4},
                        "seasonal_naive": {"smape": 5.8},
                        "delta_vs_baseline": {"smape": -1.4},
                    },
                    "feature_sources": ["lag_rolling", "external_indicators"],
                    "retrain_status": "ok",
                    "provider_mode": "cached",
                    "external_context_quality": {
                        "provider_mode": "cached",
                        "coverage_ratio": 0.96,
                        "fallback_ratio": 0.14,
                        "quality_status": "warning",
                        "reasons": ["fallback_ratio=0.140>0.10"],
                        "manifest_run_date": "2026-04-09",
                        "source_refs": [],
                    },
                    "event_context": [
                        {
                            "event_code": "summer_logistics_constraints",
                            "title": "Летние логистические ограничения",
                            "start_date": "2026-04-10",
                            "end_date": "2026-04-12",
                            "pressure_score": 0.35,
                            "demand_delta_pct": -1.2,
                            "purchase_delta_pct": 1.8,
                            "source_mode": "db",
                        }
                    ],
                    "reference_overlays": [
                        {
                            "code": "usd_rub",
                            "label": "USD/RUB",
                            "provider_mode": "cached",
                            "points": [{"date": "2026-04-10", "value": 90.3}],
                        }
                    ],
                },
                "meta": {
                    "points": 1,
                    "external_context": {
                        "provider_mode": "cached",
                        "coverage_ratio": 0.96,
                        "fallback_ratio": 0.14,
                        "quality_status": "warning",
                        "reasons": ["fallback_ratio=0.140>0.10"],
                        "manifest_run_date": "2026-04-09",
                        "source_refs": [],
                    },
                },
            },
        )()

    def get_latest_forecast(self, *, product_code: str, horizon_days: int):
        if product_code.upper() == "AI_92":
            return type(
                "LatestForecastResult",
                (),
                {"data": None, "meta": {"empty_state": "empty"}},
            )()
        return self.run_forecast(
            product_code=product_code,
            horizon_days=horizon_days,
            scenario=None,
        )

    def run_backtest(self, *, product_code: str, horizon_days: int, window_type: str):
        if horizon_days not in {1, 7, 30}:
            raise ValueError("horizon_days must be one of 1, 7, 30")
        return type(
            "BacktestResult",
            (),
            {
                "data": {
                    "product_code": product_code.upper(),
                    "horizon_days": horizon_days,
                    "model_type": "catboost",
                    "window_type": window_type,
                    "metrics": {"mae": 120.2, "rmse": 150.3, "smape": 4.4},
                    "comparison": {
                        "seasonal_naive": {"mae": 170.0, "rmse": 210.0, "smape": 5.8},
                        "catboost": {"mae": 120.2, "rmse": 150.3, "smape": 4.4},
                    },
                    "trained_at": datetime(2026, 4, 4, 20, 0, 0).isoformat(),
                    "model_version": "20260404200000",
                    "model_freshness": "fresh",
                    "training_window": {
                        "start_date": "2025-01-01",
                        "end_date": "2025-12-31",
                    },
                    "baseline_comparison": {
                        "winner": {"smape": 4.4},
                        "seasonal_naive": {"smape": 5.8},
                        "delta_vs_baseline": {"smape": -1.4},
                    },
                    "feature_sources": ["lag_rolling", "external_indicators"],
                    "retrain_status": "ok",
                    "provider_mode": "cached",
                },
                "meta": {"folds": 8},
            },
        )()

    def get_latest_backtest(self, *, product_code: str, horizon_days: int):
        if product_code.upper() == "DT_W":
            return type(
                "LatestBacktestResult",
                (),
                {"data": None, "meta": {"empty_state": "empty"}},
            )()
        return self.run_backtest(
            product_code=product_code,
            horizon_days=horizon_days,
            window_type="rolling",
        )


def _setup_overrides() -> None:
    fake_auth = FakeAuthService()
    fake_forecast = FakeForecastService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_forecast_service] = lambda: fake_forecast


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_forecast_service, None)


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_forecast_run_is_available_for_analyst() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.post(
        "/api/v1/forecasts/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "product_code": "AI_95",
            "horizon_days": 7,
            "scenario": {"retail_price_delta_pct": 2.5},
        },
    )

    _cleanup_overrides()
    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["horizon_days"] == 7
    assert payload["data"]["scenario_name"] == "what_if_price"
    assert payload["data"]["model_freshness"] == "fresh"
    assert payload["data"]["provider_mode"] == "cached"
    assert payload["data"]["external_context_quality"]["quality_status"] == "warning"
    assert payload["data"]["event_context"]
    assert payload["data"]["reference_overlays"]


def test_forecast_latest_returns_null_data_when_absent() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.get(
        "/api/v1/forecasts/latest?product_code=AI_92&horizon_days=7",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()
    assert response.status_code == 200
    assert response.json()["data"] is None


def test_backtest_run_is_admin_only() -> None:
    _setup_overrides()
    client = TestClient(app)
    analyst_token = _login(client, "analyst@fuelsight.local", "analyst12345")
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")

    analyst_response = client.post(
        "/api/v1/backtests/run",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"product_code": "AI_95", "horizon_days": 7, "window_type": "rolling"},
    )
    admin_response = client.post(
        "/api/v1/backtests/run",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"product_code": "AI_95", "horizon_days": 7, "window_type": "rolling"},
    )

    _cleanup_overrides()
    assert analyst_response.status_code == 403
    assert admin_response.status_code == 200


def test_backtest_latest_returns_null_data_when_absent() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.get(
        "/api/v1/backtests/latest?product_code=DT_W&horizon_days=30",
        headers={"Authorization": f"Bearer {token}"},
    )

    _cleanup_overrides()
    assert response.status_code == 200
    assert response.json()["data"] is None
