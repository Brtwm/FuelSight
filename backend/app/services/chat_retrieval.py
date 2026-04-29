from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from hashlib import blake2b
from math import sqrt
from typing import Any, Literal

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import ChatMessage, ChatSession, NewsDigest, NewsRaw, RagChunk

ChatAnswerMode = Literal["cloud_llm", "local_llm", "retrieval_only"]
RetrievalScope = Literal["news_raw", "news_digests", "kpi", "analytics", "forecast"]

_TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-я0-9_]{3,}")
_PRODUCT_CODE_PATTERN = re.compile(r"\b(AI_92|AI_95|DT_S|DT_W)\b", re.IGNORECASE)
_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})\b")
_PRODUCT_ALIASES = {
    "аи 92": "AI_92",
    "аи-92": "AI_92",
    "ai 92": "AI_92",
    "ai-92": "AI_92",
    "92": "AI_92",
    "аи 95": "AI_95",
    "аи-95": "AI_95",
    "ai 95": "AI_95",
    "ai-95": "AI_95",
    "95": "AI_95",
    "дт лет": "DT_S",
    "дизель лет": "DT_S",
    "летний дизель": "DT_S",
    "дт зим": "DT_W",
    "дизель зим": "DT_W",
    "зимний дизель": "DT_W",
}
_DOMAIN_TERMS = {
    "топливо",
    "бензин",
    "дизель",
    "дт",
    "маржа",
    "закуп",
    "цена",
    "спрос",
    "продаж",
    "прогноз",
    "kpi",
    "алерт",
    "аномал",
    "риск",
    "логист",
    "нефт",
    "ai_92",
    "ai_95",
    "dt_s",
    "dt_w",
}
_SOURCE_PRIORITY = {
    "news_raw": 5,
    "news_digest": 4,
    "kpi": 3,
    "analytics": 3,
    "forecast": 2,
}
_DEFAULT_SCOPE_ALIASES: dict[str, tuple[RetrievalScope, ...]] = {
    "news_digest": ("news_digests",),
    "internal_analytics": ("kpi", "analytics"),
}


@dataclass(frozen=True)
class UnifiedCitation:
    type: str
    ref_id: str
    title: str
    provider_mode: str
    confidence: float
    source_type: str
    url: str | None = None
    published_at: str | None = None
    route_path: str | None = None
    snippet: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "type": self.type,
            "ref_id": self.ref_id,
            "title": self.title,
            "provider_mode": self.provider_mode,
            "confidence": round(max(min(self.confidence, 1.0), 0.0), 4),
            "source_type": self.source_type,
        }
        for key in ("url", "published_at", "route_path", "snippet"):
            value = getattr(self, key)
            if value:
                payload[key] = value
        return payload


@dataclass(frozen=True)
class EvidenceCandidate:
    citation: UnifiedCitation
    snippet: str
    score: float
    lexical_score: float = 0.0
    vector_score: float = 0.0
    freshness_score: float = 0.0
    domain_score: float = 0.0


@dataclass(frozen=True)
class RetrievalDiagnostics:
    candidate_count: int
    selected_count: int
    source_counts: dict[str, int]
    reranker_used: bool = False
    dense_used: bool = False
    query_rewritten: bool = False
    degradation_reason: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "candidate_count": self.candidate_count,
            "selected_count": self.selected_count,
            "source_counts": self.source_counts,
            "reranker_used": self.reranker_used,
            "dense_used": self.dense_used,
            "query_rewritten": self.query_rewritten,
            "degradation_reason": self.degradation_reason,
        }


@dataclass(frozen=True)
class EvidencePack:
    candidates: list[EvidenceCandidate]
    selected: list[EvidenceCandidate]
    diagnostics: RetrievalDiagnostics
    confidence: float = 0.0

    @property
    def citations(self) -> list[dict[str, Any]]:
        return [item.citation.to_payload() for item in self.selected]


@dataclass(frozen=True)
class ChatModeResolution:
    mode: ChatAnswerMode
    provider: str
    degradation_reason: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "mode": self.mode,
            "degradation_reason": self.degradation_reason,
        }


