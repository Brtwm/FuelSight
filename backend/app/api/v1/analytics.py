from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.responses import envelope, request_meta
from app.dependencies.analytics import get_analytics_service
from app.dependencies.auth import require_roles
from app.schemas.analytics import (
    AnalyticsAnomaly,
    MarginAnalyticsPayload,
    SalesAnalyticsPayload,
)
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticatedUser

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _merge_meta(request: Request, extra_meta: dict) -> dict:
    return {**extra_meta, **request_meta(request)}


@router.get("/sales")
def get_sales_analytics(
    request: Request,
    product_code: str = Query(..., min_length=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    granularity: Literal["day", "week", "month"] = Query(default="day"),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    try:
        result = analytics_service.get_sales(
            date_from=date_from,
            date_to=date_to,
            product_code=product_code,
            granularity=granularity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    payload = SalesAnalyticsPayload(**result.data).model_dump(mode="json")
    return envelope(data=payload, error=None, meta=_merge_meta(request, result.meta))


@router.get("/margin")
def get_margin_analytics(
    request: Request,
    product_code: str = Query(..., min_length=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    granularity: Literal["day", "week", "month"] = Query(default="day"),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    try:
        result = analytics_service.get_margin(
            date_from=date_from,
            date_to=date_to,
            product_code=product_code,
            granularity=granularity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    payload = MarginAnalyticsPayload(**result.data).model_dump(mode="json")
    return envelope(data=payload, error=None, meta=_merge_meta(request, result.meta))


@router.get("/anomalies")
def get_analytics_anomalies(
    request: Request,
    metric: Literal["sales", "margin", "purchase_price"] = Query(...),
    product_code: str = Query(..., min_length=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    try:
        result = analytics_service.get_anomalies(
            metric=metric,
            date_from=date_from,
            date_to=date_to,
            product_code=product_code,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    payload = [AnalyticsAnomaly(**item).model_dump(mode="json") for item in result.data]
    return envelope(data=payload, error=None, meta=_merge_meta(request, result.meta))
