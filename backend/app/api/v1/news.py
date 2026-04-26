from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.meta_builders import build_generic_domain_meta
from app.core.responses import envelope
from app.dependencies.auth import require_roles
from app.dependencies.news import get_news_service
from app.schemas.news import DigestPeriodType, NewsDigestPayload, NewsRefreshPayload, NewsSearchItem
from app.services.auth_service import AuthenticatedUser
from app.services.news_service import NewsService

router = APIRouter(prefix="/news", tags=["news"])


def _resolve_llm_mode(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized == "off":
        return "retrieval_only"
    if normalized == "template_rag":
        return "local_llm"
    return None


@router.get("/digests/latest")
def get_latest_digest(
    request: Request,
    period_type: DigestPeriodType = Query(default="daily"),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    news_service: NewsService = Depends(get_news_service),
):
    try:
        result = news_service.get_latest_digest(period_type=period_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    if result is None:
        return envelope(
            data=None,
            error=None,
            meta=build_generic_domain_meta(
                request,
                {
                    "period_type": period_type,
                    "empty_state": "Сводка новостей пока не сформирована.",
                },
            ),
        )

    payload = NewsDigestPayload(**result).model_dump(mode="json")
    return envelope(
        data=payload,
        error=None,
        meta=build_generic_domain_meta(
            request,
            {
                "provider_mode": payload.get("provider_mode"),
                "news_freshness": payload.get("news_freshness"),
                "llm_mode": _resolve_llm_mode(payload.get("llm_mode")),
                "external_indicators_mode": payload.get("provider_mode"),
                "external_context": (payload.get("context_story") or {}).get("external_context"),
            },
        ),
    )


@router.get("/search")
def search_news(
    request: Request,
    q: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    topic: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    news_service: NewsService = Depends(get_news_service),
):
    try:
        rows = news_service.search_news(
            q=q,
            date_from=date_from,
            date_to=date_to,
            topic=topic,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    payload = [NewsSearchItem(**item).model_dump(mode="json") for item in rows]
    return envelope(
        data=payload,
        error=None,
        meta=build_generic_domain_meta(
            request,
            {
                "count": len(payload),
            },
        ),
    )


@router.post("/refresh")
def refresh_news(
    request: Request,
    _: AuthenticatedUser = Depends(require_roles("admin")),
    news_service: NewsService = Depends(get_news_service),
):
    result = news_service.refresh_news()
    payload = NewsRefreshPayload(
        status=result.status,
        imported_news_count=result.imported_news_count,
        created_digests=result.created_digests,
        provider_mode=result.provider_mode,
        news_freshness=result.news_freshness,
        quality_status=result.quality_status,
        provider_mode_counts=result.provider_mode_counts,
        written_news_count=result.written_news_count,
        coverage_ratio=result.coverage_ratio,
        cache_dir=result.cache_dir,
        last_success_at=result.last_success_at,
    )
    return envelope(
        data=payload.model_dump(mode="json"),
        error=None,
        meta=build_generic_domain_meta(
            request,
            {
                "provider_mode": result.provider_mode,
                "news_freshness": result.news_freshness,
                "quality_status": result.quality_status,
                "coverage_ratio": result.coverage_ratio,
            },
        ),
    )
