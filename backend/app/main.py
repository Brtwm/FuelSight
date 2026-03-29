import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.responses import envelope, request_meta

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    body = envelope(
        data=None,
        error={
            "code": "http_error",
            "message": str(exc.detail),
            "details": {"status_code": exc.status_code},
        },
        meta=request_meta(request),
    )
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    body = envelope(
        data=None,
        error={
            "code": "internal_error",
            "message": "Internal server error",
            "details": {"exception": exc.__class__.__name__},
        },
        meta=request_meta(request),
    )
    return JSONResponse(status_code=500, content=body)


app.include_router(api_router)
