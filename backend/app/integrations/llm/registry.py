from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.integrations.llm.adapters import GigaChatAdapter, LocalLlmAdapter, OpenAICompatibleAdapter
from app.integrations.llm.contracts import LlmAdapter
from app.schemas.common import ProviderMode

NEURALDEEP_BASE_URL = "https://api.neuraldeep.ru/v1"
NEURALDEEP_CHAT_MODEL = "gpt-oss-120b"
NEURALDEEP_EMBEDDING_MODEL = "bge-m3"
NEURALDEEP_RERANKER_MODEL = "bge-reranker"


@dataclass(frozen=True)
class LlmResolution:
    mode: ProviderMode
    provider: str
    adapter: LlmAdapter | None = None
    model: str | None = None
    degradation_reason: str | None = None

    def to_payload(self) -> dict[str, object | None]:
        return {
            "provider": self.provider,
            "mode": self.mode,
            "model": self.model,
            "degradation_reason": self.degradation_reason,
        }


def resolve_llm_adapter(settings: Settings) -> LlmResolution:
    if not settings.enable_llm:
        return LlmResolution(
            mode="retrieval_only",
            provider="none",
            degradation_reason="llm_disabled",
        )

    provider_mode = settings.llm_provider_mode.strip().lower()
    provider = settings.llm_provider.strip().lower()
    if provider_mode == "retrieval_only":
        return LlmResolution(mode="retrieval_only", provider="none")

    if provider_mode == "local_only" or provider == "local":
        adapter = LocalLlmAdapter()
        health = adapter.health()
        if health.available:
            return LlmResolution(
                mode="local_llm",
                provider="local",
                adapter=adapter,
                model=health.model,
            )
        return LlmResolution(
            mode="retrieval_only",
            provider="none",
            degradation_reason=health.degradation_reason,
        )

    if provider in {"neuraldeep", "openai_compatible"}:
        if not settings.llm_api_key:
            gigachat_resolution = _resolve_gigachat_fallback(settings)
            if gigachat_resolution is not None:
                return gigachat_resolution
            return LlmResolution(
                mode="retrieval_only",
                provider="none",
                degradation_reason="cloud_api_key_missing",
            )
        base_url = settings.llm_openai_compat_base_url or (
            NEURALDEEP_BASE_URL if provider == "neuraldeep" else ""
        )
        if not base_url:
            return LlmResolution(
                mode="retrieval_only",
                provider="none",
                degradation_reason="openai_compatible_base_url_missing",
            )
        adapter = OpenAICompatibleAdapter(
            provider_name="neuraldeep" if provider == "neuraldeep" else "openai_compatible",
            base_url=base_url,
            api_key=settings.llm_api_key,
            chat_model=settings.llm_chat_model or NEURALDEEP_CHAT_MODEL,
            embedding_model=settings.llm_embedding_model
            or (NEURALDEEP_EMBEDDING_MODEL if provider == "neuraldeep" else None),
            reranker_model=settings.llm_reranker_model
            or (NEURALDEEP_RERANKER_MODEL if provider == "neuraldeep" else None),
            timeout_seconds=settings.llm_timeout_seconds,
            embedding_dimensions=settings.llm_embedding_dimensions,
            max_evidence_chars=settings.llm_max_evidence_chars,
        )
        return LlmResolution(
            mode="cloud_llm",
            provider=adapter.provider_name,
            adapter=adapter,
            model=adapter.chat_model,
        )

    if provider == "gigachat":
        return _resolve_gigachat(settings)

    return LlmResolution(
        mode="retrieval_only",
        provider="none",
        degradation_reason="llm_provider_not_configured",
    )


def _resolve_gigachat_fallback(settings: Settings) -> LlmResolution | None:
    if settings.llm_provider_mode.strip().lower() != "cloud_first":
        return None
    if not settings.gigachat_auth_key:
        return None
    return _resolve_gigachat(settings)


def _resolve_gigachat(settings: Settings) -> LlmResolution:
    adapter = GigaChatAdapter(
        api_key=settings.gigachat_auth_key or settings.llm_api_key,
        base_url=settings.gigachat_base_url,
        auth_url=settings.gigachat_auth_url,
        scope=settings.gigachat_scope,
        chat_model=settings.gigachat_chat_model,
        embedding_model=settings.gigachat_embedding_model,
        timeout_seconds=settings.llm_timeout_seconds,
        embedding_dimensions=settings.llm_embedding_dimensions,
        max_evidence_chars=settings.llm_max_evidence_chars,
    )
    health = adapter.health()
    if health.available:
        return LlmResolution(
            mode="cloud_llm",
            provider="gigachat",
            adapter=adapter,
            model=health.model,
        )
    return LlmResolution(
        mode="retrieval_only",
        provider="none",
        degradation_reason=health.degradation_reason,
    )
