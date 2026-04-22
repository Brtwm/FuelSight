from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession, NewsRaw

_PRODUCT_CODE_PATTERN = re.compile(r"\b(AI_92|AI_95|DT_S|DT_W)\b", re.IGNORECASE)
_TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-я0-9_]{3,}")


class ChatService:
    def __init__(self, session: Session) -> None:
        self._session = session

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
                "citations": row.citations_json,
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

        user_message = ChatMessage(
            session_id=session.id,
            sender_type="user",
            message_text=normalized_question,
            citations_json=None,
            created_at=now,
        )
        self._session.add(user_message)

        citations = self._retrieve_citations(
            question=normalized_question,
            context_scope=context_scope,
        )
        if not citations:
            raise ValueError("citations are required for chat answer generation")

        answer = self._build_template_answer(question=normalized_question, citations=citations)
        assistant_message = ChatMessage(
            session_id=session.id,
            sender_type="assistant",
            message_text=answer,
            citations_json=citations,
            created_at=datetime.now(UTC),
        )
        self._session.add(assistant_message)
        session.updated_at = datetime.now(UTC)
        self._session.commit()

        return {
            "answer": answer,
            "citations": citations,
            "mode": "template_rag",
            "provider_mode": "local_llm",
        }

    def _require_session(self, *, user_id: UUID, session_id: UUID) -> ChatSession:
        row = self._session.scalar(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        if row is None:
            raise ValueError("chat_session_not_found")
        return row

    def _retrieve_citations(
        self,
        *,
        question: str,
        context_scope: list[str],
    ) -> list[dict[str, str]]:
        normalized_scope = {item.strip().lower() for item in context_scope if item and item.strip()}
        if not normalized_scope:
            normalized_scope = {"internal_analytics", "news_digest"}

        citations: list[dict[str, str]] = []
        if "news_digest" in normalized_scope:
            citations.extend(self._news_citations(question))
        if "internal_analytics" in normalized_scope:
            citations.extend(self._internal_analytics_citations(question))
        if "forecast" in normalized_scope:
            citations.extend(self._forecast_citations(question))

        deduped: list[dict[str, str]] = []
        seen_ref_ids: set[str] = set()
        for item in citations:
            ref_id = item["ref_id"]
            if ref_id in seen_ref_ids:
                continue
            deduped.append(item)
            seen_ref_ids.add(ref_id)
        return deduped[:5]

    def _news_citations(self, question: str) -> list[dict[str, str]]:
        tokens = [token.lower() for token in _TOKEN_PATTERN.findall(question)]
        tokens = [token for token in tokens if len(token) >= 3][:4]

        statement = select(NewsRaw).order_by(NewsRaw.published_at.desc()).limit(3)
        if tokens:
            conditions = []
            for token in tokens:
                pattern = f"%{token}%"
                conditions.extend(
                    [
                        NewsRaw.title.ilike(pattern),
                        NewsRaw.snippet.ilike(pattern),
                        NewsRaw.full_text.ilike(pattern),
                    ]
                )
            statement = statement.where(or_(*conditions)).limit(3)

        rows = list(self._session.scalars(statement))
        if not rows:
            rows = list(
                self._session.scalars(
                    select(NewsRaw).order_by(NewsRaw.published_at.desc()).limit(2)
                )
            )

        return [
            {
                "type": "news",
                "ref_id": row.external_ref or f"news_{row.id.hex[:12]}",
                "title": row.title,
                "provider_mode": row.provider_mode,
                "confidence": row.confidence,
                "source_type": "news_raw",
            }
            for row in rows
        ]

    def _internal_analytics_citations(self, question: str) -> list[dict[str, str]]:
        product_code = self._extract_product_code(question) or "AI_95"
        latest_margin_date = self._session.execute(
            text(
                """
                SELECT MAX(date)::date AS latest_date
                FROM vw_margin_daily
                WHERE product_code = :product_code
                """
            ),
            {"product_code": product_code},
        ).scalar_one_or_none()

        citations = [
            {
                "type": "chart",
                "ref_id": f"analytics_sales_{product_code}_latest",
                "title": f"Тренд продаж {product_code} (/analytics/sales)",
                "source_type": "internal_analytics",
            },
            {
                "type": "chart",
                "ref_id": f"analytics_margin_{product_code}_latest",
                "title": f"Динамика маржи {product_code} (/analytics/margin)",
                "source_type": "internal_analytics",
            },
        ]
        if latest_margin_date is not None:
            citations.append(
                {
                    "type": "chart",
                    "ref_id": f"kpi_snapshot_{product_code}_{latest_margin_date.isoformat()}",
                    "title": f"KPI snapshot {product_code} на {latest_margin_date.isoformat()}",
                    "source_type": "internal_analytics",
                }
            )
        return citations

    def _forecast_citations(self, question: str) -> list[dict[str, str]]:
        product_code = self._extract_product_code(question)
        row = self._session.execute(
            text(
                """
                SELECT p.code AS product_code, f.horizon_days
                FROM forecasts f
                JOIN products p ON p.id = f.product_id
                WHERE (:product_code IS NULL OR p.code = :product_code)
                ORDER BY f.created_at DESC
                LIMIT 1
                """
            ),
            {"product_code": product_code},
        ).mappings().first()

        if row is None:
            return [
                {
                    "type": "chart",
                    "ref_id": "forecast_latest",
                    "title": "Последний прогноз спроса (/forecast)",
                    "source_type": "forecast",
                }
            ]

        return [
            {
                "type": "chart",
                "ref_id": f"forecast_{row['product_code']}_{row['horizon_days']}_latest",
                "title": f"Прогноз {row['product_code']} на {row['horizon_days']} дней (/forecast)",
                "source_type": "forecast",
            }
        ]

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
    def _extract_product_code(text_value: str) -> str | None:
        matched = _PRODUCT_CODE_PATTERN.search(text_value)
        if matched is None:
            return None
        return matched.group(1).upper()
