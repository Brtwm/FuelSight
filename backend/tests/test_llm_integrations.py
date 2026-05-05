from __future__ import annotations

import json
import os
from io import BytesIO
from http.client import RemoteDisconnected
from urllib.error import HTTPError

import pytest

from app.core.config import Settings
from app.integrations.llm import adapters as llm_adapters
from app.integrations.llm.adapters import GigaChatAdapter, OpenAICompatibleAdapter, UrllibJsonClient
from app.integrations.llm.contracts import LlmChatRequest, RerankDocument
from app.integrations.llm.registry import resolve_llm_adapter


class FakeHttpClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        if url.endswith("/chat/completions"):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Подтверждённый вывод по источникам.",
                        }
                    }
                ],
                "usage": {"total_tokens": 42},
            }
        if url.endswith("/embeddings"):
            return {"data": [{"embedding": [float(index) for index in range(128)]}]}
        if url.endswith("/rerank"):
            return {"results": [{"index": 1, "relevance_score": 0.91}]}
        raise AssertionError(f"unexpected url {url}")


class FakeGigaChatHttpClient:
    def __init__(self) -> None:
        self.form_calls: list[dict[str, object]] = []
        self.json_calls: list[dict[str, object]] = []
        self.token_counter = 0
        self.fail_first_chat_with_401 = False
        self._chat_failed = False

    def post_form(
        self,
        *,
        url: str,
        headers: dict[str, str],
        form: dict[str, str],
        timeout_seconds: float,
    ) -> dict[str, object]:
        self.form_calls.append(
            {
                "url": url,
                "headers": headers,
                "form": form,
                "timeout_seconds": timeout_seconds,
            }
        )
        self.token_counter += 1
        return {"access_token": f"token-{self.token_counter}", "expires_in": 1800}

    def post_json(
        self,
        *,
        url: str,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        self.json_calls.append(
            {
                "url": url,
                "headers": headers,
                "payload": payload,
                "timeout_seconds": timeout_seconds,
            }
        )
        if self.fail_first_chat_with_401 and not self._chat_failed:
            self._chat_failed = True
            raise HTTPError(url=url, code=401, msg="Unauthorized", hdrs=None, fp=BytesIO())
        if url.endswith("/chat/completions"):
            return {"choices": [{"message": {"content": "Ответ GigaChat по источникам."}}]}
        if url.endswith("/embeddings"):
            return {"data": [{"embedding": [0.0, 1.0, 0.0, 1.0]}]}
        raise AssertionError(f"unexpected url {url}")


def test_urllib_json_client_retries_rate_limit_then_succeeds(monkeypatch) -> None:
    calls = 0

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):  # noqa: ANN001
            return False

        def read(self) -> bytes:
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):  # noqa: ANN001
        nonlocal calls
        calls += 1
        if calls < 3:
            raise HTTPError(
                url=request.full_url,
                code=429,
                msg="Too Many Requests",
                hdrs=None,
                fp=BytesIO(b'{"error":"rate_limited"}'),
            )
        return FakeResponse()

    monkeypatch.setattr(llm_adapters.urllib_request, "urlopen", fake_urlopen)

    result = UrllibJsonClient().post_json(
        url="https://api.neuraldeep.ru/v1/chat/completions",
        headers={"authorization": "Bearer secret"},
        payload={"model": "gpt-oss-120b"},
        timeout_seconds=60,
    )

    assert result == {"ok": True}
    assert calls == 3


def test_urllib_json_client_retries_remote_disconnect_then_succeeds(monkeypatch) -> None:
    calls = 0

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):  # noqa: ANN001
            return False

        def read(self) -> bytes:
            return b'{"ok": true}'

    def fake_urlopen(request, timeout):  # noqa: ANN001
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RemoteDisconnected("Remote end closed connection without response")
        return FakeResponse()

    monkeypatch.setattr(llm_adapters.urllib_request, "urlopen", fake_urlopen)

    result = UrllibJsonClient().post_json(
        url="https://api.neuraldeep.ru/v1/chat/completions",
        headers={"authorization": "Bearer secret"},
        payload={"model": "gpt-oss-120b"},
        timeout_seconds=60,
    )

    assert result == {"ok": True}
    assert calls == 2


