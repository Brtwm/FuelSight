from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.integrations.llm.contracts import LlmChatRequest
from app.integrations.llm.registry import resolve_llm_adapter
from app.models import ChatMessage, ChatSession
from app.services.chat_retrieval import ChatModeResolution, ChatRetrievalService, EvidencePack

_PRODUCT_CODE_PATTERN = re.compile(r"\b(AI_92|AI_95|DT_S|DT_W)\b", re.IGNORECASE)
_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_PATTERN = re.compile(r"(?:\+?\d[\s()\-]*){7,}")


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
            reason = evidence_pack.diagnostics.degradation_reason or "evidence_not_found"
            if reason == "unsupported_question":
                answer = ChatRetrievalService.format_out_of_domain_answer(
                    question=normalized_question
                )
                verification_reason = "out_of_domain_question"
            else:
                answer = self._retrieval.format_uncertainty_answer(question=normalized_question)
                verification_reason = reason
            verification = {
                "status": "blocked",
                "reason": verification_reason,
                "checked_claims": 0,
                "supported_claims": 0,
                "severity": "error",
                "unsupported_terms": [],
                "repair_attempted": False,
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
                    "degradation_reason": verification_reason,
                },
                "retrieval": evidence_pack.diagnostics.to_payload(),
            }

        mode_resolution = self._retrieval.resolve_mode()
        answer, mode_resolution = self._generate_answer(
            question=normalized_question,
            session=session,
            evidence_pack=evidence_pack,
        )
        verification = self._verify_answer_support(
            question=normalized_question,
            answer=answer,
            evidence_pack=evidence_pack,
            strict=mode_resolution.mode in {"cloud_llm", "local_llm"},
        )
        if mode_resolution.degradation_reason == "cloud_provider_unavailable":
            verification = {
                **verification,
                "status": "fallback_verified",
                "reason": "provider_unavailable",
                "severity": "warning",
                "unsupported_terms": verification.get("unsupported_terms") or [],
                "repair_attempted": False,
                "supported_claims": max(int(verification.get("supported_claims") or 0), 1),
            }
        elif verification["status"] == "blocked":
            answer, verification = self._repair_blocked_answer(
                question=normalized_question,
                evidence_pack=evidence_pack,
                verification=verification,
            )
            citations = evidence_pack.citations
            mode_resolution = ChatModeResolution(
                mode="retrieval_only",
                provider=mode_resolution.provider,
                model=mode_resolution.model,
                degradation_reason=verification.get("reason") or "verification_blocked",
            )
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

    def _generate_answer(
        self,
        *,
        question: str,
        session: ChatSession,
        evidence_pack: EvidencePack,
    ) -> tuple[str, ChatModeResolution]:
        mode_resolution = self._retrieval.resolve_mode()
        provider_failures: list[str] = []
        for candidate_resolution in [
            mode_resolution,
            *self._fallback_mode_resolutions(primary=mode_resolution),
        ]:
            if candidate_resolution.adapter is None or candidate_resolution.mode not in {
                "cloud_llm",
                "local_llm",
            }:
                continue
            try:
                result = candidate_resolution.adapter.chat(
                    LlmChatRequest(
                        question=question,
                        evidence_pack=self._build_sanitized_evidence_pack(evidence_pack),
                        citations=evidence_pack.citations,
                        running_summary=self._sanitize_running_summary(
                            getattr(session, "running_summary", None)
                        ),
                    )
                )
                if result.answer.strip():
                    normalized_answer = self._normalize_answer_text(result.answer)
                    return (
                        normalized_answer,
                        ChatModeResolution(
                            mode=result.mode,  # type: ignore[arg-type]
                            provider=result.provider,
                            adapter=candidate_resolution.adapter,
                            model=result.model,
                            degradation_reason=result.degradation_reason,
                        ),
                    )
            except Exception as exc:
                provider_failures.append(f"{candidate_resolution.provider}: {exc}")
        answer = self._retrieval.format_retrieval_only_answer(
            question=question,
            evidence_pack=evidence_pack,
        )
        if mode_resolution.mode != "retrieval_only" or provider_failures:
            mode_resolution = ChatModeResolution(
                mode="retrieval_only",
                provider=mode_resolution.provider,
                model=mode_resolution.model,
                degradation_reason="cloud_provider_unavailable"
                if provider_failures
                else mode_resolution.degradation_reason,
            )
        return answer, mode_resolution

    def _fallback_mode_resolutions(
        self, *, primary: ChatModeResolution
    ) -> list[ChatModeResolution]:
        provider = primary.provider.strip().lower()
        provider_mode = self._settings.llm_provider_mode.strip().lower()
        if (
            not self._settings.enable_llm
            or provider_mode != "cloud_first"
            or provider not in {"neuraldeep", "openai_compatible"}
            or not self._settings.gigachat_auth_key
        ):
            return []
        gigachat_settings = self._settings.model_copy(
            update={
                "llm_provider": "gigachat",
                "llm_provider_mode": "cloud_first",
            }
        )
        resolution = resolve_llm_adapter(gigachat_settings)
        if resolution.adapter is None or resolution.mode != "cloud_llm":
            return []
        return [
            ChatModeResolution(
                mode="cloud_llm",
                provider=resolution.provider,
                adapter=resolution.adapter,
                model=resolution.model,
            )
        ]

    def _repair_blocked_answer(
        self,
        *,
        question: str,
        evidence_pack: EvidencePack,
        verification: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        answer = self._retrieval.format_retrieval_only_answer(
            question=question,
            evidence_pack=evidence_pack,
        )
        reason = verification.get("reason")
        unsupported_terms = [
            str(item) for item in verification.get("unsupported_terms", []) if str(item)
        ]
        if reason == "unsupported_claim_terms":
            numeric_terms = [item for item in unsupported_terms if item.isdigit()]
            repaired_status = "fallback_verified" if numeric_terms else "repaired"
            repaired_reason = "unsupported_numeric_claim" if numeric_terms else reason
            return answer, {
                **verification,
                "status": repaired_status,
                "reason": repaired_reason,
                "severity": "warning",
                "unsupported_terms": unsupported_terms[:5],
                "repair_attempted": True,
                "supported_claims": max(int(verification.get("supported_claims") or 0), 1),
            }
        if reason == "weak_evidence" and evidence_pack.confidence >= 0.35:
            return answer, {
                **verification,
                "status": "fallback_verified",
                "severity": "warning",
                "unsupported_terms": unsupported_terms[:5],
                "repair_attempted": True,
            }
        return answer, {
            **verification,
            "severity": verification.get("severity") or "error",
            "unsupported_terms": unsupported_terms[:5],
            "repair_attempted": True,
        }

    @staticmethod
    def _build_sanitized_evidence_pack(evidence_pack: EvidencePack) -> dict[str, Any]:
        return {
            "items": [
                {
                    "title": item.citation.title,
                    "snippet": item.snippet,
                    "ref_id": item.citation.ref_id,
                    "source_type": item.citation.source_type,
                    "provider_mode": item.citation.provider_mode,
                    "confidence": item.citation.confidence,
                }
                for item in evidence_pack.selected
            ],
            "confidence": evidence_pack.confidence,
            "diagnostics": evidence_pack.diagnostics.to_payload(),
        }

    def _verify_answer_support(
        self,
        *,
        question: str,
        answer: str,
        evidence_pack: EvidencePack,
        strict: bool,
    ) -> dict[str, Any]:
        try:
            return self._retrieval.verify_answer_support(
                question=question,
                answer=answer,
                evidence_pack=evidence_pack,
                strict=strict,
            )
        except TypeError:
            return self._retrieval.verify_answer_support(
                question=question,
                answer=answer,
                evidence_pack=evidence_pack,
            )

    @staticmethod
    def _sanitize_running_summary(value: str | None) -> str | None:
        if not value:
            return None
        sanitized = _EMAIL_PATTERN.sub("[redacted-email]", value)
        sanitized = _PHONE_PATTERN.sub("[redacted-phone]", sanitized)
        return sanitized[-1200:]

    @staticmethod
    def _normalize_answer_text(value: str) -> str:
        normalized = value.strip()
        normalized = re.sub(r"\*\*(.*?)\*\*", r"\1", normalized)
        normalized = re.sub(r"__(.*?)__", r"\1", normalized)
        normalized = re.sub(r"(?m)^\s*[-*]\s+", "", normalized)
        normalized = re.sub(r"[ \t]+\n", "\n", normalized)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()

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