@dataclass(frozen=True)
class QueryContext:
    question: str
    normalized_text: str | None = None
    rewritten_text: str | None = None
    product_code: str | None = None
    date_from: str | None = None
    running_summary: str | None = None
    previous_user_messages: list[str] = field(default_factory=list)
    previous_citation_refs: list[str] = field(default_factory=list)

    @property
    def search_text(self) -> str:
        return " ".join(
            [
                self.rewritten_text or self.normalized_text or self.question,
                self.running_summary or "",
                *self.previous_user_messages,
                *self.previous_citation_refs,
            ]
        )


@dataclass(frozen=True)
class NormalizedQuery:
    original: str
    normalized_text: str
    rewritten_text: str
    product_code: str | None = None
    date_from: str | None = None


class QueryNormalizer:
    @staticmethod
    def normalize(question: str) -> NormalizedQuery:
        original = " ".join(question.strip().split())
        normalized_text = original.lower()
        product_code = _extract_product_code(normalized_text) or _extract_product_alias(
            normalized_text
        )
        date_from = _extract_date(normalized_text)
        rewritten_text = normalized_text
        if product_code:
            rewritten_text = _replace_product_alias(rewritten_text, product_code)
            if product_code not in rewritten_text:
                rewritten_text = f"{rewritten_text} {product_code}"
        return NormalizedQuery(
            original=original,
            normalized_text=normalized_text,
            rewritten_text=rewritten_text,
            product_code=product_code,
            date_from=date_from,
        )

    @staticmethod
    def context(question: str, *, running_summary: str | None = None) -> QueryContext:
        normalized = QueryNormalizer.normalize(question)
        return QueryContext(
            question=normalized.original,
            normalized_text=normalized.normalized_text,
            rewritten_text=normalized.rewritten_text,
            product_code=normalized.product_code,
            date_from=normalized.date_from,
            running_summary=running_summary,
        )


