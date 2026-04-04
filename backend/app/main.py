import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.responses import envelope, error_payload, request_meta

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["x-request-id"] = request_id
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
    body = envelope(
        data=None,
        error=error_payload(
            code="validation_error",
            message="Request validation failed",
            details={"errors": exc.errors()},
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
            details={"exception": exc.__class__.__name__},
        ),
        meta=request_meta(request),
    )
    return JSONResponse(status_code=500, content=body)


app.include_router(api_router)
