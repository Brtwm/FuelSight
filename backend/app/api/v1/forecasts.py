from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.meta_builders import build_generic_domain_meta
from app.core.responses import envelope
from app.dependencies.auth import require_roles
from app.dependencies.forecast import get_forecast_service
from app.schemas.forecasts import ForecastPayload, ForecastRunRequest
from app.services.auth_service import AuthenticatedUser
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/forecasts", tags=["forecasts"])


@router.post("/run")
def run_forecast(
    request: Request,
    payload: ForecastRunRequest,
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    forecast_service: ForecastService = Depends(get_forecast_service),
):
    try:
        result = forecast_service.run_forecast(
            product_code=payload.product_code,
            horizon_days=payload.horizon_days,
            scenario=payload.scenario.model_dump() if payload.scenario is not None else None,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc
    data = ForecastPayload(**result.data).model_dump(mode="json")
    return envelope(
        data=data,
        error=None,
        meta=build_generic_domain_meta(request, result.meta),
    )


@router.get("/latest")
def get_latest_forecast(
    request: Request,
    product_code: str = Query(..., min_length=1),
    horizon_days: int = Query(...),
    _: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    forecast_service: ForecastService = Depends(get_forecast_service),
):
    try:
        result = forecast_service.get_latest_forecast(
            product_code=product_code,
            horizon_days=horizon_days,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    data = None
    if result.data is not None:
        data = ForecastPayload(**result.data).model_dump(mode="json")
    return envelope(
        data=data,
        error=None,
        meta=build_generic_domain_meta(request, result.meta),
    )
