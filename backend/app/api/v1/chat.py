from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.responses import envelope, request_meta
from app.dependencies.auth import require_roles
from app.dependencies.chat import get_chat_service
from app.schemas.chat import (
    ChatAnswerPayload,
    ChatAskRequest,
    ChatMessagePayload,
    ChatSessionCreateRequest,
    ChatSessionPayload,
)
from app.services.auth_service import AuthenticatedUser
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def _raise_for_service_error(exc: ValueError) -> None:
    if str(exc) == "chat_session_not_found":
        raise HTTPException(
            status_code=404,
            detail={"code": "http_error", "message": "Chat session not found"},
        ) from exc
    raise HTTPException(
        status_code=422,
        detail={"code": "validation_error", "message": str(exc)},
    ) from exc


@router.post("/sessions")
def create_session(
    request: Request,
    payload: ChatSessionCreateRequest,
    current_user: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        session = chat_service.create_session(user_id=current_user.id, title=payload.title)
    except ValueError as exc:
        _raise_for_service_error(exc)
    data = ChatSessionPayload(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )
    return envelope(data=data.model_dump(mode="json"), error=None, meta=request_meta(request))


@router.get("/sessions/{session_id}/messages")
def get_session_messages(
    request: Request,
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        rows = chat_service.get_messages(user_id=current_user.id, session_id=session_id)
    except ValueError as exc:
        _raise_for_service_error(exc)
    payload = [ChatMessagePayload(**item).model_dump(mode="json") for item in rows]
    return envelope(
        data=payload,
        error=None,
        meta={"count": len(payload), **request_meta(request)},
    )


@router.post("/sessions/{session_id}/messages")
def post_session_message(
    request: Request,
    session_id: UUID,
    payload: ChatAskRequest,
    current_user: AuthenticatedUser = Depends(require_roles("admin", "analyst")),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        result = chat_service.answer_question(
            user_id=current_user.id,
            session_id=session_id,
            question=payload.question,
            context_scope=payload.context_scope,
        )
    except ValueError as exc:
        _raise_for_service_error(exc)

    data = ChatAnswerPayload(**result).model_dump(mode="json")
    return envelope(
        data=data,
        error=None,
        meta={
            "llm_provider": result.get("llm_provider"),
            "retrieval": result.get("retrieval"),
            "verification": result.get("verification"),
            "confidence": result.get("confidence"),
            **request_meta(request),
        },
    )
