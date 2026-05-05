from __future__ import annotations

from datetime import UTC, date, datetime

from app.core.config import Settings
from app.models.chat_message import ChatMessage
from app.services.chat_retrieval import (
    ChatModeResolution,
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


def test_retrieval_only_answer_explains_internal_and_external_factors() -> None:
    evidence_pack = EvidencePack(
        candidates=[],
        selected=[
            _candidate(
                "analytics",
                "analytics_sales_AI_95",
                0.78,
                snippet="Последняя точка продаж AI_95: 11766 л. День-к-дню: снижение на 876 л.",
            ),
            _candidate(
                "analytics",
                "analytics_margin_AI_95",
                0.78,
                snippet="Маржа AI_95: 12.38 руб/л на 2026-05-01.",
            ),
            _candidate(
                "kpi",
                "kpi_summary_AI_95",
                0.82,
                snippet="KPI на 2026-05-01: продажи 11376599 л, маржа 171220236 руб.",
            ),
            _candidate(
                "forecast",
                "forecast_AI_95_7_latest",
                0.72,
                snippet="Последний прогноз AI_95 на 7 дней: 9679 л на 2026-05-02.",
            ),
            _candidate(
                "news_raw",
                "news_iran_fuel_prices",
                0.86,
                snippet="Война в Иране привела к росту цен на бензин.",
            ),
        ],
        diagnostics=RetrievalDiagnostics(
            candidate_count=5,
            selected_count=5,
            source_counts={"analytics": 2, "kpi": 1, "forecast": 1, "news_raw": 1},
        ),
        confidence=0.79,
    )

    answer = ChatRetrievalService.format_retrieval_only_answer(
        question="С чем связано изменение цен на AI_95?",
        evidence_pack=evidence_pack,
    )

    assert "Короткий вывод" in answer
    assert "Внутренние факторы" in answer
    assert "Внешний фон" in answer
    assert "Прямая причинная связь" in answer
    assert "День-к-дню: снижение на 876 л" in answer
    assert "Война в Иране" in answer


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


def test_cloud_answer_verification_allows_neutral_bridge_terms() -> None:
    evidence_pack = EvidencePack(
        candidates=[],
        selected=[
            _candidate(
                "analytics",
                "analytics_margin_AI_95",
                0.9,
                snippet=(
                    "Маржа AI_95 12.38 руб/л. Закупочная цена выросла, "
                    "продажи AI_95 снизились."
                ),
            )
        ],
        diagnostics=RetrievalDiagnostics(
            candidate_count=1,
            selected_count=1,
            source_counts={"analytics": 1},
        ),
        confidence=0.84,
    )

    verification = ChatRetrievalService.verify_answer_support(
        question="Почему такая маржа на AI_95?",
        answer=(
            "Следовательно, наиболее вероятное влияние связано с закупочной "
            "ценой и продажами AI_95. Источник: analytics_margin_AI_95."
        ),
        evidence_pack=evidence_pack,
        strict=True,
    )

    assert verification["status"] == "verified"


def test_cloud_answer_verification_blocks_unsupported_material_terms() -> None:
    evidence_pack = _evidence_pack_for_chat()

    verification = ChatRetrievalService.verify_answer_support(
        question="Почему такая маржа на AI_95?",
        answer="Маржа AI_95 снизилась из-за пожара на НПЗ.",
        evidence_pack=evidence_pack,
        strict=True,
    )

    assert verification["status"] == "blocked"
    assert verification["reason"] == "unsupported_claim_terms"
    assert "пожара" in verification["unsupported_terms"]


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


def test_strict_verification_blocks_unsupported_numeric_claim() -> None:
    evidence_pack = _evidence_pack_for_chat()

    verification = ChatRetrievalService.verify_answer_support(
        question="Что с маржой AI_95?",
        answer="Маржа AI_95 снизилась на 1200 рублей из-за закупочной цены.",
        evidence_pack=evidence_pack,
        strict=True,
    )

    assert verification["status"] == "blocked"
    assert verification["reason"] == "unsupported_claim_terms"
    assert "1200" in verification["unsupported_terms"]


def test_strict_verification_allows_supported_russian_word_forms() -> None:
    evidence_pack = _evidence_pack_for_chat()

    verification = ChatRetrievalService.verify_answer_support(
        question="Что с маржой AI_95?",
        answer="Маржа AI_95 снизилась из-за закупочная цена.",
        evidence_pack=evidence_pack,
        strict=True,
    )

    assert verification["status"] == "verified"


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


def test_answer_question_returns_clear_out_of_domain_response() -> None:
    class FakeRetrieval:
        def __init__(self) -> None:
            self.resolve_mode_called = False

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
                    degradation_reason="unsupported_question",
                ),
                confidence=0.0,
            )

        def resolve_mode(self):
            self.resolve_mode_called = True
            raise AssertionError("out-of-domain question must not call LLM mode resolver")

    session = _fake_chat_session()
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    retrieval = FakeRetrieval()
    service._retrieval = retrieval  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Кто выиграет футбольный матч завтра?",
        context_scope=["news_raw", "internal_analytics"],
    )

    assert result["mode"] == "retrieval_only"
    assert result["provider_mode"] == "retrieval_only"
    assert result["citations"] == []
    assert result["verification"]["status"] == "blocked"
    assert result["verification"]["reason"] == "out_of_domain_question"
    assert "не относится к предметной области FuelSight" in result["answer"]
    assert retrieval.resolve_mode_called is False
    assert session.commits == 1


