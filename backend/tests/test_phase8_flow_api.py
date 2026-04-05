from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.dependencies.auth import get_auth_service
from app.dependencies.chat import get_chat_service
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


class FakeNewsService:
    def get_latest_digest(self, *, period_type: str):
        return {
            "digest_date": date(2026, 3, 28),
            "period_type": period_type,
            "summary_text": "Рост индикативов и логистические риски.",
            "bullet_points": ["Логистика влияет на закупку", "Спрос на бензин растет"],
            "source_ids": ["gdelt_2026_03_24_01", "gdelt_2026_03_25_02"],
            "llm_mode": "template_rag",
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
        return [
            {
                "id": uuid4(),
                "ref_id": "gdelt_2026_03_24_01",
                "source_name": "GDELT",
                "published_at": datetime(2026, 3, 24, 8, 30, tzinfo=UTC),
                "title": "Логистические ограничения",
                "url": "https://example.local/news/1",
                "snippet": "Снижение поставок",
                "topic_tags": ["logistics"],
                "impact_hint": "purchase_up",
            }
        ][:limit]

    def refresh_news(self):
        return type(
            "RefreshResult",
            (),
            {"status": "ok", "imported_news_count": 5, "created_digests": 2},
        )()


class FakeChatService:
    def __init__(self) -> None:
        self.session_id = uuid4()

    def create_session(self, *, user_id: UUID, title: str):
        return type(
            "Session",
            (),
            {
                "id": self.session_id,
                "title": title,
                "created_at": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "updated_at": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            },
        )()

    def get_messages(self, *, user_id: UUID, session_id: UUID):
        if session_id != self.session_id:
            raise ValueError("chat_session_not_found")
        return []

    def answer_question(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        question: str,
        context_scope: list[str],
    ):
        if session_id != self.session_id:
            raise ValueError("chat_session_not_found")
        return {
            "answer": "Шаблонный ответ по внутренним данным и новостям.",
            "citations": [
                {
                    "type": "news",
                    "ref_id": "gdelt_2026_03_24_01",
                    "title": "Логистические ограничения",
                },
                {
                    "type": "chart",
                    "ref_id": "analytics_margin_AI_95_latest",
                    "title": "Динамика маржи AI_95",
                },
            ],
            "mode": "template_rag",
        }


def _setup_overrides() -> FakeChatService:
    fake_auth = FakeAuthService()
    fake_news = FakeNewsService()
    fake_chat = FakeChatService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_news_service] = lambda: fake_news
    app.dependency_overrides[get_chat_service] = lambda: fake_chat
    app.dependency_overrides[get_settings] = lambda: Settings(enable_llm=True)
    return fake_chat


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_news_service, None)
    app.dependency_overrides.pop(get_chat_service, None)
    app.dependency_overrides.pop(get_settings, None)


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "analyst@fuelsight.local", "password": "analyst12345"},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_phase8_news_chat_flow_returns_citations() -> None:
    fake_chat = _setup_overrides()
    client = TestClient(app)
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    digest_response = client.get("/api/v1/news/digests/latest?period_type=daily", headers=headers)
    search_response = client.get("/api/v1/news/search?q=логистика", headers=headers)
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"title": "Почему выросла закупка?"},
    )
    answer_response = client.post(
        f"/api/v1/chat/sessions/{fake_chat.session_id}/messages",
        headers=headers,
        json={
            "question": "Почему выросла закупка?",
            "context_scope": ["internal_analytics", "news_digest"],
        },
    )
    _cleanup_overrides()

    assert digest_response.status_code == 200
    assert digest_response.json()["data"]["source_ids"]
    assert search_response.status_code == 200
    assert search_response.json()["meta"]["count"] >= 1
    assert session_response.status_code == 200
    assert answer_response.status_code == 200
    assert len(answer_response.json()["data"]["citations"]) >= 1
