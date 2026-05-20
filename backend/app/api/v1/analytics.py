from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.meta_builders import (
    build_generic_domain_meta,
    build_margin_meta,
    build_sales_meta,
)
from app.core.responses import envelope
from app.core.roles import (
    MARGIN_ANALYTICS_ROLES,
    SALES_ANALYTICS_ROLES,
    analytics_roles_for_metric,
)
from app.dependencies.analytics import get_analytics_service
from app.dependencies.auth import forbidden_exception, get_current_user, require_roles
from app.schemas.analytics import (
    AnalyticsAnomaly,
    MarginAnalyticsPayload,
    SalesAnalyticsPayload,
)
from app.services.analytics_service import AnalyticsService
from app.services.auth_service import AuthenticatedUser

router = APIRouter(prefix="/analytics", tags=["analytics"])


def require_analytics_metric_access(
    metric: Literal["sales", "margin", "purchase_price"] = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if current_user.role not in analytics_roles_for_metric(metric):
        raise forbidden_exception()
    return current_user


@router.get("/sales")
def get_sales_analytics(
    request: Request,
    product_code: str = Query(..., min_length=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    granularity: Literal["day", "week", "month"] = Query(default="day"),
    _: AuthenticatedUser = Depends(require_roles(*SALES_ANALYTICS_ROLES)),
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
    return envelope(
        data=payload,
        error=None,
        meta=build_sales_meta(request, result.meta),
    )


@router.get("/margin")
def get_margin_analytics(
    request: Request,
    product_code: str = Query(..., min_length=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    granularity: Literal["day", "week", "month"] = Query(default="day"),
    _: AuthenticatedUser = Depends(require_roles(*MARGIN_ANALYTICS_ROLES)),
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
    return envelope(
        data=payload,
        error=None,
        meta=build_margin_meta(request, result.meta),
    )


@router.get("/anomalies")
def get_analytics_anomalies(
    request: Request,
    metric: Literal["sales", "margin", "purchase_price"] = Query(...),
    product_code: str = Query(..., min_length=1),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_analytics_metric_access),
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
    return envelope(
        data=payload,
        error=None,
        meta=build_generic_domain_meta(request, result.meta),
    )
