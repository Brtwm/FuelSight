from __future__ import annotations

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


def test_retrieve_citations_deduplicates_ref_ids() -> None:
    service = ChatService(session=None)  # type: ignore[arg-type]
    service._news_citations = lambda _question: [  # type: ignore[method-assign]
        {"type": "news", "ref_id": "shared", "title": "Shared"},
        {"type": "news", "ref_id": "n2", "title": "N2"},
    ]
    service._internal_analytics_citations = lambda _question: [  # type: ignore[method-assign]
        {"type": "chart", "ref_id": "shared", "title": "Shared chart"},
        {"type": "chart", "ref_id": "c2", "title": "C2"},
    ]
    service._forecast_citations = lambda _question: [  # type: ignore[method-assign]
        {"type": "chart", "ref_id": "c3", "title": "C3"}
    ]

    citations = service._retrieve_citations(
        question="Факторы спроса",
        context_scope=["news_digest", "internal_analytics", "forecast"],
    )

    ref_ids = [item["ref_id"] for item in citations]
    assert ref_ids.count("shared") == 1
    assert "n2" in ref_ids and "c2" in ref_ids and "c3" in ref_ids
