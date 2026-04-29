from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import ChatMessage, ChatSession
from app.services.chat_retrieval import ChatRetrievalService

_PRODUCT_CODE_PATTERN = re.compile(r"\b(AI_92|AI_95|DT_S|DT_W)\b", re.IGNORECASE)


class ChatService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._retrieval = ChatRetrievalService(session=session, settings=self._settings)

    def create_session(self, *, user_id: UUID, title: str) -> ChatSession:
        normalized_title = title.strip()
        if len(normalized_title) < 3:
            raise ValueError("title must be at least 3 characters")

        now = datetime.now(UTC)
        session = ChatSession(
            user_id=user_id,
            title=normalized_title,
            created_at=now,
            updated_at=now,
        )
        self._session.add(session)
        self._session.commit()
        self._session.refresh(session)
        return session

    def get_messages(self, *, user_id: UUID, session_id: UUID) -> list[dict[str, Any]]:
        session = self._require_session(user_id=user_id, session_id=session_id)
        rows = list(
            self._session.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.created_at.asc())
            )
        )
        return [
            {
                "id": row.id,
                "sender_type": row.sender_type,
                "message_text": row.message_text,
                "citations": self._normalize_stored_citations(row.citations_json),
                "confidence": (row.metadata_json or {}).get("confidence"),
                "verification": (row.metadata_json or {}).get("verification"),
                "created_at": row.created_at,
            }
            for row in rows
        ]

    def answer_question(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        question: str,
        context_scope: list[str],
    ) -> dict[str, Any]:
        normalized_question = question.strip()
        if len(normalized_question) < 3:
            raise ValueError("question must be at least 3 characters")

        session = self._require_session(user_id=user_id, session_id=session_id)
        now = datetime.now(UTC)

        query_context = self._retrieval.build_query_context(
            session_id=session.id,
            question=normalized_question,
        )
        user_message = ChatMessage(
            session_id=session.id,
            sender_type="user",
            message_text=normalized_question,
            citations_json=None,
            metadata_json={},
            created_at=now,
        )
        self._session.add(user_message)

        evidence_pack = self._retrieval.retrieve(
            query_context=query_context,
            context_scope=context_scope,
        )
        citations = evidence_pack.citations
        if not citations:
            answer = self._retrieval.format_uncertainty_answer(question=normalized_question)
            verification = {
                "status": "blocked",
                "reason": evidence_pack.diagnostics.degradation_reason or "evidence_not_found",
                "checked_claims": 0,
                "supported_claims": 0,
            }
            assistant_message = ChatMessage(
                session_id=session.id,
                sender_type="assistant",
                message_text=answer,
                citations_json=[],
                metadata_json={
                    "confidence": evidence_pack.confidence,
                    "verification": verification,
                },
                created_at=datetime.now(UTC),
            )
            self._session.add(assistant_message)
            session.updated_at = datetime.now(UTC)
            self._session.commit()
            return {
                "answer": answer,
                "citations": [],
                "mode": "retrieval_only",
                "provider_mode": "retrieval_only",
                "confidence": evidence_pack.confidence,
                "verification": verification,
                "llm_provider": {
                    "provider": "none",
                    "mode": "retrieval_only",
                    "degradation_reason": "evidence_not_found",
                },
                "retrieval": evidence_pack.diagnostics.to_payload(),
            }

        mode_resolution = self._retrieval.resolve_mode()
        answer = self._retrieval.format_retrieval_only_answer(
            question=normalized_question,
            evidence_pack=evidence_pack,
        )
        verification = self._retrieval.verify_answer_support(
            question=normalized_question,
            answer=answer,
            evidence_pack=evidence_pack,
        )
        if verification["status"] == "blocked":
            answer = self._retrieval.format_uncertainty_answer(question=normalized_question)
            citations = []
        assistant_message = ChatMessage(
            session_id=session.id,
            sender_type="assistant",
            message_text=answer,
            citations_json=citations,
            metadata_json={"confidence": evidence_pack.confidence, "verification": verification},
            created_at=datetime.now(UTC),
        )
        self._session.add(assistant_message)
        if verification["status"] == "verified":
            session.running_summary = self._build_running_summary(
                previous=getattr(session, "running_summary", None),
                question=normalized_question,
                answer=answer,
                citations=citations,
            )
        session.updated_at = datetime.now(UTC)
        self._session.commit()

        return {
            "answer": answer,
            "citations": citations,
            "mode": mode_resolution.mode,
            "provider_mode": mode_resolution.mode,
            "confidence": evidence_pack.confidence,
            "verification": verification,
            "llm_provider": mode_resolution.to_payload(),
            "retrieval": evidence_pack.diagnostics.to_payload(),
        }

    def _require_session(self, *, user_id: UUID, session_id: UUID) -> ChatSession:
        row = self._session.scalar(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        if row is None:
            raise ValueError("chat_session_not_found")
        return row

    @staticmethod
    def _build_template_answer(*, question: str, citations: list[dict[str, str]]) -> str:
        cited_titles = "; ".join(item["title"] for item in citations[:2])
        return (
            "По доступным внутренним данным и новостным материалам найдено несколько "
            "релевантных сигналов. Ключевые источники: "
            f"{cited_titles}. "
            "Проверьте указанные ссылки перед принятием решения по цене и закупке."
        )

    @staticmethod
    def _normalize_stored_citations(
        citations: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]] | None:
        if citations is None:
            return None
        normalized: list[dict[str, Any]] = []
        for item in citations:
            if not isinstance(item, dict):
                continue
            citation_type = str(item.get("type") or "chart").strip() or "chart"
            source_type = str(item.get("source_type") or citation_type).strip() or citation_type
            confidence = item.get("confidence")
            try:
                confidence_value = float(confidence) if confidence is not None else 0.6
            except (TypeError, ValueError):
                confidence_value = 0.6
            normalized.append(
                {
                    **item,
                    "type": citation_type,
                    "ref_id": str(item.get("ref_id") or "legacy_ref"),
                    "title": str(item.get("title") or item.get("ref_id") or "Источник"),
                    "provider_mode": item.get("provider_mode") or "retrieval_only",
                    "confidence": confidence_value,
                    "source_type": source_type,
                }
            )
        return normalized

    @staticmethod
    def _build_running_summary(
        *,
        previous: str | None,
        question: str,
        answer: str,
        citations: list[dict[str, Any]],
    ) -> str:
        refs = ", ".join(str(item.get("ref_id")) for item in citations[:3] if item.get("ref_id"))
        update = f"Q: {question[:180]} | A: {answer[:260]}"
        if refs:
            update = f"{update} | refs: {refs}"
        combined = " ".join([previous or "", update]).strip()
        return combined[-1800:]

    @staticmethod
    def _extract_product_code(text_value: str) -> str | None:
        matched = _PRODUCT_CODE_PATTERN.search(text_value)
        if matched is None:
            return None
        return matched.group(1).upper()