def test_openai_compatible_adapter_sends_sanitized_chat_request() -> None:
    client = FakeHttpClient()
    adapter = OpenAICompatibleAdapter(
        provider_name="neuraldeep",
        base_url="https://api.neuraldeep.ru/v1/",
        api_key="secret-key",
        chat_model="gpt-oss-120b",
        embedding_model="bge-m3",
        reranker_model="bge-reranker",
        timeout_seconds=7.5,
        http_client=client,
    )

    result = adapter.chat(
        LlmChatRequest(
            question="Почему изменилась маржа AI_95?",
            evidence_pack={
                "items": [
                    {
                        "title": "Маржа AI_95",
                        "snippet": "Маржа снизилась из-за закупочной цены.",
                        "raw_table": [{"should": "not be here"}],
                    }
                ]
            },
            citations=[{"ref_id": "analytics_margin_AI_95", "title": "Маржа AI_95"}],
            running_summary="",
        )
    )

    assert result.answer == "Подтверждённый вывод по источникам."
    assert result.provider == "neuraldeep"
    assert result.mode == "cloud_llm"
    assert result.model == "gpt-oss-120b"
    call = client.calls[0]
    assert call["url"] == "https://api.neuraldeep.ru/v1/chat/completions"
    assert call["headers"] == {
        "authorization": "Bearer secret-key",
        "content-type": "application/json",
    }
    payload = call["payload"]
    assert payload["model"] == "gpt-oss-120b"
    assert payload["temperature"] == 0
    messages = payload["messages"]
    assert isinstance(messages, list)
    system_prompt = messages[0]["content"]
    assert "аналитик FuelSight" in system_prompt
    assert "только evidence pack" in system_prompt
    assert "citations" in system_prompt
    assert "Не добавляй факты" in system_prompt
    assert "Не называй числа" in system_prompt
    assert "Не превращай новости" in system_prompt
    assert "внешний фон без доказанной причинности" in system_prompt
    assert "Недостаточно подтверждённых данных" in system_prompt
    assert "3 коротких абзаца" in system_prompt
    payload_text = json.dumps(payload, ensure_ascii=False)
    assert "Маржа снизилась" in payload_text
    assert "raw_table" not in payload_text
    assert call["timeout_seconds"] == 7.5


def test_openai_compatible_adapter_normalizes_embeddings_to_target_dimensions() -> None:
    adapter = OpenAICompatibleAdapter(
        provider_name="neuraldeep",
        base_url="https://api.neuraldeep.ru/v1",
        api_key="secret-key",
        chat_model="gpt-oss-120b",
        embedding_model="bge-m3",
        reranker_model="bge-reranker",
        embedding_dimensions=64,
        http_client=FakeHttpClient(),
    )

    result = adapter.embed_texts(["маржа дизель логистика"])

    assert result.provider == "neuraldeep"
    assert result.mode == "cloud_llm"
    assert len(result.vectors) == 1
    assert len(result.vectors[0]) == 64


def test_openai_compatible_adapter_reranks_documents() -> None:
    adapter = OpenAICompatibleAdapter(
        provider_name="neuraldeep",
        base_url="https://api.neuraldeep.ru/v1",
        api_key="secret-key",
        chat_model="gpt-oss-120b",
        embedding_model="bge-m3",
        reranker_model="bge-reranker",
        http_client=FakeHttpClient(),
    )

    result = adapter.rerank(
        query="почему растёт закупка",
        documents=[
            RerankDocument(index=0, text="Нерелевантно"),
            RerankDocument(index=1, text="Закупочная цена выросла"),
        ],
    )

    assert result.provider == "neuraldeep"
    assert result.scores[1] == 0.91


def test_llm_registry_resolves_neuraldeep_cloud_profile_when_key_is_present() -> None:
    resolution = resolve_llm_adapter(
        Settings(
            enable_llm=True,
            llm_provider_mode="cloud_first",
            llm_provider="neuraldeep",
            llm_api_key="secret-key",
        )
    )

    assert resolution.mode == "cloud_llm"
    assert resolution.provider == "neuraldeep"
    assert resolution.adapter is not None
    assert resolution.degradation_reason is None