class DeterministicEmbeddingProvider:
    dimensions = 64

    def embed(self, text_value: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokens(text_value):
            digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest, byteorder="big") % self.dimensions
            vector[bucket] += 1.0
        norm = sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class ChatRetrievalService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def build_query_context(self, *, session_id: Any, question: str) -> QueryContext:
        running_summary = self._session.scalar(
            select(ChatSession.running_summary).where(ChatSession.id == session_id)
        )
        rows = list(
            self._session.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(8)
            )
        )
        previous_user_messages: list[str] = []
        previous_citation_refs: list[str] = []
        for row in rows:
            if row.sender_type == "user" and len(previous_user_messages) < 5:
                previous_user_messages.append(row.message_text)
            if row.sender_type == "assistant" and row.citations_json:
                for citation in row.citations_json[:5]:
                    ref_id = citation.get("ref_id") if isinstance(citation, dict) else None
                    if isinstance(ref_id, str) and ref_id:
                        previous_citation_refs.append(ref_id)
        normalized = QueryNormalizer.normalize(question)
        return QueryContext(
            question=normalized.original,
            normalized_text=normalized.normalized_text,
            rewritten_text=normalized.rewritten_text,
            product_code=normalized.product_code,
            date_from=normalized.date_from,
            running_summary=running_summary if isinstance(running_summary, str) else None,
            previous_user_messages=list(reversed(previous_user_messages)),
            previous_citation_refs=previous_citation_refs[:5],
        )

    def retrieve(self, *, query_context: QueryContext, context_scope: list[str]) -> EvidencePack:
        if not _is_supported_current_question(query_context):
            diagnostics = RetrievalDiagnostics(
                candidate_count=0,
                selected_count=0,
                source_counts={},
                degradation_reason="unsupported_question",
            )
            return EvidencePack(
                candidates=[],
                selected=[],
                diagnostics=diagnostics,
                confidence=0.0,
            )

        scopes = self._normalize_scopes(context_scope)
        candidates: list[EvidenceCandidate] = []
        if "news_raw" in scopes:
            candidates.extend(self._retrieve_news_raw(query_context))
        if "news_digests" in scopes:
            candidates.extend(self._retrieve_news_digests(query_context))
        if "kpi" in scopes:
            candidates.extend(self._retrieve_kpi(query_context))
        if "analytics" in scopes:
            candidates.extend(self._retrieve_analytics(query_context))
        if "forecast" in scopes:
            candidates.extend(self._retrieve_forecast(query_context))
        candidates.extend(self._retrieve_rag_chunks(query_context, scopes=scopes))

        selected = self._select_candidates(candidates)
        confidence = _evidence_confidence(selected)
        source_counts = Counter(item.citation.source_type for item in selected)
        diagnostics = RetrievalDiagnostics(
            candidate_count=len(candidates),
            selected_count=len(selected),
            source_counts=dict(source_counts),
            reranker_used=bool(candidates),
            dense_used=any(item.vector_score > 0 for item in selected),
            query_rewritten=(query_context.rewritten_text or "")
            != (query_context.normalized_text or ""),
            degradation_reason=None if selected else "evidence_not_found",
        )
        return EvidencePack(
            candidates=candidates,
            selected=selected,
            diagnostics=diagnostics,
            confidence=confidence,
        )

    def resolve_mode(self) -> ChatModeResolution:
        if not self._settings.enable_llm:
            return ChatModeResolution(
                mode="retrieval_only",
                provider="none",
                degradation_reason="llm_disabled",
            )

        provider_mode = self._settings.llm_provider_mode.strip().lower()
        if provider_mode == "cloud_first":
            return ChatModeResolution(
                mode="retrieval_only",
                provider="none",
                degradation_reason="cloud_adapter_not_configured",
            )
        if provider_mode == "local_only":
            return ChatModeResolution(
                mode="retrieval_only",
                provider="none",
                degradation_reason="local_adapter_not_configured",
            )
        return ChatModeResolution(mode="retrieval_only", provider="none")

    @staticmethod
    def format_retrieval_only_answer(*, question: str, evidence_pack: EvidencePack) -> str:
        selected = evidence_pack.selected
        if not selected:
            raise ValueError("citations are required for chat answer generation")

        primary = selected[0]
        secondary = selected[1] if len(selected) > 1 else None
        confidence = sum(item.citation.confidence for item in selected) / len(selected)
        confidence_text = (
            "данных недостаточно для уверенного вывода, но есть релевантные сигналы"
            if confidence < 0.55
            else "вывод можно использовать как предварительный ориентир"
        )
        answer_parts = [
            (
                "По найденным источникам главный сигнал: "
                f"{_clip_sentence(primary.snippet or primary.citation.title)}"
            )
        ]
        if secondary is not None:
            answer_parts.append(
                "Дополнительный источник указывает: "
                f"{_clip_sentence(secondary.snippet or secondary.citation.title)}"
            )
        answer_parts.append(
            f"Для вопроса «{_clip_sentence(question, max_len=140)}» {confidence_text}."
        )
        answer_parts.append("Проверьте приложенные источники перед изменением цены или закупки.")
        return " ".join(answer_parts)

    @staticmethod
    def format_uncertainty_answer(*, question: str) -> str:
        return (
            "По текущим данным недостаточно подтверждённых данных, чтобы ответить на этот "
            f"вопрос: «{_clip_sentence(question, max_len=140)}». "
            "Я не буду достраивать вывод без источников; уточните продукт, период "
            "или загрузите свежие данные."
        )

    @staticmethod
    def verify_answer_support(
        *,
        question: str,
        answer: str,
        evidence_pack: EvidencePack,
    ) -> dict[str, Any]:
        if not evidence_pack.selected:
            return {
                "status": "blocked",
                "reason": "evidence_not_found",
                "checked_claims": 0,
                "supported_claims": 0,
            }
        question_tokens = set(_tokens(question))
        answer_tokens = set(_tokens(answer))
        evidence_tokens: set[str] = set()
        for item in evidence_pack.selected:
            evidence_tokens.update(_tokens(f"{item.citation.title} {item.snippet}"))
        overlap = len((question_tokens | answer_tokens) & evidence_tokens)
        checked_claims = max(1, min(3, len(answer_tokens) // 8 or 1))
        supported_claims = min(checked_claims, overlap)
        if evidence_pack.confidence < 0.35 or supported_claims == 0:
            return {
                "status": "blocked",
                "reason": "weak_evidence",
                "checked_claims": checked_claims,
                "supported_claims": supported_claims,
            }
        return {
            "status": "verified",
            "reason": None,
            "checked_claims": checked_claims,
            "supported_claims": checked_claims,
        }

    @staticmethod
    def _normalize_scopes(context_scope: list[str]) -> set[RetrievalScope]:
        if not context_scope:
            return {"news_raw", "news_digests", "kpi", "analytics"}
        scopes: set[RetrievalScope] = set()
        allowed = {"news_raw", "news_digests", "kpi", "analytics", "forecast"}
        for item in context_scope:
            normalized = item.strip().lower()
            if normalized in allowed:
                scopes.add(normalized)  # type: ignore[arg-type]
            elif normalized in _DEFAULT_SCOPE_ALIASES:
                scopes.update(_DEFAULT_SCOPE_ALIASES[normalized])
        return scopes or {"news_raw", "news_digests", "kpi", "analytics"}

    def _retrieve_news_raw(self, query_context: QueryContext) -> list[EvidenceCandidate]:
        tokens = _tokens(query_context.search_text)[:6]
        statement = select(NewsRaw).order_by(NewsRaw.published_at.desc()).limit(8)
        if tokens:
            conditions = []
            for token in tokens:
                pattern = f"%{token}%"
                conditions.extend(
                    [
                        NewsRaw.title.ilike(pattern),
                        NewsRaw.snippet.ilike(pattern),
                        NewsRaw.full_text.ilike(pattern),
                        NewsRaw.external_ref.ilike(pattern),
                    ]
                )
            statement = statement.where(or_(*conditions)).limit(12)

        rows = list(self._session.scalars(statement))
        return [self._news_raw_candidate(row=row, tokens=tokens) for row in rows]

    def _retrieve_news_digests(self, query_context: QueryContext) -> list[EvidenceCandidate]:
        tokens = _tokens(query_context.search_text)[:6]
        rows = list(
            self._session.scalars(
                select(NewsDigest)
                .order_by(NewsDigest.digest_date.desc(), NewsDigest.created_at.desc())
                .limit(4)
            )
        )
        candidates: list[EvidenceCandidate] = []
        for row in rows:
            haystack = " ".join(
                [
                    row.summary_text,
                    *[str(item) for item in row.bullet_points_json],
                    *row.source_ids_json,
                ]
            )
            relevance = _lexical_score(haystack, tokens)
            if tokens and relevance <= 0:
                continue
            source_id = (
                row.source_ids_json[0] if row.source_ids_json else f"digest_{row.id.hex[:12]}"
            )
            linked_news = self._find_news_by_ref(source_id)
            provider_mode = (
                linked_news.provider_mode if linked_news is not None else "retrieval_only"
            )
            confidence = linked_news.confidence if linked_news is not None else 0.65
            candidates.append(
                EvidenceCandidate(
                    citation=UnifiedCitation(
                        type="digest",
                        ref_id=f"news_digest_{row.period_type}_{row.digest_date.isoformat()}",
                        title=f"Сводка новостей за {row.digest_date.isoformat()}",
                        provider_mode=provider_mode,
                        confidence=_confidence(confidence, relevance, row.digest_date),
                        source_type="news_digest",
                        route_path="/news",
                        snippet=row.summary_text,
                    ),
                    snippet=row.summary_text,
                    score=0.55 + relevance + _freshness_boost(row.digest_date),
                )
            )
        return candidates

    def _retrieve_kpi(self, query_context: QueryContext) -> list[EvidenceCandidate]:
        product_code = _extract_product_code(query_context.search_text)
        row = (
            self._session.execute(
                text(
                    """
                SELECT
                  MAX(v.date)::date AS latest_date,
                  SUM(v.volume_liters)::numeric AS volume_liters,
                  SUM(v.gross_margin_rub)::numeric AS gross_margin_rub,
                  AVG(v.gross_margin_rub_per_liter)::numeric AS gross_margin_rub_per_liter
                FROM vw_margin_daily v
                WHERE (CAST(:product_code AS VARCHAR) IS NULL OR v.product_code = :product_code)
                """
                ),
                {"product_code": product_code},
            )
            .mappings()
            .first()
        )
        if row is None or row["latest_date"] is None:
            return []
        title_product = product_code or "всем продуктам"
        volume_liters = float(row["volume_liters"] or 0)
        snippet = (
            f"KPI на {row['latest_date'].isoformat()}: продажи {volume_liters:.0f} л, "
            f"маржа {float(row['gross_margin_rub'] or 0):.0f} руб."
        )
        return [
            EvidenceCandidate(
                citation=UnifiedCitation(
                    type="kpi",
                    ref_id=f"kpi_summary_{product_code or 'all'}_{row['latest_date'].isoformat()}",
                    title=f"KPI summary по {title_product}",
                    provider_mode="retrieval_only",
                    confidence=0.82,
                    source_type="kpi",
                    route_path="/dashboard",
                    snippet=snippet,
                ),
                snippet=snippet,
                score=0.82,
            )
        ]

    def _retrieve_analytics(self, query_context: QueryContext) -> list[EvidenceCandidate]:
        product_code = (
            query_context.product_code
            or _extract_product_code(query_context.search_text)
            or "AI_95"
        )
        rows = (
            self._session.execute(
                text(
                    """
                SELECT
                  date::date AS date,
                  volume_liters,
                  avg_retail_price_rub,
                  avg_purchase_price_rub,
                  gross_margin_rub_per_liter
                FROM vw_margin_daily
                WHERE product_code = :product_code
                ORDER BY date DESC
                LIMIT 2
                """
                ),
                {"product_code": product_code},
            )
            .mappings()
            .all()
        )
        if not rows:
            return []
        latest = rows[0]
        previous = rows[1] if len(rows) > 1 else None
        volume_delta = None
        if previous is not None:
            volume_delta = float(latest["volume_liters"] or 0) - float(
                previous["volume_liters"] or 0
            )
        sales_snippet = (
            f"Последняя точка продаж {product_code}: {float(latest['volume_liters'] or 0):.0f} л "
            f"на {latest['date'].isoformat()}."
        )
        if volume_delta is not None:
            direction = (
                "рост" if volume_delta > 0 else "снижение" if volume_delta < 0 else "без изменения"
            )
            sales_snippet += f" День-к-дню: {direction} на {abs(volume_delta):.0f} л."
        margin_snippet = (
            f"Маржа {product_code}: {float(latest['gross_margin_rub_per_liter'] or 0):.2f} руб/л "
            f"на {latest['date'].isoformat()}."
        )
        return [
            EvidenceCandidate(
                citation=UnifiedCitation(
                    type="chart",
                    ref_id=f"analytics_sales_{product_code}_{latest['date'].isoformat()}",
                    title=f"Динамика продаж {product_code}",
                    provider_mode="retrieval_only",
                    confidence=0.78,
                    source_type="analytics",
                    route_path="/analytics/sales",
                    snippet=sales_snippet,
                ),
                snippet=sales_snippet,
                score=0.78,
            ),
            EvidenceCandidate(
                citation=UnifiedCitation(
                    type="chart",
                    ref_id=f"analytics_margin_{product_code}_{latest['date'].isoformat()}",
                    title=f"Динамика маржи {product_code}",
                    provider_mode="retrieval_only",
                    confidence=0.78,
                    source_type="analytics",
                    route_path="/analytics/margin",
                    snippet=margin_snippet,
                ),
                snippet=margin_snippet,
                score=0.78,
            ),
        ]

    def _retrieve_forecast(self, query_context: QueryContext) -> list[EvidenceCandidate]:
        product_code = query_context.product_code or _extract_product_code(
            query_context.search_text
        )
        row = (
            self._session.execute(
                text(
                    """
                    SELECT
                      p.code AS product_code,
                      f.horizon_days,
                      f.target_date,
                      f.y_hat,
                      f.y_lo,
                      f.y_hi,
                      f.scenario_name,
                      f.created_at
                    FROM forecasts f
                    JOIN products p ON p.id = f.product_id
                    WHERE (CAST(:product_code AS VARCHAR) IS NULL OR p.code = :product_code)
                    ORDER BY f.created_at DESC, f.target_date ASC
                    LIMIT 1
                    """
                ),
                {"product_code": product_code},
            )
            .mappings()
            .first()
        )
        if row is None:
            return []
        snippet = (
            f"Последний прогноз {row['product_code']} на {row['horizon_days']} дней: "
            f"{float(row['y_hat']):.0f} л на {row['target_date'].isoformat()}."
        )
        return [
            EvidenceCandidate(
                citation=UnifiedCitation(
                    type="forecast",
                    ref_id=f"forecast_{row['product_code']}_{row['horizon_days']}_latest",
                    title=f"Прогноз {row['product_code']} на {row['horizon_days']} дней",
                    provider_mode="retrieval_only",
                    confidence=0.72,
                    source_type="forecast",
                    route_path="/forecast",
                    snippet=snippet,
                ),
                snippet=snippet,
                score=0.72,
                lexical_score=_lexical_score(snippet, _tokens(query_context.search_text)),
            )
        ]

    def _retrieve_rag_chunks(
        self,
        query_context: QueryContext,
        *,
        scopes: set[RetrievalScope],
    ) -> list[EvidenceCandidate]:
        tokens = _tokens(query_context.search_text)[:8]
        if not tokens:
            return []
        allowed_source_types = {
            "news_raw"
            if scope == "news_raw"
            else "news_digest"
            if scope == "news_digests"
            else scope
            for scope in scopes
        }
        if not allowed_source_types:
            return []

        lexical_statement = select(RagChunk).where(
            RagChunk.source_type.in_(allowed_source_types)
        ).limit(20)
        conditions = []
        for token in tokens:
            pattern = f"%{token}%"
            conditions.extend(
                [
                    RagChunk.title.ilike(pattern),
                    RagChunk.snippet.ilike(pattern),
                    RagChunk.full_text_chunk.ilike(pattern),
                    RagChunk.external_ref.ilike(pattern),
                ]
            )
        query_vector = DeterministicEmbeddingProvider().embed(query_context.search_text)
        if conditions:
            lexical_statement = lexical_statement.where(or_(*conditions))
        rows = list(self._session.scalars(lexical_statement))
        rows.extend(
            self._retrieve_rag_chunks_by_vector(
                query_vector=query_vector,
                source_types=allowed_source_types,
            )
        )
        candidates: list[EvidenceCandidate] = []
        for row in rows:
            haystack = " ".join(
                [row.title, row.snippet or "", row.full_text_chunk, row.external_ref or ""]
            )
            lexical_score = _lexical_score(haystack, tokens)
            vector_score = _cosine(query_vector, row.embedding or [])
            freshness_score = _freshness_boost(row.published_at.date()) if row.published_at else 0.0
            domain_score = _domain_boost(haystack, tokens)
            score = (
                0.45 * lexical_score
                + 0.25 * vector_score
                + 0.15 * freshness_score
                + 0.15 * domain_score
                + min(float(row.confidence or 0.6), 1.0) * 0.2
            )
            if score <= 0.12:
                continue
            candidates.append(
                EvidenceCandidate(
                    citation=UnifiedCitation(
                        type=_citation_type_for_source(row.source_type),
                        ref_id=row.source_id,
                        title=row.title,
                        provider_mode=row.provider_mode,
                        confidence=max(min(float(row.confidence or 0.6), 1.0), 0.2),
                        source_type=row.source_type,
                        published_at=row.published_at.astimezone(UTC).isoformat()
                        if row.published_at
                        else None,
                        route_path=_route_for_source(row.source_type),
                        snippet=row.snippet or row.full_text_chunk,
                    ),
                    snippet=row.snippet or row.full_text_chunk,
                    score=score,
                    lexical_score=lexical_score,
                    vector_score=vector_score,
                    freshness_score=freshness_score,
                    domain_score=domain_score,
                )
            )
        return candidates

    def _retrieve_rag_chunks_by_vector(
        self,
        *,
        query_vector: list[float],
        source_types: set[str],
    ) -> list[RagChunk]:
        source_filter = ", ".join(f"'{item}'" for item in sorted(source_types))
        statement = select(RagChunk).from_statement(
            text(
                f"""
                SELECT *
                FROM rag_chunks
                WHERE source_type IN ({source_filter})
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> CAST(:query_embedding AS vector)
                LIMIT 20
                """
            )
        )
        return list(
            self._session.scalars(
                statement,
                {"query_embedding": _format_pgvector(query_vector)},
            )
        )

    def _news_raw_candidate(self, *, row: NewsRaw, tokens: list[str]) -> EvidenceCandidate:
        haystack = " ".join(
            [row.title, row.snippet or "", row.full_text or "", row.external_ref or ""]
        )
        relevance = _lexical_score(haystack, tokens)
        confidence = _confidence(row.confidence, relevance, row.published_at.date())
        ref_id = row.external_ref or f"news_{row.id.hex[:12]}"
        snippet = (row.snippet or row.full_text or row.title).strip()
        return EvidenceCandidate(
            citation=UnifiedCitation(
                type="news",
                ref_id=ref_id,
                title=row.title,
                provider_mode=row.provider_mode,
                confidence=confidence,
                source_type="news_raw",
                url=row.url,
                published_at=row.published_at.astimezone(UTC).isoformat(),
                route_path="/news",
                snippet=snippet,
            ),
            snippet=snippet,
            score=confidence + relevance + _freshness_boost(row.published_at.date()),
            lexical_score=relevance,
            freshness_score=_freshness_boost(row.published_at.date()),
            domain_score=_domain_boost(haystack, tokens),
        )

    def _find_news_by_ref(self, ref_id: str) -> NewsRaw | None:
        row = self._session.scalar(select(NewsRaw).where(NewsRaw.external_ref == ref_id).limit(1))
        if row is not None:
            return row
        if ref_id.startswith("news_"):
            prefix = ref_id.removeprefix("news_")
            return self._session.scalar(
                select(NewsRaw)
                .where(text("replace(id::text, '-', '') LIKE :prefix"))
                .params(prefix=f"{prefix}%")
            )
        return None

    @staticmethod
    def _select_candidates(candidates: list[EvidenceCandidate]) -> list[EvidenceCandidate]:
        deduped: dict[tuple[str, str], EvidenceCandidate] = {}
        for candidate in candidates:
            key = (candidate.citation.source_type, candidate.citation.ref_id)
            existing = deduped.get(key)
            if existing is None or candidate.score > existing.score:
                deduped[key] = candidate
        ranked = sorted(
            deduped.values(),
            key=lambda item: (
                item.score,
                _SOURCE_PRIORITY.get(item.citation.source_type, 0),
                item.citation.confidence,
            ),
            reverse=True,
        )
        selected: list[EvidenceCandidate] = []
        source_counts: Counter[str] = Counter()
        for item in ranked:
            if source_counts[item.citation.source_type] >= 3:
                continue
            selected.append(item)
            source_counts[item.citation.source_type] += 1
            if len(selected) >= 8:
                break
        return selected


def _tokens(text_value: str) -> list[str]:
    seen: set[str] = set()
    tokens: list[str] = []
    for token in _TOKEN_PATTERN.findall(text_value.lower()):
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def _extract_product_code(text_value: str) -> str | None:
    matched = _PRODUCT_CODE_PATTERN.search(text_value)
    if matched is None:
        return None
    return matched.group(1).upper()


def _extract_product_alias(text_value: str) -> str | None:
    compact = text_value.replace("_", " ").replace("-", " ")
    for alias, product_code in _PRODUCT_ALIASES.items():
        if alias in compact:
            return product_code
    return None


def _replace_product_alias(text_value: str, product_code: str) -> str:
    compact = text_value.replace("_", " ").replace("-", " ")
    for alias, alias_product_code in _PRODUCT_ALIASES.items():
        if alias_product_code == product_code and alias in compact:
            return compact.replace(alias, product_code, 1)
    return text_value


def _extract_date(text_value: str) -> str | None:
    matched = _DATE_PATTERN.search(text_value)
    if matched is None:
        return None
    value = matched.group(1)
    if "." in value:
        day, month, year = value.split(".")
        return f"{year}-{month}-{day}"
    return value


def _lexical_score(haystack: str, tokens: list[str]) -> float:
    if not tokens:
        return 0.05
    normalized = haystack.lower()
    matched = sum(1 for token in tokens if token in normalized)
    weighted = 0.0
    for token in tokens:
        occurrences = normalized.count(token)
        if occurrences:
            weighted += 1.0 + min(occurrences - 1, 3) * 0.2
    return min((matched + weighted) / max(len(tokens) * 2, 1), 1.0)


def _domain_boost(haystack: str, tokens: list[str]) -> float:
    normalized = haystack.lower()
    token_hits = sum(1 for token in tokens if any(term in token for term in _DOMAIN_TERMS))
    text_hits = sum(1 for term in _DOMAIN_TERMS if term in normalized)
    return min((token_hits + text_hits) / 6, 1.0)


def _is_supported_current_question(query_context: QueryContext) -> bool:
    current_text = " ".join(
        [
            query_context.rewritten_text or "",
            query_context.normalized_text or "",
            query_context.question,
        ]
    ).lower()
    if _extract_product_code(current_text):
        return True
    current_tokens = _tokens(current_text)
    return any(
        term in current_text or any(term in token for token in current_tokens)
        for term in _DOMAIN_TERMS
    )


def _freshness_boost(value: date) -> float:
    age_days = max((datetime.now(UTC).date() - value).days, 0)
    if age_days <= 3:
        return 0.12
    if age_days <= 14:
        return 0.08
    if age_days <= 45:
        return 0.03
    return 0.0


def _confidence(base: float | None, relevance: float, freshness_date: date) -> float:
    value = base if base is not None else 0.62
    return max(min(value + (relevance * 0.5) + _freshness_boost(freshness_date), 0.98), 0.2)


def _evidence_confidence(selected: list[EvidenceCandidate]) -> float:
    if not selected:
        return 0.0
    source_diversity = min(len({item.citation.source_type for item in selected}) / 3, 1.0)
    score_avg = sum(min(item.score, 1.0) for item in selected) / len(selected)
    citation_avg = sum(item.citation.confidence for item in selected) / len(selected)
    retrieval_avg = sum(
        min(item.lexical_score + item.vector_score + item.domain_score, 1.0) for item in selected
    ) / len(selected)
    return round(
        min(
            (0.4 * score_avg)
            + (0.3 * citation_avg)
            + (0.2 * retrieval_avg)
            + (0.1 * source_diversity),
            1.0,
        ),
        4,
    )


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = sqrt(sum(value * value for value in left[:size])) or 1.0
    right_norm = sqrt(sum(value * value for value in right[:size])) or 1.0
    return max(min(dot / (left_norm * right_norm), 1.0), 0.0)


def _format_pgvector(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(item):.8f}" for item in vector) + "]"


def _citation_type_for_source(source_type: str) -> str:
    if source_type == "news_raw":
        return "news"
    if source_type == "news_digest":
        return "digest"
    if source_type == "forecast":
        return "forecast"
    if source_type == "kpi":
        return "kpi"
    return "chart"


def _route_for_source(source_type: str) -> str:
    if source_type == "news_raw" or source_type == "news_digest":
        return "/news"
    if source_type == "forecast":
        return "/forecast"
    if source_type == "kpi":
        return "/dashboard"
    if source_type == "analytics":
        return "/analytics/sales"
    return "/news"


def _clip_sentence(value: str, *, max_len: int = 180) -> str:
    normalized = " ".join(value.strip().split())
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[: max_len - 3].rstrip()}..."