def test_answer_question_uses_cloud_adapter_after_evidence_is_found() -> None:
    class FakeAdapter:
        def chat(self, request):  # noqa: ANN001
            self.request = request
            return type(
                "Result",
                (),
                {
                    "answer": "Маржа AI_95 снизилась по подтверждённым источникам.",
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "usage": {"total_tokens": 12},
                    "degradation_reason": None,
                },
            )()

    class FakeRetrieval:
        def __init__(self) -> None:
            self.adapter = FakeAdapter()

        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=self.adapter,
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack):  # noqa: ANN001
            return {
                "status": "verified",
                "reason": None,
                "checked_claims": 1,
                "supported_claims": 1,
            }

    session = _fake_chat_session()
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    retrieval = FakeRetrieval()
    service._retrieval = retrieval  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert result["mode"] == "cloud_llm"
    assert result["provider_mode"] == "cloud_llm"
    assert result["answer"] == "Маржа AI_95 снизилась по подтверждённым источникам."
    assert result["llm_provider"]["provider"] == "neuraldeep"
    assert result["llm_provider"]["model"] == "gpt-oss-120b"
    assert "raw_table" not in str(retrieval.adapter.request.evidence_pack)


def test_answer_question_normalizes_cloud_markdown_to_plain_text() -> None:
    class FakeAdapter:
        def chat(self, request):  # noqa: ANN001
            return type(
                "Result",
                (),
                {
                    "answer": (
                        "**Вывод**: Маржа AI_95 снизилась из-за закупочной цены.\n\n"
                        "- Источник: analytics_margin_AI_95"
                    ),
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "usage": {},
                    "degradation_reason": None,
                },
            )()

    class FakeRetrieval:
        def __init__(self) -> None:
            self.adapter = FakeAdapter()

        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=self.adapter,
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack, strict=False):  # noqa: ANN001
            return ChatRetrievalService.verify_answer_support(
                question=question,
                answer=answer,
                evidence_pack=evidence_pack,
                strict=strict,
            )

    session = _fake_chat_session()
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    retrieval = FakeRetrieval()
    service._retrieval = retrieval  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert "**" not in result["answer"]
    assert "\n- " not in result["answer"]
    assert "Вывод: Маржа AI_95" in result["answer"]


def test_answer_question_sanitizes_running_summary_before_cloud_adapter() -> None:
    class FakeAdapter:
        def chat(self, request):  # noqa: ANN001
            self.request = request
            return type(
                "Result",
                (),
                {
                    "answer": "Маржа AI_95 снизилась из-за закупочной цены.",
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "usage": {},
                    "degradation_reason": None,
                },
            )()

    class FakeRetrieval:
        def __init__(self) -> None:
            self.adapter = FakeAdapter()

        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=self.adapter,
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.verify_answer_support(
                question=question,
                answer=answer,
                evidence_pack=evidence_pack,
            )

    session = _fake_chat_session(
        running_summary=(
            "Q: мой email user@example.com и телефон +7 999 111 22 33 | "
            "A: прошлый ответ по марже AI_95 | refs: analytics_margin_AI_95"
        )
    )
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    retrieval = FakeRetrieval()
    service._retrieval = retrieval  # type: ignore[assignment]

    service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert retrieval.adapter.request.running_summary is not None
    assert "user@example.com" not in retrieval.adapter.request.running_summary
    assert "+7 999 111 22 33" not in retrieval.adapter.request.running_summary
    assert "analytics_margin_AI_95" in retrieval.adapter.request.running_summary


