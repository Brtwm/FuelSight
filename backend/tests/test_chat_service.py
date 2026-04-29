from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.config import Settings
from app.models.chat_message import ChatMessage
from app.services.chat_retrieval import (
    ChatRetrievalService,
    EvidenceCandidate,
    EvidencePack,
    QueryContext,
    QueryNormalizer,
    RetrievalDiagnostics,
    UnifiedCitation,
)
from app.services.chat_service import ChatService


def test_extract_product_code_from_question() -> None:
    assert ChatService._extract_product_code("Что с маржой AI_95 за март?") == "AI_95"
    assert ChatService._extract_product_code("Нужен обзор по продукту") is None


def test_template_answer_contains_citation_titles() -> None:
    answer = ChatService._build_template_answer(
        question="Что влияет на маржу?",
        citations=[
            {"type": "news", "ref_id": "n1", "title": "Новость 1"},
            {"type": "chart", "ref_id": "c1", "title": "График 1"},
        ],
    )
    assert "Новость 1" in answer
    assert "График 1" in answer


def test_retrieval_scope_aliases_preserve_legacy_names() -> None:
    scopes = ChatRetrievalService._normalize_scopes(
        ["news_digest", "internal_analytics", "forecast"]
    )

    assert scopes == {"news_digests", "kpi", "analytics", "forecast"}


def test_select_candidates_deduplicates_source_ref_pairs() -> None:
    candidates = [
        _candidate("news_raw", "shared", 0.4),
        _candidate("news_raw", "shared", 0.9),
        _candidate("analytics", "shared", 0.6),
        _candidate("forecast", "f1", 0.5),
    ]

    selected = ChatRetrievalService._select_candidates(candidates)

    assert [(item.citation.source_type, item.citation.ref_id) for item in selected] == [
        ("news_raw", "shared"),
        ("analytics", "shared"),
        ("forecast", "f1"),
    ]


def test_mode_resolver_degrades_to_retrieval_only_when_llm_disabled() -> None:
    service = ChatRetrievalService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(enable_llm=False),
    )

    mode = service.resolve_mode()

    assert mode.mode == "retrieval_only"
    assert mode.provider == "none"
    assert mode.degradation_reason == "llm_disabled"


def test_retrieval_only_answer_uses_evidence_and_citations() -> None:
    evidence_pack = EvidencePack(
        candidates=[],
        selected=[
            _candidate(
                "news_raw",
                "n1",
                0.8,
                snippet="Логистическая нагрузка повышает риск роста закупочных цен.",
            )
        ],
        diagnostics=RetrievalDiagnostics(
            candidate_count=1,
            selected_count=1,
            source_counts={"news_raw": 1},
        ),
    )

    answer = ChatRetrievalService.format_retrieval_only_answer(
        question="Почему выросла закупка?",
        evidence_pack=evidence_pack,
    )

    assert "По найденным источникам" in answer
    assert "Логистическая нагрузка" in answer
    assert evidence_pack.citations[0]["provider_mode"] == "retrieval_only"


def test_retrieval_only_answer_requires_citations() -> None:
    evidence_pack = EvidencePack(
        candidates=[],
        selected=[],
        diagnostics=RetrievalDiagnostics(
            candidate_count=0,
            selected_count=0,
            source_counts={},
            degradation_reason="evidence_not_found",
        ),
    )

    try:
        ChatRetrievalService.format_retrieval_only_answer(
            question="Почему выросла закупка?",
            evidence_pack=evidence_pack,
        )
    except ValueError as exc:
        assert str(exc) == "citations are required for chat answer generation"
    else:
        raise AssertionError("Expected ValueError for empty evidence pack")


def test_query_normalizer_maps_russian_product_alias_and_dates() -> None:
    normalized = QueryNormalizer.normalize("  Что с маржой дизель зимний за 05.04.2026?  ")

    assert normalized.original == "Что с маржой дизель зимний за 05.04.2026?"
    assert normalized.normalized_text == "что с маржой дизель зимний за 05.04.2026?"
    assert normalized.product_code == "DT_W"
    assert normalized.date_from == "2026-04-05"
    assert normalized.rewritten_text.startswith("что с маржой DT_W")


def test_news_raw_retrieval_does_not_fallback_to_latest_when_query_has_no_match() -> None:
    class FakeSession:
        def scalars(self, statement):  # noqa: ANN001
            compiled = str(statement)
            if "WHERE" in compiled:
                return []
            raise AssertionError("latest-news fallback query must not run for unmatched tokens")

    service = ChatRetrievalService(
        session=FakeSession(),  # type: ignore[arg-type]
        settings=Settings(enable_llm=False),
    )
    query_context = QueryNormalizer.context(question="расскажи про налоги на кофе")

    assert service._retrieve_news_raw(query_context) == []


