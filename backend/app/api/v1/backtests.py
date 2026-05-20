from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.v1.meta_builders import build_generic_domain_meta
from app.core.responses import envelope
from app.core.roles import BACKTEST_READ_ROLES, BACKTEST_RUN_ROLES
from app.dependencies.auth import require_roles
from app.dependencies.forecast import get_forecast_service
from app.schemas.backtests import BacktestPayload, BacktestRunRequest
from app.services.auth_service import AuthenticatedUser
from app.services.forecast_service import ForecastService

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.post("/run")
def run_backtest(
    request: Request,
    payload: BacktestRunRequest,
    _: AuthenticatedUser = Depends(require_roles(*BACKTEST_RUN_ROLES)),
    forecast_service: ForecastService = Depends(get_forecast_service),
):
    try:
        result = forecast_service.run_backtest(
            product_code=payload.product_code,
            horizon_days=payload.horizon_days,
            window_type=payload.window_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc
    data = BacktestPayload(**result.data).model_dump(mode="json")
    return envelope(
        data=data,
        error=None,
        meta=build_generic_domain_meta(request, result.meta),
    )


@router.get("/latest")
def get_latest_backtest(
    request: Request,
    product_code: str = Query(..., min_length=1),
    horizon_days: int = Query(...),
    _: AuthenticatedUser = Depends(require_roles(*BACKTEST_READ_ROLES)),
    forecast_service: ForecastService = Depends(get_forecast_service),
):
    try:
        result = forecast_service.get_latest_backtest(
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
        data = BacktestPayload(**result.data).model_dump(mode="json")
    return envelope(
        data=data,
        error=None,
        meta=build_generic_domain_meta(request, result.meta),
    )
