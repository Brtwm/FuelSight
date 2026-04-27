from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any, Literal

from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import ChatMessage, NewsDigest, NewsRaw

ChatAnswerMode = Literal["cloud_llm", "local_llm", "retrieval_only"]
RetrievalScope = Literal["news_raw", "news_digests", "kpi", "analytics", "forecast"]

_TOKEN_PATTERN = re.compile(r"[A-Za-zА-Яа-я0-9_]{3,}")
_PRODUCT_CODE_PATTERN = re.compile(r"\b(AI_92|AI_95|DT_S|DT_W)\b", re.IGNORECASE)
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


@dataclass(frozen=True)
class RetrievalDiagnostics:
    candidate_count: int
    selected_count: int
    source_counts: dict[str, int]
    reranker_used: bool = False
    degradation_reason: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return {
            "candidate_count": self.candidate_count,
            "selected_count": self.selected_count,
            "source_counts": self.source_counts,
            "reranker_used": self.reranker_used,
            "degradation_reason": self.degradation_reason,
        }


@dataclass(frozen=True)
class EvidencePack:
    candidates: list[EvidenceCandidate]
    selected: list[EvidenceCandidate]
    diagnostics: RetrievalDiagnostics

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
    previous_user_messages: list[str] = field(default_factory=list)
    previous_citation_refs: list[str] = field(default_factory=list)

    @property
    def search_text(self) -> str:
        return " ".join([self.question, *self.previous_user_messages, *self.previous_citation_refs])


class ChatRetrievalService:
    def __init__(self, session: Session, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    def build_query_context(self, *, session_id: Any, question: str) -> QueryContext:
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
        return QueryContext(
            question=question,
            previous_user_messages=list(reversed(previous_user_messages)),
            previous_citation_refs=previous_citation_refs[:5],
        )

    def retrieve(self, *, query_context: QueryContext, context_scope: list[str]) -> EvidencePack:
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

        selected = self._select_candidates(candidates)
        source_counts = Counter(item.citation.source_type for item in selected)
        diagnostics = RetrievalDiagnostics(
            candidate_count=len(candidates),
            selected_count=len(selected),
            source_counts=dict(source_counts),
            degradation_reason=None if selected else "evidence_not_found",
        )
        return EvidencePack(candidates=candidates, selected=selected, diagnostics=diagnostics)

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
        if not rows:
            rows = list(
                self._session.scalars(select(NewsRaw).order_by(NewsRaw.published_at.desc()).limit(5))
            )
        return [self._news_raw_candidate(row=row, tokens=tokens) for row in rows]

    def _retrieve_news_digests(self, query_context: QueryContext) -> list[EvidenceCandidate]:
        tokens = _tokens(query_context.search_text)[:6]
        rows = list(
            self._session.scalars(
                select(NewsDigest).order_by(NewsDigest.digest_date.desc(), NewsDigest.created_at.desc()).limit(4)
            )
        )
        candidates: list[EvidenceCandidate] = []
        for row in rows:
            haystack = " ".join(
                [row.summary_text, *[str(item) for item in row.bullet_points_json], *row.source_ids_json]
            )
            relevance = _lexical_score(haystack, tokens)
            if tokens and relevance <= 0:
                continue
            source_id = row.source_ids_json[0] if row.source_ids_json else f"digest_{row.id.hex[:12]}"
            linked_news = self._find_news_by_ref(source_id)
            provider_mode = linked_news.provider_mode if linked_news is not None else "retrieval_only"
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
        row = self._session.execute(
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
        ).mappings().first()
        if row is None or row["latest_date"] is None:
            return []
        title_product = product_code or "всем продуктам"
        snippet = (
            f"KPI на {row['latest_date'].isoformat()}: продажи {float(row['volume_liters'] or 0):.0f} л, "
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
        product_code = _extract_product_code(query_context.search_text) or "AI_95"
        rows = self._session.execute(
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
        ).mappings().all()
        if not rows:
            return []
        latest = rows[0]
        previous = rows[1] if len(rows) > 1 else None
        volume_delta = None
        if previous is not None:
            volume_delta = float(latest["volume_liters"] or 0) - float(previous["volume_liters"] or 0)
        sales_snippet = (
            f"Последняя точка продаж {product_code}: {float(latest['volume_liters'] or 0):.0f} л "
            f"на {latest['date'].isoformat()}."
        )
        if volume_delta is not None:
            direction = "рост" if volume_delta > 0 else "снижение" if volume_delta < 0 else "без изменения"
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
        product_code = _extract_product_code(query_context.search_text)
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
                    WHERE (:product_code IS NULL OR p.code = :product_code)
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
            )
        ]

    def _news_raw_candidate(self, *, row: NewsRaw, tokens: list[str]) -> EvidenceCandidate:
        haystack = " ".join([row.title, row.snippet or "", row.full_text or "", row.external_ref or ""])
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
        )

    def _find_news_by_ref(self, ref_id: str) -> NewsRaw | None:
        row = self._session.scalar(select(NewsRaw).where(NewsRaw.external_ref == ref_id).limit(1))
        if row is not None:
            return row
        if ref_id.startswith("news_"):
            prefix = ref_id.removeprefix("news_")
            return self._session.scalar(
                select(NewsRaw).where(text("replace(id::text, '-', '') LIKE :prefix")).params(
                    prefix=f"{prefix}%"
                )
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
        return sorted(
            deduped.values(),
            key=lambda item: (
                item.score,
                _SOURCE_PRIORITY.get(item.citation.source_type, 0),
                item.citation.confidence,
            ),
            reverse=True,
        )[:8]


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


def _lexical_score(haystack: str, tokens: list[str]) -> float:
    if not tokens:
        return 0.05
    normalized = haystack.lower()
    matched = sum(1 for token in tokens if token in normalized)
    return min(matched / max(len(tokens), 1), 1.0) * 0.35


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


def _clip_sentence(value: str, *, max_len: int = 180) -> str:
    normalized = " ".join(value.strip().split())
    if len(normalized) <= max_len:
        return normalized
    return f"{normalized[: max_len - 3].rstrip()}..."