def test_answer_question_repairs_cloud_answer_with_unsupported_reason() -> None:
    class FakeAdapter:
        def chat(self, request):  # noqa: ANN001
            return type(
                "Result",
                (),
                {
                    "answer": "Маржа AI_95 снизилась из-за новых акцизов.",
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "usage": {},
                    "degradation_reason": None,
                },
            )()

    class FakeRetrieval:
        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=FakeAdapter(),
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.verify_answer_support(
                question=question,
                answer=answer,
                evidence_pack=evidence_pack,
                strict=True,
            )

        @staticmethod
        def format_uncertainty_answer(*, question):
            return ChatRetrievalService.format_uncertainty_answer(question=question)

    session = _fake_chat_session()
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    service._retrieval = FakeRetrieval()  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert result["mode"] == "retrieval_only"
    assert result["verification"]["status"] == "repaired"
    assert result["verification"]["reason"] == "unsupported_claim_terms"
    assert result["verification"]["repair_attempted"] is True
    assert result["citations"]
    assert "По найденным источникам" in result["answer"]


def test_answer_question_repairs_cloud_answer_with_unsupported_terms() -> None:
    class FakeAdapter:
        def chat(self, request):  # noqa: ANN001
            return type(
                "Result",
                (),
                {
                    "answer": "Маржа AI_95 снизилась из-за новых акцизов.",
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "usage": {},
                    "degradation_reason": None,
                },
            )()

    class FakeRetrieval:
        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=FakeAdapter(),
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack, strict=False):  # noqa: ANN001
            return ChatRetrievalService.verify_answer_support(
                question=question,
                answer=answer,
                evidence_pack=evidence_pack,
                strict=strict,
            )

    session = _fake_chat_session()
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    service._retrieval = FakeRetrieval()  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert result["mode"] == "retrieval_only"
    assert result["verification"]["status"] == "repaired"
    assert result["verification"]["reason"] == "unsupported_claim_terms"
    assert result["verification"]["severity"] == "warning"
    assert result["verification"]["repair_attempted"] is True
    assert result["verification"]["unsupported_terms"] == ["акцизов"]
    assert "акциз" not in result["answer"].lower()
    assert "Подтверждено внутренними данными" in result["answer"]


def test_answer_question_returns_fallback_verified_for_invented_number() -> None:
    class FakeAdapter:
        def chat(self, request):  # noqa: ANN001
            return type(
                "Result",
                (),
                {
                    "answer": "Маржа AI_95 снизилась на 1200 рублей из-за закупочной цены.",
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "usage": {},
                    "degradation_reason": None,
                },
            )()

    class FakeRetrieval:
        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=FakeAdapter(),
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack, strict=False):  # noqa: ANN001
            return ChatRetrievalService.verify_answer_support(
                question=question,
                answer=answer,
                evidence_pack=evidence_pack,
                strict=strict,
            )

    session = _fake_chat_session()
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    service._retrieval = FakeRetrieval()  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert result["mode"] == "retrieval_only"
    assert result["verification"]["status"] == "fallback_verified"
    assert result["verification"]["reason"] == "unsupported_numeric_claim"
    assert result["verification"]["severity"] == "warning"
    assert result["verification"]["repair_attempted"] is True
    assert result["verification"]["unsupported_terms"] == ["1200"]
    assert "1200" not in result["answer"]


def test_answer_question_falls_back_to_retrieval_only_when_cloud_adapter_fails() -> None:
    class FailingAdapter:
        def chat(self, request):  # noqa: ANN001
            raise RuntimeError("provider timeout")

    class FakeRetrieval:
        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=FailingAdapter(),
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack):  # noqa: ANN001
            return {
                "status": "verified",
                "reason": None,
                "checked_claims": 1,
                "supported_claims": 1,
            }

    session = _fake_chat_session()
    service = ChatService(session=session, settings=Settings(enable_llm=True))  # type: ignore[arg-type]
    service._retrieval = FakeRetrieval()  # type: ignore[assignment]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert result["mode"] == "retrieval_only"
    assert result["provider_mode"] == "retrieval_only"
    assert result["verification"]["status"] == "fallback_verified"
    assert result["verification"]["reason"] == "provider_unavailable"
    assert result["verification"]["severity"] == "warning"
    assert result["llm_provider"]["provider"] == "neuraldeep"
    assert result["llm_provider"]["degradation_reason"] == "cloud_provider_unavailable"
    assert "По найденным источникам" in result["answer"]


