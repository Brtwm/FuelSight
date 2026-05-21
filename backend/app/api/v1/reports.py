from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.v1.meta_builders import build_generic_domain_meta
from app.core.responses import envelope
from app.core.roles import EXECUTIVE_REPORT_ROLES
from app.dependencies.auth import require_roles
from app.dependencies.reports import get_executive_report_service
from app.schemas.reports import ExecutiveReportPayload, ExecutiveReportRequest
from app.services.auth_service import AuthenticatedUser
from app.services.executive_report_service import ExecutiveReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/executive")
def build_executive_report(
    request: Request,
    payload: ExecutiveReportRequest | None = None,
    _: AuthenticatedUser = Depends(require_roles(*EXECUTIVE_REPORT_ROLES)),
    report_service: ExecutiveReportService = Depends(get_executive_report_service),
):
    payload = payload or ExecutiveReportRequest()
    try:
        result = report_service.build_report(
            date_from=payload.date_from,
            date_to=payload.date_to,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": str(exc)},
        ) from exc

    data = ExecutiveReportPayload(**result.data).model_dump(mode="json")
    return envelope(
        data=data,
        error=None,
        meta=build_generic_domain_meta(request, result.meta),
    )
