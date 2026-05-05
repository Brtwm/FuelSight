from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.dependencies.analytics import get_analytics_service
from app.dependencies.auth import get_auth_service
from app.dependencies.chat import get_chat_service
from app.dependencies.forecast import get_forecast_service
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


EXTERNAL_CONTEXT = {
    "provider_mode": "cached",
    "coverage_ratio": 0.96,
    "fallback_ratio": 0.08,
    "quality_status": "warning",
    "reasons": ["fallback_ratio=0.08"],
    "manifest_run_date": "2026-05-05",
    "source_refs": [
        {
            "type": "indicator",
            "ref_id": "external_indicators:usd_rub",
            "title": "USD/RUB",
            "provider_mode": "cached",
            "confidence": 0.9,
            "source_type": "external_indicator",
        }
    ],
}


COMMON_META = {
    "business_summary": {
        "title": "Краткий вывод",
        "summary": "Данные доступны с контролируемой деградацией.",
        "bullets": ["Источник работает через cache"],
    },
    "chart_annotations": [
        {"id": "annotation-1", "date": "2026-05-05", "label": "Контрольная точка"}
    ],
    "reference_overlays": [
        {
            "code": "usd_rub",
            "label": "USD/RUB",
            "provider_mode": "cached",
            "points": [{"date": "2026-05-05", "value": 91.2}],
        }
    ],
    "supporting_refs": [
        {
            "type": "chart",
            "ref_id": "analytics_margin_AI_95",
            "title": "Маржа AI-95",
            "provider_mode": "cached",
            "confidence": 0.84,
            "source_type": "analytics",
        }
    ],
    "data_freshness": "warning",
    "provider_mode": "cached",
    "external_indicators_mode": "cached",
    "external_context": EXTERNAL_CONTEXT,
}


class FakeKpiService:
    def get_summary(self, *, date_from, date_to, product_code):  # noqa: ANN001
        return SimpleNamespace(
            data={
                "sales_volume_liters": 1000.0,
                "revenue_rub": 62000.0,
                "gross_margin_rub": 5200.0,
                "gross_margin_pct": 8.4,
                "low_margin_days": 1,
                "anomaly_count": 2,
            },
            meta={**COMMON_META, "margin_coverage_days": 20, "margin_missing_days": 1},
        )

    def get_alerts(self, **_kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(data=[], meta={"count": 0})

    def get_snapshot(self, *, date_from, date_to, product_code):  # noqa: ANN001
        return SimpleNamespace(
            data=[
                {
                    "date": date(2026, 5, 5),
                    "volume_liters": 1000.0,
                    "avg_retail_price_rub": 62.0,
                }
            ],
            meta={**COMMON_META, "points": 1},
        )


class FakeAnalyticsService:
    def get_sales(self, *, date_from, date_to, product_code, granularity):  # noqa: ANN001
        return SimpleNamespace(
            data={
                "product_code": product_code,
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 5, 5),
                        "volume_liters": 1000.0,
                        "avg_retail_price_rub": 62.0,
                    }
                ],
                "seasonality": {"by_weekday": [], "by_month": []},
                "comparisons": {"mom_pct": None, "yoy_pct": None},
            },
            meta={**COMMON_META, "data_mode": "cached"},
        )

    def get_margin(self, *, date_from, date_to, product_code, granularity):  # noqa: ANN001
        return SimpleNamespace(
            data={
                "product_code": product_code,
                "granularity": granularity,
                "series": [
                    {
                        "period_start": date(2026, 5, 5),
                        "avg_purchase_price_rub": 55.0,
                        "avg_retail_price_rub": 62.0,
                        "gross_margin_rub": 7000.0,
                        "gross_margin_rub_per_liter": 7.0,
                        "gross_margin_pct": 11.3,
                        "purchase_data_missing": False,
                    }
                ],
                "threshold_rub_per_liter": 3.0,
                "below_threshold_days": 0,
                "low_margin_days": [],
            },
            meta={
                **COMMON_META,
                "thresholds": [
                    {
                        "id": "margin-threshold",
                        "label": "Порог маржи",
                        "value": 3.0,
                        "unit": "RUB/L",
                    }
                ],
            },
        )

    def get_anomalies(self, **_kwargs):  # noqa: ANN003, ANN201
        return SimpleNamespace(data=[], meta={"count": 0})