def test_retrieval_blocks_out_of_domain_question_before_session_memory() -> None:
    class FakeSession:
        def scalars(self, statement):  # noqa: ANN001
            raise AssertionError("unsupported question must not query retrieval sources")

        def execute(self, statement, params=None):  # noqa: ANN001
            raise AssertionError("unsupported question must not query retrieval sources")

    service = ChatRetrievalService(
        session=FakeSession(),  # type: ignore[arg-type]
        settings=Settings(enable_llm=False),
    )
    query_context = QueryContext(
        question="Что с рынком кофе?",
        normalized_text="что с рынком кофе?",
        rewritten_text="что с рынком кофе?",
        previous_user_messages=["Почему изменилась маржа AI_95 за последние 14 дней?"],
        previous_citation_refs=["analytics_margin_AI_95_2026-04-29"],
    )

    evidence_pack = service.retrieve(
        query_context=query_context,
        context_scope=["news_raw", "internal_analytics", "forecast"],
    )

    assert evidence_pack.selected == []
    assert evidence_pack.diagnostics.degradation_reason == "unsupported_question"


def test_forecast_retrieval_handles_missing_product_code() -> None:
    class FakeResult:
        def mappings(self):  # noqa: ANN201
            return self

        def first(self):  # noqa: ANN201
            return {
                "product_code": "AI_95",
                "horizon_days": 7,
                "target_date": date(2026, 4, 30),
                "y_hat": 1200,
                "y_lo": 1100,
                "y_hi": 1300,
                "scenario_name": "base",
                "created_at": datetime(2026, 4, 29, tzinfo=UTC),
            }

    class FakeSession:
        def execute(self, statement, params):  # noqa: ANN001, ANN201
            compiled = str(statement)
            assert params == {"product_code": None}
            assert "CAST(:product_code AS VARCHAR) IS NULL" in compiled
            return FakeResult()

    service = ChatRetrievalService(
        session=FakeSession(),  # type: ignore[arg-type]
        settings=Settings(enable_llm=False),
    )
    query_context = QueryNormalizer.context(question="Что с прогнозом спроса?")

    candidates = service._retrieve_forecast(query_context)

    assert len(candidates) == 1
    assert candidates[0].citation.source_type == "forecast"
    assert candidates[0].citation.ref_id == "forecast_AI_95_7_latest"


def test_verification_blocks_unsupported_low_relevance_answer() -> None:
    evidence_pack = EvidencePack(
        candidates=[],
        selected=[_candidate("news_raw", "n1", 0.2, snippet="Новость о погоде.")],
        diagnostics=RetrievalDiagnostics(
            candidate_count=1,
            selected_count=1,
            source_counts={"news_raw": 1},
        ),
        confidence=0.22,
    )

    verification = ChatRetrievalService.verify_answer_support(
        question="Почему выросла закупка дизеля?",
        answer="Закупка дизеля выросла из-за логистики.",
        evidence_pack=evidence_pack,
    )

    assert verification["status"] == "blocked"
    assert verification["reason"] == "weak_evidence"


def test_answer_question_persists_uncertainty_response_when_evidence_is_missing() -> None:
    class FakeRetrieval:
        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return EvidencePack(
                candidates=[],
                selected=[],
                diagnostics=RetrievalDiagnostics(
                    candidate_count=0,
                    selected_count=0,
                    source_counts={},
                    degradation_reason="evidence_not_found",
                ),
                confidence=0.0,
            )

        def resolve_mode(self):
            return type(
                "Mode",
                (),
                {
                    "mode": "retrieval_only",
                    "to_payload": lambda self: {
                        "provider": "none",
                        "mode": "retrieval_only",
                        "degradation_reason": "llm_disabled",
                    },
                },
            )()

        @staticmethod
        def format_uncertainty_answer(*, question):
            return ChatRetrievalService.format_uncertainty_answer(question=question)

    class FakeSession:
        def __init__(self) -> None:
            self.added = []
            self.commits = 0

        def scalar(self, statement):  # noqa: ANN001
            return type("ChatSessionRow", (), {"id": "s1", "user_id": "u1", "updated_at": None})()

        def add(self, row):
            self.added.append(row)

        def commit(self):
            self.commits += 1

    session = FakeSession()
    service = ChatService(session=session, settings=Settings(enable_llm=False))  # type: ignore[arg-type]
    service._retrieval = FakeRetrieval()  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с рынком кофе?",
        context_scope=["news_raw"],
    )

    assert result["verification"]["status"] == "blocked"
    assert result["retrieval"]["selected_count"] == 0
    assert "недостаточно подтверждённых данных" in result["answer"]
    assert len([row for row in session.added if isinstance(row, ChatMessage)]) == 2
    assert session.commits == 1


def test_stored_legacy_citations_are_normalized_for_history() -> None:
    citations = ChatService._normalize_stored_citations(
        [{"type": "news", "ref_id": "legacy_1", "title": "Legacy source"}]
    )

    assert citations == [
        {
            "type": "news",
            "ref_id": "legacy_1",
            "title": "Legacy source",
            "provider_mode": "retrieval_only",
            "confidence": 0.6,
            "source_type": "news",
        }
    ]


def _candidate(
    source_type: str,
    ref_id: str,
    score: float,
    *,
    snippet: str = "Evidence snippet",
) -> EvidenceCandidate:
    return EvidenceCandidate(
        citation=UnifiedCitation(
            type="news" if source_type == "news_raw" else "chart",
            ref_id=ref_id,
            title=f"Title {ref_id}",
            provider_mode="retrieval_only",
            confidence=score,
            source_type=source_type,
            snippet=snippet,
        ),
        snippet=snippet,
        score=score,
        lexical_score=score,
    )
