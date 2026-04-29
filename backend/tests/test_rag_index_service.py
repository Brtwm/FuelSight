from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.news_raw import NewsRaw
from app.models.rag_chunk import Vector
from app.services.chat_retrieval import DeterministicEmbeddingProvider
from app.services.rag_index_service import RagIndexService


def test_build_news_chunks_preserves_source_and_embedding_shape() -> None:
    row = NewsRaw(
        id=uuid4(),
        external_ref="gdelt_1",
        source_name="GDELT",
        provider_name="GDELT",
        provider_mode="cached",
        published_at=datetime(2026, 4, 5, 11, 0, tzinfo=UTC),
        title="Логистика влияет на дизель",
        url="https://example.local/news",
        snippet="Поставки дизеля замедлились.",
        full_text="Поставки дизеля замедлились. Закупочные цены растут из-за логистики.",
        language="ru",
        topic_tags=["logistics", "diesel"],
        impact_hint="purchase_up",
        confidence=0.72,
        cached_at=None,
        metadata_json={},
    )

    chunks = RagIndexService.build_news_raw_chunks([row])

    assert len(chunks) == 1
    assert chunks[0].source_type == "news_raw"
    assert chunks[0].source_id == "gdelt_1"
    assert chunks[0].provider_mode == "cached"
    assert len(chunks[0].embedding or []) == 64


def test_vector_type_serializes_python_lists_for_pgvector() -> None:
    vector = Vector(3)
    bind = vector.bind_processor(dialect=None)
    result = vector.result_processor(dialect=None, coltype=None)

    assert bind([0.1, 0.2, 0.3]) == "[0.10000000,0.20000000,0.30000000]"
    assert result("[0.10000000,0.20000000,0.30000000]") == [0.1, 0.2, 0.3]


def test_deterministic_embedding_provider_uses_stable_buckets() -> None:
    provider = DeterministicEmbeddingProvider()

    assert provider.embed("маржа дизель логистика") == provider.embed("маржа дизель логистика")
    assert provider.embed("маржа дизель логистика") != provider.embed("бензин спрос цена")