FORECAST_DATA = {
    "product_code": "AI_95",
    "horizon_days": 7,
    "model_type": "catboost",
    "model_status": "active",
    "scenario_name": "base",
    "scenario_params": None,
    "forecast_points": [
        {"target_date": date(2026, 5, 6), "y_hat": 1010.0, "y_lo": 950.0, "y_hi": 1060.0}
    ],
    "base_forecast_points": [
        {"target_date": date(2026, 5, 6), "y_hat": 1010.0, "y_lo": 950.0, "y_hi": 1060.0}
    ],
    "scenario_forecast_points": None,
    "drivers": ["Спрос прошлой недели задаёт базовый тренд"],
    "model_freshness": "warning",
    "training_window": {"start_date": date(2025, 5, 6), "end_date": date(2026, 5, 5)},
    "baseline_comparison": {"catboost": {"smape": 4.8}, "seasonal_naive": {"smape": 6.1}},
    "feature_sources": ["lag_7", "price_margin", "external_indicators"],
    "retrain_status": "warning",
    "provider_mode": "cached",
    "external_context_quality": EXTERNAL_CONTEXT,
    "event_context": [],
    "reference_overlays": COMMON_META["reference_overlays"],
}


BACKTEST_DATA = {
    "product_code": "AI_95",
    "horizon_days": 7,
    "model_type": "catboost",
    "window_type": "rolling",
    "metrics": {"mae": 420.0, "rmse": 560.0, "smape": 4.8},
    "comparison": {
        "catboost": {"mae": 420.0, "rmse": 560.0, "smape": 4.8},
        "seasonal_naive": {"mae": 510.0, "rmse": 680.0, "smape": 6.1},
    },
    "trained_at": datetime(2026, 5, 5, tzinfo=UTC),
    "model_version": "20260505090000",
    "model_freshness": "warning",
    "training_window": {"start_date": date(2025, 5, 6), "end_date": date(2026, 5, 5)},
    "baseline_comparison": {"catboost": {"smape": 4.8}, "seasonal_naive": {"smape": 6.1}},
    "feature_sources": ["lag_7", "external_indicators"],
    "retrain_status": "warning",
    "provider_mode": "cached",
}


class FakeForecastService:
    def run_forecast(self, *, product_code, horizon_days, scenario):  # noqa: ANN001
        return SimpleNamespace(data=FORECAST_DATA, meta={**COMMON_META, "points": 1})

    def get_latest_forecast(self, *, product_code, horizon_days):  # noqa: ANN001
        return SimpleNamespace(data=FORECAST_DATA, meta={**COMMON_META, "points": 1})

    def get_latest_backtest(self, *, product_code, horizon_days):  # noqa: ANN001
        return SimpleNamespace(data=BACKTEST_DATA, meta={**COMMON_META})

    def run_backtest(self, *, product_code, horizon_days, window_type):  # noqa: ANN001
        return SimpleNamespace(data=BACKTEST_DATA, meta={**COMMON_META})


class FakeNewsService:
    def get_latest_digest(self, *, period_type):  # noqa: ANN001
        return {
            "digest_date": date(2026, 5, 5),
            "period_type": period_type,
            "summary_text": "Сводка построена по сохранённым источникам.",
            "bullet_points": ["Внешний фон умеренно влияет на маржу"],
            "source_ids": ["news-1"],
            "llm_mode": "off",
            "provider_mode": "cached",
            "news_freshness": "warning",
            "context_story": {"external_context": EXTERNAL_CONTEXT},
        }

    def search_news(self, *, q, date_from, date_to, topic, limit):  # noqa: ANN001
        return [
            {
                "id": uuid4(),
                "ref_id": "news_20260505_01",
                "source_name": "RBC",
                "provider_name": "rss",
                "published_at": datetime(2026, 5, 5, 9, 0, tzinfo=UTC),
                "title": "Топливный рынок стабилен",
                "url": "https://example.test/news",
                "snippet": "Оптовые цены остаются в сезонном диапазоне.",
                "topic_tags": ["oil_market"],
                "provider_mode": "cached",
                "confidence": 0.82,
            }
        ]

    def refresh_news(self):  # noqa: ANN201
        raise AssertionError("refresh is not used in analyst contract tests")


class FakeChatService:
    def create_session(self, *, user_id, title):  # noqa: ANN001
        now = datetime(2026, 5, 5, 9, 0, tzinfo=UTC)
        return SimpleNamespace(id=uuid4(), title=title, created_at=now, updated_at=now)

    def get_messages(self, *, user_id, session_id):  # noqa: ANN001
        return []

    def answer_question(self, *, user_id, session_id, question, context_scope):  # noqa: ANN001
        return {
            "answer": "Маржа объясняется найденными источниками.",
            "citations": [
                {
                    "type": "chart",
                    "ref_id": "analytics_margin_AI_95",
                    "title": "Маржа AI-95",
                    "provider_mode": "cached",
                    "confidence": 0.87,
                    "source_type": "analytics",
                }
            ],
            "mode": "retrieval_only",
            "provider_mode": "retrieval_only",
            "confidence": 0.87,
            "verification": {
                "status": "fallback_verified",
                "reason": "provider_unavailable",
                "checked_claims": 1,
                "supported_claims": 1,
                "severity": "warning",
            },
            "llm_provider": {
                "provider": "none",
                "mode": "retrieval_only",
                "model": None,
                "degradation_reason": "llm_disabled",
            },
            "retrieval": {
                "candidate_count": 3,
                "selected_count": 1,
                "source_counts": {"analytics": 1},
            },
        }


