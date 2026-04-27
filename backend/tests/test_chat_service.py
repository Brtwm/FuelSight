from __future__ import annotations

from app.core.config import Settings
from app.services.chat_service import ChatService
from app.services.chat_retrieval import (
    ChatRetrievalService,
    EvidenceCandidate,
    EvidencePack,
    RetrievalDiagnostics,
    UnifiedCitation,
)


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
    )
