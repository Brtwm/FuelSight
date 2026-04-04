from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.core.responses import envelope, request_meta
from app.dependencies.auth import require_roles
from app.dependencies.kpi import get_kpi_service
from app.schemas.kpi import KpiAlert, KpiSnapshotPoint, KpiSummary
from app.services.auth_service import AuthenticatedUser
from app.services.kpi_service import KpiService

router = APIRouter(prefix="/kpi", tags=["kpi"])


def _merge_meta(request: Request, extra_meta: dict) -> dict:
    return {**extra_meta, **request_meta(request)}


@router.get("/summary")
def get_kpi_summary(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    product_code: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    kpi_service: KpiService = Depends(get_kpi_service),
):
    try:
        result = kpi_service.get_summary(
            date_from=date_from,
            date_to=date_to,
            product_code=product_code,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    payload = None if result.data is None else KpiSummary(**result.data).model_dump(mode="json")
    return envelope(data=payload, error=None, meta=_merge_meta(request, result.meta))


@router.get("/alerts")
def get_kpi_alerts(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    product_code: str | None = Query(default=None),
    severity: Literal["high", "medium", "low"] | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    kpi_service: KpiService = Depends(get_kpi_service),
):
    try:
        result = kpi_service.get_alerts(
            date_from=date_from,
            date_to=date_to,
            product_code=product_code,
            severity=severity,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    payload = [KpiAlert(**item).model_dump(mode="json") for item in result.data]
    return envelope(data=payload, error=None, meta=_merge_meta(request, result.meta))


@router.get("/snapshot")
def get_kpi_snapshot(
    request: Request,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    product_code: str | None = Query(default=None),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    kpi_service: KpiService = Depends(get_kpi_service),
):
    try:
        result = kpi_service.get_snapshot(
            date_from=date_from,
            date_to=date_to,
            product_code=product_code,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    payload = [KpiSnapshotPoint(**item).model_dump(mode="json") for item in result.data]
    return envelope(data=payload, error=None, meta=_merge_meta(request, result.meta))