def _setup_overrides() -> None:
    auth_service = FakeAuthService()
    app.dependency_overrides[get_auth_service] = lambda: auth_service
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


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@fuelsight.local", "password": "analyst12345"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def _assert_envelope(payload: dict) -> None:
    assert set(payload.keys()) == {"data", "error", "meta"}
    assert payload["error"] is None
    assert isinstance(payload["meta"].get("request_id"), str)


def _assert_explainability(meta: dict) -> None:
    explainability = meta["explainability"]
    assert set(explainability.keys()) >= {"summary", "chart", "trust", "state"}
    assert explainability["summary"]["title"]
    assert explainability["chart"]["annotations"]
    assert explainability["chart"]["overlays"]
    assert explainability["chart"]["supporting_refs"]
    assert explainability["trust"]["external_context"]["quality_status"] == "warning"
    assert explainability["state"]["status"] == "ready"


def _assert_forecast_payload(data: dict) -> None:
    assert data["model_freshness"] == "warning"
    assert data["training_window"]["start_date"] == "2025-05-06"
    assert data["baseline_comparison"]["seasonal_naive"]["smape"] == 6.1
    assert "external_indicators" in data["feature_sources"]
    assert data["retrain_status"] == "warning"
    assert data["provider_mode"] == "cached"
    assert data["external_context_quality"]["quality_status"] == "warning"


def test_phase_k_backend_enriched_payload_contracts_are_stable() -> None:
    _setup_overrides()
    try:
        client = TestClient(app)
        token = _login(client)
        headers = {"Authorization": f"Bearer {token}"}

        responses = {
            "kpi_summary": client.get("/api/v1/kpi/summary?product_code=AI_95", headers=headers),
            "kpi_snapshot": client.get("/api/v1/kpi/snapshot?product_code=AI_95", headers=headers),
            "sales": client.get("/api/v1/analytics/sales?product_code=AI_95", headers=headers),
            "margin": client.get("/api/v1/analytics/margin?product_code=AI_95", headers=headers),
            "forecast_run": client.post(
                "/api/v1/forecasts/run",
                headers=headers,
                json={"product_code": "AI_95", "horizon_days": 7},
            ),
            "forecast_latest": client.get(
                "/api/v1/forecasts/latest?product_code=AI_95&horizon_days=7",
                headers=headers,
            ),
            "backtest_latest": client.get(
                "/api/v1/backtests/latest?product_code=AI_95&horizon_days=7",
                headers=headers,
            ),
            "news_digest": client.get(
                "/api/v1/news/digests/latest?period_type=daily",
                headers=headers,
            ),
            "news_search": client.get("/api/v1/news/search?q=market", headers=headers),
            "health": client.get("/api/v1/health"),
        }

        session_response = client.post(
            "/api/v1/chat/sessions",
            headers=headers,
            json={"title": "Phase K contract"},
        )
        session_id = session_response.json()["data"]["id"]
        responses["chat_answer"] = client.post(
            f"/api/v1/chat/sessions/{session_id}/messages",
            headers=headers,
            json={"question": "Почему изменилась маржа?", "context_scope": ["analytics"]},
        )
    finally:
        _cleanup_overrides()

    for response in responses.values():
        assert response.status_code == 200
        _assert_envelope(response.json())

    for key in ("kpi_summary", "kpi_snapshot", "sales", "margin"):
        _assert_explainability(responses[key].json()["meta"])

    _assert_forecast_payload(responses["forecast_run"].json()["data"])
    _assert_forecast_payload(responses["forecast_latest"].json()["data"])

    backtest_data = responses["backtest_latest"].json()["data"]
    assert backtest_data["model_freshness"] == "warning"
    assert backtest_data["baseline_comparison"]["catboost"]["smape"] == 4.8
    assert backtest_data["feature_sources"] == ["lag_7", "external_indicators"]

    news_digest = responses["news_digest"].json()
    assert news_digest["data"]["context_story"]["external_context"]["quality_status"] == "warning"
    assert news_digest["meta"]["llm_mode"] == "retrieval_only"

    news_search_item = responses["news_search"].json()["data"][0]
    assert news_search_item["provider_mode"] == "cached"
    assert news_search_item["confidence"] == 0.82

    chat_payload = responses["chat_answer"].json()
    citation = chat_payload["data"]["citations"][0]
    assert citation["provider_mode"] == "cached"
    assert citation["confidence"] == 0.87
    assert citation["source_type"] == "analytics"
    assert chat_payload["meta"]["llm_provider"]["mode"] == "retrieval_only"
    assert chat_payload["meta"]["retrieval"]["selected_count"] == 1

    health_data = responses["health"].json()["data"]
    assert "defense_profile" in health_data
    assert isinstance(health_data["llm_active"], dict)
    assert "llm_api_key" not in health_data
    assert "gigachat_auth_key" not in health_data
