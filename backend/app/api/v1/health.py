from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.responses import envelope, request_meta
from app.integrations.llm.registry import resolve_llm_adapter

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    settings = get_settings()
    llm_resolution = resolve_llm_adapter(settings)
    return envelope(
        data={
            "ok": True,
            "app_env": settings.app_env,
            "version": settings.app_version,
            "enable_llm": settings.enable_llm,
            "llm_provider": settings.llm_provider,
            "llm_provider_mode": settings.llm_provider_mode,
            "llm_chat_model": settings.llm_chat_model,
            "llm_embedding_model": settings.llm_embedding_model,
            "cloud_configured": (
                bool(settings.llm_api_key)
                and settings.llm_provider.strip().lower()
                in {"neuraldeep", "openai_compatible"}
            )
            or (
                bool(settings.gigachat_auth_key or settings.llm_api_key)
                and settings.llm_provider.strip().lower() == "gigachat"
            ),
            "fallback_available": True,
            "llm_active": llm_resolution.to_payload(),
            "timestamp": datetime.now(UTC).isoformat(),
        },
        error=None,
        meta=request_meta(request),
    )
