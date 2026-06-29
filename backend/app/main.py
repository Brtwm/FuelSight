import uuid
from time import perf_counter

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging import (
    bind_request_id,
    get_logger,
    log_event,
    reset_request_id,
    setup_logging,
)
from app.core.responses import envelope, error_payload, request_meta

settings = get_settings()
setup_logging()
logger = get_logger("app.api")
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
    openapi_url="/openapi.json" if settings.enable_api_docs else None,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _internal_error_details(
    current_settings: Settings,
    exc: Exception,
) -> dict[str, str]:
    if current_settings.app_env.strip().lower() in {"local", "test"}:
        return {"exception": exc.__class__.__name__}
    return {}


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    token = bind_request_id(request_id)
    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        duration_ms = int((perf_counter() - started_at) * 1000)
        log_event(
            logger,
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
        )
        reset_request_id(token)
        raise

    duration_ms = int((perf_counter() - started_at) * 1000)
    log_event(
        logger,
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=status_code,
        duration_ms=duration_ms,
    )
    response.headers["x-request-id"] = request_id
    reset_request_id(token)
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_code = "http_error"
    details: dict[str, object] = {"status_code": exc.status_code}
    message = str(exc.detail)
    if isinstance(exc.detail, dict):
        error_code = str(exc.detail.get("code", "http_error"))
        message = str(exc.detail.get("message", "HTTP error"))
        provided_details = exc.detail.get("details")
        if isinstance(provided_details, dict):
            details |= provided_details
        elif provided_details is not None:
            details["reason"] = provided_details

    body = envelope(
        data=None,
        error=error_payload(
            code=error_code,
            message=message,
            details=details,
        ),
        meta=request_meta(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    error_code = "http_error"
    message = str(exc.detail)
    details: dict[str, object] = {"status_code": exc.status_code}
    if isinstance(exc.detail, dict):
        error_code = str(exc.detail.get("code", "http_error"))
        message = str(exc.detail.get("message", "HTTP error"))
        provided_details = exc.detail.get("details")
        if isinstance(provided_details, dict):
            details |= provided_details
        elif provided_details is not None:
            details["reason"] = provided_details

    body = envelope(
        data=None,
        error=error_payload(
            code=error_code,
            message=message,
            details=details,
        ),
        meta=request_meta(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    serializable_errors = [
        {key: value for key, value in item.items() if key != "ctx"}
        for item in exc.errors()
    ]
    body = envelope(
        data=None,
        error=error_payload(
            code="validation_error",
            message="Request validation failed",
            details={"errors": serializable_errors},
        ),
        meta=request_meta(request),
    )
    return JSONResponse(status_code=422, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    body = envelope(
        data=None,
        error=error_payload(
            code="internal_error",
            message="Internal server error",
            details=_internal_error_details(settings, exc),
        ),
        meta=request_meta(request),
    )
    return JSONResponse(status_code=500, content=body)


app.include_router(api_router)
