from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.dependencies.auth import get_auth_service
from app.dependencies.chat import get_chat_service
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


class FakeChatService:
    def __init__(self) -> None:
        self.session_id = uuid4()
        self._messages = [
            {
                "id": uuid4(),
                "sender_type": "user",
                "message_text": "Почему выросла закупка?",
                "citations": None,
                "created_at": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            },
            {
                "id": uuid4(),
                "sender_type": "assistant",
                "message_text": "Рост закупочной цены подтверждён новостным фоном.",
                "citations": [
                    {
                        "type": "news",
                        "ref_id": "gdelt_2026_03_24_01",
                        "title": "Логистические ограничения",
                        "provider_mode": "cached",
                        "confidence": 0.78,
                        "source_type": "news_raw",
                    }
                ],
                "created_at": datetime(2026, 4, 1, 10, 1, tzinfo=UTC),
            },
        ]

    def create_session(self, *, user_id: UUID, title: str):
        if len(title.strip()) < 3:
            raise ValueError("title must be at least 3 characters")
        return type(
            "Session",
            (),
            {
                "id": self.session_id,
                "title": title.strip(),
                "created_at": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
                "updated_at": datetime(2026, 4, 1, 10, 0, tzinfo=UTC),
            },
        )()

    def get_messages(self, *, user_id: UUID, session_id: UUID):
        if session_id != self.session_id:
            raise ValueError("chat_session_not_found")
        return self._messages

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
        if "без источников" in question:
            raise ValueError("citations are required for chat answer generation")
        if "cloud" in question.lower():
            return {
                "answer": "Облачный ответ по подтверждённым источникам.",
                "citations": [
                    {
                        "type": "chart",
                        "ref_id": "analytics_margin_AI_95_latest",
                        "title": "Динамика маржи AI_95",
                        "provider_mode": "retrieval_only",
                        "confidence": 0.82,
                        "source_type": "analytics",
                    },
                ],
                "mode": "cloud_llm",
                "provider_mode": "cloud_llm",
                "confidence": 0.82,
                "verification": {
                    "status": "verified",
                    "reason": None,
                    "checked_claims": 1,
                    "supported_claims": 1,
                },
                "llm_provider": {
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "degradation_reason": None,
                },
                "retrieval": {
                    "candidate_count": 1,
                    "selected_count": 1,
                    "source_counts": {"analytics": 1},
                    "reranker_used": True,
                    "degradation_reason": None,
                },
            }
        return {
            "answer": "Шаблонный RAG-ответ по внутренним данным и новостям.",
            "citations": [
                {
                    "type": "news",
                    "ref_id": "gdelt_2026_03_24_01",
                    "title": "Логистические ограничения",
                    "provider_mode": "cached",
                    "confidence": 0.78,
                    "source_type": "news_raw",
                },
                {
                    "type": "chart",
                    "ref_id": "analytics_margin_AI_95_latest",
                    "title": "Динамика маржи AI_95",
                    "provider_mode": "retrieval_only",
                    "confidence": 0.82,
                    "source_type": "analytics",
                },
            ],
            "mode": "retrieval_only",
            "provider_mode": "retrieval_only",
            "confidence": 0.8,
            "verification": {
                "status": "verified",
                "reason": None,
                "checked_claims": 2,
                "supported_claims": 2,
            },
            "llm_provider": {
                "provider": "none",
                "mode": "retrieval_only",
                "degradation_reason": "llm_disabled",
            },
            "retrieval": {
                "candidate_count": 2,
                "selected_count": 2,
                "source_counts": {"news_raw": 1, "analytics": 1},
                "reranker_used": False,
                "degradation_reason": None,
            },
        }


def _setup_overrides(*, llm_enabled: bool) -> FakeChatService:
    fake_auth = FakeAuthService()
    fake_chat = FakeChatService()
    app.dependency_overrides[get_auth_service] = lambda: fake_auth
    app.dependency_overrides[get_chat_service] = lambda: fake_chat
    app.dependency_overrides[get_settings] = lambda: Settings(enable_llm=llm_enabled)
    return fake_chat


def _cleanup_overrides() -> None:
    app.dependency_overrides.pop(get_auth_service, None)
    app.dependency_overrides.pop(get_chat_service, None)
    app.dependency_overrides.pop(get_settings, None)


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_chat_create_session_and_get_messages() -> None:
    fake_chat = _setup_overrides(llm_enabled=True)
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    create_response = client.post(
        "/api/v1/chat/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Почему растёт закупка ДТ"},
    )
    messages_response = client.get(
        f"/api/v1/chat/sessions/{fake_chat.session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    _cleanup_overrides()

    assert create_response.status_code == 200
    assert messages_response.status_code == 200
    assert messages_response.json()["meta"]["count"] == 2


def test_chat_message_returns_retrieval_only_when_llm_disabled() -> None:
    fake_chat = _setup_overrides(llm_enabled=False)
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.post(
        f"/api/v1/chat/sessions/{fake_chat.session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "Что влияет на маржу?", "context_scope": ["internal_analytics"]},
    )
    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["mode"] == "retrieval_only"
    assert payload["data"]["citations"][0]["provider_mode"] == "cached"
    assert payload["data"]["citations"][0]["confidence"] == 0.78
    assert payload["data"]["citations"][0]["source_type"] == "news_raw"
    assert payload["meta"]["retrieval"]["selected_count"] == 2
    assert payload["meta"]["llm_provider"]["degradation_reason"] == "llm_disabled"


def test_chat_message_success_when_llm_enabled() -> None:
    fake_chat = _setup_overrides(llm_enabled=True)
    client = TestClient(app)
    token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.post(
        f"/api/v1/chat/sessions/{fake_chat.session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "Покажи факторы роста закупочной цены",
            "context_scope": ["internal_analytics", "news_digest"],
        },
    )
    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["error"] is None
    assert payload["data"]["mode"] == "retrieval_only"
    assert len(payload["data"]["citations"]) == 2


def test_chat_message_surfaces_cloud_provider_meta_when_cloud_path_is_used() -> None:
    fake_chat = _setup_overrides(llm_enabled=True)
    client = TestClient(app)
    token = _login(client, "admin@fuelsight.local", "admin12345")

    response = client.post(
        f"/api/v1/chat/sessions/{fake_chat.session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "cloud: покажи факторы маржи",
            "context_scope": ["internal_analytics"],
        },
    )
    _cleanup_overrides()

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["mode"] == "cloud_llm"
    assert payload["data"]["provider_mode"] == "cloud_llm"
    assert payload["data"]["citations"]
    assert payload["meta"]["llm_provider"]["provider"] == "neuraldeep"
    assert payload["meta"]["llm_provider"]["model"] == "gpt-oss-120b"
    assert payload["meta"]["retrieval"]["reranker_used"] is True


def test_chat_message_requires_citations() -> None:
    fake_chat = _setup_overrides(llm_enabled=True)
    client = TestClient(app)
    token = _login(client, "analyst@fuelsight.local", "analyst12345")

    response = client.post(
        f"/api/v1/chat/sessions/{fake_chat.session_id}/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "ответ без источников", "context_scope": ["news_digest"]},
    )
    _cleanup_overrides()

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
