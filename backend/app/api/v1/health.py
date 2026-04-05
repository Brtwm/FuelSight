from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.core.config import get_settings
from app.core.responses import envelope, request_meta

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    settings = get_settings()
    return envelope(
        data={
            "ok": True,
            "app_env": settings.app_env,
            "version": settings.app_version,
            "enable_llm": settings.enable_llm,
            "timestamp": datetime.now(UTC).isoformat(),
        },
        error=None,
        meta=request_meta(request),
    )