def test_answer_question_uses_gigachat_fallback_when_primary_cloud_adapter_fails() -> None:
    class FailingAdapter:
        def chat(self, request):  # noqa: ANN001
            raise RuntimeError("provider timeout")

    class GigaChatFallbackAdapter:
        def chat(self, request):  # noqa: ANN001
            self.request = request
            return type(
                "Result",
                (),
                {
                    "answer": "GigaChat подтвердил вывод по источникам.",
                    "provider": "gigachat",
                    "mode": "cloud_llm",
                    "model": "GigaChat",
                    "usage": {},
                    "degradation_reason": None,
                },
            )()

    class FakeRetrieval:
        def build_query_context(self, *, session_id, question):  # noqa: ANN001
            return QueryNormalizer.context(question=question)

        def retrieve(self, *, query_context, context_scope):  # noqa: ANN001
            return _evidence_pack_for_chat()

        def resolve_mode(self):
            return ChatModeResolution(
                mode="cloud_llm",
                provider="neuraldeep",
                adapter=FailingAdapter(),
                model="gpt-oss-120b",
            )

        @staticmethod
        def format_retrieval_only_answer(*, question, evidence_pack):  # noqa: ANN001
            return ChatRetrievalService.format_retrieval_only_answer(
                question=question,
                evidence_pack=evidence_pack,
            )

        @staticmethod
        def verify_answer_support(*, question, answer, evidence_pack, strict=False):  # noqa: ANN001
            return {
                "status": "verified",
                "reason": None,
                "checked_claims": 1,
                "supported_claims": 1,
                "severity": "info",
                "unsupported_terms": [],
                "repair_attempted": False,
            }

    fallback_adapter = GigaChatFallbackAdapter()
    session = _fake_chat_session()
    service = ChatService(
        session=session,
        settings=Settings(
            enable_llm=True,
            llm_provider_mode="cloud_first",
            llm_provider="neuraldeep",
            llm_api_key="neuraldeep-key",
            gigachat_auth_key="gigachat-key",
        ),
    )  # type: ignore[arg-type]
    service._retrieval = FakeRetrieval()  # type: ignore[assignment]

    def fallback_resolutions(primary):  # noqa: ANN001
        return [
            ChatModeResolution(
                mode="cloud_llm",
                provider="gigachat",
                adapter=fallback_adapter,  # type: ignore[arg-type]
                model="GigaChat",
            )
        ]

    service._fallback_mode_resolutions = fallback_resolutions  # type: ignore[method-assign]

    result = service.answer_question(
        user_id="u1",  # type: ignore[arg-type]
        session_id="s1",  # type: ignore[arg-type]
        question="Что с маржой AI_95?",
        context_scope=["analytics"],
    )

    assert result["mode"] == "cloud_llm"
    assert result["provider_mode"] == "cloud_llm"
    assert result["answer"] == "GigaChat подтвердил вывод по источникам."
    assert result["llm_provider"]["provider"] == "gigachat"
    assert result["llm_provider"]["model"] == "GigaChat"


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


def _evidence_pack_for_chat() -> EvidencePack:
    return EvidencePack(
        candidates=[],
        selected=[
            _candidate(
                "analytics",
                "analytics_margin_AI_95",
                0.9,
                snippet="Маржа AI_95 снизилась из-за закупочной цены.",
            )
        ],
        diagnostics=RetrievalDiagnostics(
            candidate_count=1,
            selected_count=1,
            source_counts={"analytics": 1},
        ),
        confidence=0.84,
    )


def _fake_chat_session(running_summary: str = ""):
    class FakeSession:
        def __init__(self) -> None:
            self.added = []
            self.commits = 0

        def scalar(self, statement):  # noqa: ANN001
            return type(
                "ChatSessionRow",
                (),
                {
                    "id": "s1",
                    "user_id": "u1",
                    "running_summary": running_summary,
                    "updated_at": None,
                },
            )()

        def add(self, row):
            self.added.append(row)

        def commit(self):
            self.commits += 1

    return FakeSession()
