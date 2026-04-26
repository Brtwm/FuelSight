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
            "digest_date": date(2026, 4, 5),
            "period_type": period_type,
            "summary_text": "Логистические факторы продолжают давить на закупочную цену.",
            "bullet_points": ["Растут индикативы", "Сохраняются логистические риски"],
            "source_ids": ["gdelt_2026_04_05_01"],
            "llm_mode": "off",
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
                "ref_id": "gdelt_2026_04_05_01",
                "source_name": "GDELT",
                "published_at": datetime(2026, 4, 5, 11, 30, tzinfo=UTC),
                "title": "Логистические ограничения на поставки топлива",
                "url": "https://example.local/news/logistics",
                "snippet": "Поставки замедлились из-за роста нагрузки на коридоры.",
                "topic_tags": ["logistics"],
                "impact_hint": "purchase_up",
            }
        ][:limit]

    def refresh_news(self):
        raise NotImplementedError


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
                "created_at": datetime(2026, 4, 5, 10, 0, tzinfo=UTC),
                "updated_at": datetime(2026, 4, 5, 10, 0, tzinfo=UTC),
            },
        )()

    def get_messages(self, *, user_id: UUID, session_id: UUID):
        return []

    def answer_question(
        self, *, user_id: UUID, session_id: UUID, question: str, context_scope: list[str]
    ):
        raise AssertionError("Chat generation should not be called when ENABLE_LLM=false")


def _setup_overrides() -> FakeChatService:
    fake_auth = FakeAuthService()
    fake_news = FakeNewsService()
    fake_chat = FakeChatService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_news_service] = lambda: fake_news
    app.dependency_overrides[get_chat_service] = lambda: fake_chat
    app.dependency_overrides[get_settings] = lambda: Settings(enable_llm=False)
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


def test_phase9_llm_off_smoke_flow() -> None:
    fake_chat = _setup_overrides()
    client = TestClient(app)
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    digest_response = client.get("/api/v1/news/digests/latest?period_type=daily", headers=headers)
    search_response = client.get("/api/v1/news/search?q=логистика", headers=headers)
    session_response = client.post(
        "/api/v1/chat/sessions",
        headers=headers,
        json={"title": "Проверка LLM off"},
    )
    chat_response = client.post(
        f"/api/v1/chat/sessions/{fake_chat.session_id}/messages",
        headers=headers,
        json={"question": "Почему выросла закупка?", "context_scope": ["news_digest"]},
    )
    _cleanup_overrides()

    assert digest_response.status_code == 200
    assert digest_response.json()["data"]["llm_mode"] == "off"
    assert search_response.status_code == 200
    assert search_response.json()["meta"]["count"] >= 1
    assert session_response.status_code == 200
    assert chat_response.status_code == 503
    assert chat_response.json()["error"]["code"] == "llm_disabled"
