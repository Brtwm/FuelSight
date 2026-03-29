"""Reusable response envelope helpers."""

from typing import Any

from fastapi import Request


def envelope(*, data: Any = None, error: dict[str, Any] | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "data": data,
        "error": error,
        "meta": meta or {},
    }


def request_meta(request: Request) -> dict[str, Any]:
    request_id = getattr(request.state, "request_id", None)
    return {"request_id": request_id} if request_id else {}
