from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)

from app.core.database import SessionLocal
from app.core.responses import envelope, request_meta
from app.dependencies.auth import require_roles
from app.dependencies.imports import get_import_service
from app.schemas.imports import (
    GenerateDemoRequest,
    ImportJobDetails,
    ImportJobSummary,
    ImportQueuedResponse,
)
from app.services.auth_service import AuthenticatedUser
from app.services.import_service import GenerateDemoPayload, ImportEntityType, ImportService

router = APIRouter(prefix="/import", tags=["import"])


def _display_label_for_entity(entity_type: str) -> str:
    if entity_type == "sales":
        return "sales"
    if entity_type == "purchases":
        return "purchases"
    return "initial_history"


def _provenance_mode_for_source(source_type: str) -> str:
    if source_type in {"generated", "snapshot"}:
        return "manual_snapshot"
    return "manual_snapshot"


def _quality_status_for_job_status(status: str) -> str | None:
    if status == "completed":
        return "ok"
    if status == "completed_with_errors":
        return "warning"
    if status == "failed":
        return "failed"
    return None


def _detect_source_type(file_name: str | None) -> str:
    if not file_name:
        return "file"
    if "." not in file_name:
        return "file"
    ext = file_name.rsplit(".", maxsplit=1)[-1].strip().lower()
    return ext or "file"


def _process_file_job_in_background(
    *,
    job_id: UUID,
    entity_type: ImportEntityType,
    file_name: str,
    file_bytes: bytes,
    source_name: str | None,
) -> None:
    with SessionLocal() as session:
        service = ImportService(session)
        service.process_file_job(
            job_id=job_id,
            entity_type=entity_type,
            file_name=file_name,
            file_bytes=file_bytes,
            source_name=source_name,
        )


def _process_generate_demo_job_in_background(*, job_id: UUID, payload: dict[str, Any]) -> None:
    with SessionLocal() as session:
        service = ImportService(session)
        service.process_generate_demo_job(
            job_id=job_id,
            payload=GenerateDemoPayload(
                start_date=payload["start_date"],
                end_date=payload["end_date"],
                products=payload["products"],
                seed=payload["seed"],
                replace_existing=payload["replace_existing"],
            ),
        )


def _to_job_summary(job) -> ImportJobSummary:
    return ImportJobSummary(
        id=job.id,
        entity_type=job.entity_type,
        source_type=job.source_type,
        file_name=job.file_name,
        status=job.status,
        rows_total=job.rows_total,
        rows_success=job.rows_success,
        rows_failed=job.rows_failed,
        error_report_path=job.error_report_path,
        started_at=job.started_at,
        finished_at=job.finished_at,
        display_label=_display_label_for_entity(job.entity_type),
        provenance_mode=_provenance_mode_for_source(job.source_type),
        quality_status=_quality_status_for_job_status(job.status),
    )


@router.post("/sales", status_code=202)
async def upload_sales(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_name: str | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(require_roles("admin")),
    import_service: ImportService = Depends(get_import_service),
):
    file_name = file.filename or "sales_upload.csv"
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": "Файл пустой"},
        )

    job = import_service.create_job(
        entity_type="sales",
        source_type=_detect_source_type(file_name),
        file_name=file_name,
        started_by=current_user.id,
    )
    background_tasks.add_task(
        _process_file_job_in_background,
        job_id=job.id,
        entity_type="sales",
        file_name=file_name,
        file_bytes=file_bytes,
        source_name=source_name,
    )
    payload = ImportQueuedResponse(job_id=job.id, entity_type="sales", status="queued")
    payload.display_label = _display_label_for_entity("sales")
    payload.provenance_mode = _provenance_mode_for_source(_detect_source_type(file_name))
    return envelope(data=payload.model_dump(mode="json"), error=None, meta=request_meta(request))


@router.post("/purchases", status_code=202)
async def upload_purchases(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_name: str | None = Form(default=None),
    current_user: AuthenticatedUser = Depends(require_roles("admin")),
    import_service: ImportService = Depends(get_import_service),
):
    file_name = file.filename or "purchases_upload.csv"
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=422,
            detail={"code": "validation_error", "message": "Файл пустой"},
        )

    job = import_service.create_job(
        entity_type="purchases",
        source_type=_detect_source_type(file_name),
        file_name=file_name,
        started_by=current_user.id,
    )
    background_tasks.add_task(
        _process_file_job_in_background,
        job_id=job.id,
        entity_type="purchases",
        file_name=file_name,
        file_bytes=file_bytes,
        source_name=source_name,
    )
    payload = ImportQueuedResponse(job_id=job.id, entity_type="purchases", status="queued")
    payload.display_label = _display_label_for_entity("purchases")
    payload.provenance_mode = _provenance_mode_for_source(_detect_source_type(file_name))
    return envelope(data=payload.model_dump(mode="json"), error=None, meta=request_meta(request))


@router.post("/generate-demo", status_code=202)
def generate_demo(
    request: Request,
    payload: GenerateDemoRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(require_roles("admin")),
    import_service: ImportService = Depends(get_import_service),
):
    job = import_service.create_job(
        entity_type="historical_data",
        source_type="generated",
        file_name=None,
        started_by=current_user.id,
    )
    background_tasks.add_task(
        _process_generate_demo_job_in_background,
        job_id=job.id,
        payload=payload.model_dump(mode="python"),
    )
    response_payload = ImportQueuedResponse(
        job_id=job.id,
        entity_type="historical_data",
        status="queued",
    )
    response_payload.display_label = _display_label_for_entity("historical_data")
    response_payload.provenance_mode = _provenance_mode_for_source("generated")
    return envelope(
        data=response_payload.model_dump(mode="json"),
        error=None,
        meta=request_meta(request),
    )


@router.get("/jobs")
def list_jobs(
    request: Request,
    entity_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthenticatedUser = Depends(require_roles("admin")),
    import_service: ImportService = Depends(get_import_service),
):
    rows = import_service.list_jobs(entity_type=entity_type, status=status, limit=limit)
    payload = [_to_job_summary(row).model_dump(mode="json") for row in rows]
    return envelope(data=payload, error=None, meta=request_meta(request))


@router.get("/jobs/{job_id}")
def get_job_details(
    request: Request,
    job_id: UUID,
    _: AuthenticatedUser = Depends(require_roles("admin")),
    import_service: ImportService = Depends(get_import_service),
):
    row = import_service.get_job(job_id=job_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "http_error", "message": "Import job not found"},
        )
    payload = ImportJobDetails(
        **_to_job_summary(row).model_dump(mode="python"),
        started_by=row.started_by,
    )
    return envelope(data=payload.model_dump(mode="json"), error=None, meta=request_meta(request))