def test_llm_registry_degrades_when_cloud_key_is_missing() -> None:
    resolution = resolve_llm_adapter(
        Settings(
            enable_llm=True,
            llm_provider_mode="cloud_first",
            llm_provider="neuraldeep",
            llm_api_key=None,
        )
    )

    assert resolution.mode == "retrieval_only"
    assert resolution.provider == "none"
    assert resolution.adapter is None
    assert resolution.degradation_reason == "cloud_api_key_missing"


def test_llm_registry_uses_gigachat_when_neuraldeep_key_is_missing() -> None:
    resolution = resolve_llm_adapter(
        Settings(
            enable_llm=True,
            llm_provider_mode="cloud_first",
            llm_provider="neuraldeep",
            llm_api_key=None,
            gigachat_auth_key="gigachat-secret",
        )
    )

    assert resolution.mode == "cloud_llm"
    assert resolution.provider == "gigachat"
    assert resolution.adapter is not None
    assert resolution.model == "GigaChat"
    assert resolution.degradation_reason is None


def test_llm_registry_offline_safe_never_enables_cloud_even_with_keys() -> None:
    resolution = resolve_llm_adapter(
        Settings(
            enable_llm=False,
            llm_provider_mode="retrieval_only",
            llm_provider="neuraldeep",
            llm_api_key="neuraldeep-secret",
            gigachat_auth_key="gigachat-secret",
            defense_profile="offline-safe",
        )
    )

    assert resolution.mode == "retrieval_only"
    assert resolution.provider == "none"
    assert resolution.adapter is None
    assert resolution.degradation_reason == "llm_disabled"


def test_openai_compatible_registry_requires_base_url() -> None:
    resolution = resolve_llm_adapter(
        Settings(
            enable_llm=True,
            llm_provider_mode="cloud_first",
            llm_provider="openai_compatible",
            llm_api_key="secret-key",
            llm_openai_compat_base_url=None,
        )
    )

    assert resolution.mode == "retrieval_only"
    assert resolution.provider == "none"
    assert resolution.adapter is None
    assert resolution.degradation_reason == "openai_compatible_base_url_missing"


def test_gigachat_boundary_reports_not_configured_without_live_auth() -> None:
    adapter = GigaChatAdapter(api_key=None)

    health = adapter.health()

    assert health.provider == "gigachat"
    assert health.mode == "retrieval_only"
    assert health.available is False
    assert health.degradation_reason == "gigachat_auth_not_configured"


def test_gigachat_adapter_obtains_token_and_calls_chat_completions() -> None:
    client = FakeGigaChatHttpClient()
    adapter = GigaChatAdapter(
        api_key="basic-secret",
        base_url="https://gigachat.devices.sberbank.ru/api/v1",
        auth_url="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        scope="GIGACHAT_API_PERS",
        chat_model="GigaChat",
        embedding_model="EmbeddingsGigaR",
        http_client=client,
    )

    result = adapter.chat(
        LlmChatRequest(
            question="Что с маржой AI_95?",
            evidence_pack={"items": [{"title": "Маржа", "snippet": "Маржа снизилась."}]},
            citations=[{"ref_id": "analytics_margin_AI_95", "title": "Маржа"}],
        )
    )

    assert result.answer == "Ответ GigaChat по источникам."
    assert result.provider == "gigachat"
    assert result.model == "GigaChat"
    assert len(client.form_calls) == 1
    assert client.form_calls[0]["form"] == {"scope": "GIGACHAT_API_PERS"}
    assert client.json_calls[0]["url"] == (
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    )
    assert client.json_calls[0]["headers"]["authorization"] == "Bearer token-1"


