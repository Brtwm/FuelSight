from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.dependencies.auth import get_auth_service
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


class FakeNewsService:
    def get_latest_digest(self, *, period_type: str):
        if period_type == "weekly":
            return None
        return {
            "digest_date": date(2026, 3, 28),
            "created_at": datetime(2026, 3, 28, 9, 15, tzinfo=UTC),
            "period_type": "daily",
            "summary_text": "Рост закупочных индикативов и сезонный спрос на бензин.",
            "bullet_points": ["Рост индикативов AI-95", "Риск по логистике ДТ"],
            "source_ids": ["gdelt_2026_03_25_02", "gdelt_2026_03_24_01"],
            "llm_mode": "off",
            "provider_mode": "cached",
            "news_freshness": "fresh",
            "context_story": {
                "window": {"start_date": "2026-03-28", "end_date": "2026-03-28"},
                "external_context": {
                    "provider_mode": "cached",
                    "coverage_ratio": 0.94,
                    "fallback_ratio": 0.22,
                    "quality_status": "warning",
                    "reasons": ["coverage_ratio=0.940<0.95"],
                    "manifest_run_date": "2026-03-28",
                    "source_refs": [],
                },
                "event_context": [
                    {
                        "event_code": "may_holiday_mobility",
                        "title": "Майская мобильность",
                        "start_date": "2026-03-28",
                        "end_date": "2026-03-28",
                        "pressure_score": 0.2,
                        "demand_delta_pct": 1.0,
                        "purchase_delta_pct": 0.4,
                        "source_mode": "db",
                    }
                ],
                "indicator_refs": [],
                "event_refs": [],
            },
        }

    def search_news(
        self,
        *,
        q: str | None,
        date_from: date | None,
        date_to: date | None,
        topic: str | None,
        limit: int,
    ):
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be less than or equal to date_to")
        return [
            {
                "id": uuid4(),
                "ref_id": "gdelt_2026_03_24_01",
                "source_name": "GDELT",
                "provider_name": "GDELT",
                "published_at": datetime(2026, 3, 24, 8, 30, tzinfo=UTC),
                "title": "Логистические ограничения",
                "url": "https://example.local/news/1",
                "snippet": "Снижение поставок",
                "topic_tags": ["logistics"],
                "impact_hint": "purchase_up",
                "provider_mode": "cached",
                "confidence": 0.67,
                "cached_at": datetime(2026, 3, 24, 9, 0, tzinfo=UTC),
            }
        ][:limit]

    def refresh_news(self):
        return type(
            "RefreshResult",
            (),
            {
                "status": "warning",
                "imported_news_count": 5,
                "created_digests": 2,
                "provider_mode": "cached",
                "news_freshness": "fresh",
                "quality_status": "warning",
                "provider_mode_counts": {"cached": 5},
                "written_news_count": 5,
                "coverage_ratio": 0.75,
                "cache_dir": "/tmp/news",
                "last_success_at": "2026-03-28T09:00:00+00:00",
            },
        )()


def _setup_overrides() -> None:
    fake_auth = FakeAuthService()
    fake_news = FakeNewsService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_news_service] = lambda: fake_news


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_news_service, None)


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_news_digest_returns_data_for_analyst() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.get(
        "/api/v1/news/digests/latest?period_type=daily",
        headers={"Authorization": f"Bearer {token}"},
    )
    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["period_type"] == "daily"
    assert len(payload["data"]["source_ids"]) == 2
    assert payload["data"]["context_story"]["external_context"]["quality_status"] == "warning"


def test_news_digest_empty_state_is_supported() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.get(
        "/api/v1/news/digests/latest?period_type=weekly",
        headers={"Authorization": f"Bearer {token}"},
    )
    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] is None
    assert payload["meta"]["empty_state"]


def test_news_search_returns_envelope_and_count() -> None:
    _setup_overrides()
    client = TestClient(app)
    token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.get(
        "/api/v1/news/search?q=логистика&limit=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["meta"]["count"] == 1
    assert payload["data"][0]["source_name"] == "GDELT"
    assert payload["data"][0]["provider_mode"] == "cached"
    assert payload["data"][0]["confidence"] == 0.67


def test_news_refresh_is_admin_only() -> None:
    _setup_overrides()
    client = TestClient(app)
    admin_token = _login(client, "admin@fuelsight.local", "admin12345")
    analyst_token = _login(client, "analyst@fuelsight.local", "analyst12345")

    analyst_response = client.post(
        "/api/v1/news/refresh",
        headers={"Authorization": f"Bearer {analyst_token}"},
    )
    admin_response = client.post(
        "/api/v1/news/refresh",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    _cleanup_overrides()

    assert analyst_response.status_code == 403
    assert admin_response.status_code == 200
    assert admin_response.json()["data"]["created_digests"] == 2
    assert admin_response.json()["data"]["provider_mode"] == "cached"