def test_gigachat_adapter_reuses_token_for_embeddings() -> None:
    client = FakeGigaChatHttpClient()
    adapter = GigaChatAdapter(
        api_key="basic-secret",
        base_url="https://gigachat.devices.sberbank.ru/api/v1",
        auth_url="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        scope="GIGACHAT_API_PERS",
        chat_model="GigaChat",
        embedding_model="EmbeddingsGigaR",
        http_client=client,
    )

    adapter.chat(
        LlmChatRequest(
            question="Что с маржой AI_95?",
            evidence_pack={"items": [{"title": "Маржа", "snippet": "Маржа снизилась."}]},
            citations=[{"ref_id": "analytics_margin_AI_95", "title": "Маржа"}],
        )
    )
    embeddings = adapter.embed_texts(["маржа AI_95"])

    assert len(client.form_calls) == 1
    assert len(embeddings.vectors) == 1
    assert len(embeddings.vectors[0]) == 64
    assert client.json_calls[1]["headers"]["authorization"] == "Bearer token-1"


def test_gigachat_adapter_refreshes_token_once_after_unauthorized() -> None:
    client = FakeGigaChatHttpClient()
    client.fail_first_chat_with_401 = True
    adapter = GigaChatAdapter(
        api_key="basic-secret",
        base_url="https://gigachat.devices.sberbank.ru/api/v1",
        auth_url="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        scope="GIGACHAT_API_PERS",
        chat_model="GigaChat",
        embedding_model="EmbeddingsGigaR",
        http_client=client,
    )

    result = adapter.chat(
        LlmChatRequest(
            question="Что с маржой AI_95?",
            evidence_pack={"items": [{"title": "Маржа", "snippet": "Маржа снизилась."}]},
            citations=[{"ref_id": "analytics_margin_AI_95", "title": "Маржа"}],
        )
    )

    assert result.answer == "Ответ GigaChat по источникам."
    assert len(client.form_calls) == 2
    assert client.json_calls[0]["headers"]["authorization"] == "Bearer token-1"
    assert client.json_calls[1]["headers"]["authorization"] == "Bearer token-2"


@pytest.mark.skipif(
    not os.getenv("LLM_API_KEY"),
    reason="LLM_API_KEY is required for optional NeuralDeep/OpenAI-compatible live smoke",
)
def test_openai_compatible_live_contract_smoke() -> None:
    resolution = resolve_llm_adapter(
        Settings(
            enable_llm=True,
            llm_provider_mode="cloud_first",
            llm_provider=os.getenv("LLM_PROVIDER", "neuraldeep"),
            llm_api_key=os.environ["LLM_API_KEY"],
            llm_openai_compat_base_url=os.getenv("LLM_OPENAI_COMPAT_BASE_URL") or None,
            llm_chat_model=os.getenv("LLM_CHAT_MODEL") or None,
            llm_embedding_model=os.getenv("LLM_EMBEDDING_MODEL") or None,
            llm_reranker_model=os.getenv("LLM_RERANKER_MODEL") or None,
        )
    )

    assert resolution.adapter is not None
    result = resolution.adapter.chat(
        LlmChatRequest(
            question="Кратко проверь формат ответа.",
            evidence_pack={"items": [{"title": "Smoke", "snippet": "FuelSight smoke test."}]},
            citations=[{"ref_id": "smoke_ref", "title": "Smoke"}],
        )
    )

    assert result.answer.strip()


@pytest.mark.skipif(
    not os.getenv("GIGACHAT_AUTH_KEY"),
    reason="GIGACHAT_AUTH_KEY is required for optional GigaChat live smoke",
)
def test_gigachat_live_contract_smoke() -> None:
    adapter = GigaChatAdapter(
        api_key=os.environ["GIGACHAT_AUTH_KEY"],
        base_url=os.getenv("GIGACHAT_BASE_URL", "https://gigachat.devices.sberbank.ru/api/v1"),
        auth_url=os.getenv(
            "GIGACHAT_AUTH_URL",
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        ),
        scope=os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS"),
        chat_model=os.getenv("GIGACHAT_CHAT_MODEL", "GigaChat"),
        embedding_model=os.getenv("GIGACHAT_EMBEDDING_MODEL", "EmbeddingsGigaR"),
    )

    result = adapter.chat(
        LlmChatRequest(
            question="Кратко проверь формат ответа.",
            evidence_pack={"items": [{"title": "Smoke", "snippet": "FuelSight smoke test."}]},
            citations=[{"ref_id": "smoke_ref", "title": "Smoke"}],
        )
    )

    assert result.answer.strip()
