from __future__ import annotations

from collections.abc import Iterable

from app.core.config import get_settings
from app.integrations.llm.registry import resolve_llm_adapter
from app.models import NewsDigest, NewsRaw, RagChunk
from app.services.chat_retrieval import DeterministicEmbeddingProvider


class RagIndexService:
    _embedding_provider = DeterministicEmbeddingProvider()

    @classmethod
    def _embed(cls, text_value: str) -> list[float]:
        resolution = resolve_llm_adapter(get_settings())
        if resolution.adapter is not None:
            try:
                result = resolution.adapter.embed_texts([text_value])
                if result.vectors:
                    return result.vectors[0]
            except Exception:
                pass
        return cls._embedding_provider.embed(text_value)

    @classmethod
    def build_news_raw_chunks(cls, rows: Iterable[NewsRaw]) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for row in rows:
            source_id = row.external_ref or f"news_{row.id.hex[:12]}"
            text = cls._chunk_text(row.full_text or row.snippet or row.title)
            chunks.append(
                RagChunk(
                    source_type="news_raw",
                    source_id=source_id,
                    title=row.title,
                    snippet=row.snippet,
                    full_text_chunk=text,
                    external_ref=row.external_ref,
                    provider_mode=row.provider_mode,
                    confidence=row.confidence,
                    embedding=cls._embed(f"{row.title} {row.snippet or ''} {text}"),
                    metadata_json={
                        "url": row.url,
                        "topic_tags": row.topic_tags,
                        "provider_name": row.provider_name,
                    },
                    published_at=row.published_at,
                )
            )
        return chunks

    @classmethod
    def build_news_digest_chunks(cls, rows: Iterable[NewsDigest]) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for row in rows:
            source_id = f"news_digest_{row.period_type}_{row.digest_date.isoformat()}"
            text = cls._chunk_text(
                " ".join([row.summary_text, *[str(item) for item in row.bullet_points_json]])
            )
            chunks.append(
                RagChunk(
                    source_type="news_digest",
                    source_id=source_id,
                    title=f"Сводка новостей за {row.digest_date.isoformat()}",
                    snippet=row.summary_text,
                    full_text_chunk=text,
                    external_ref=source_id,
                    provider_mode="retrieval_only",
                    confidence=0.65,
                    embedding=cls._embed(text),
                    metadata_json={"source_ids": row.source_ids_json},
                    published_at=None,
                )
            )
        return chunks

    @staticmethod
    def _chunk_text(text_value: str, *, max_chars: int = 900) -> str:
        normalized = " ".join(text_value.strip().split())
        if len(normalized) <= max_chars:
            return normalized
        return normalized[:max_chars].rsplit(" ", 1)[0]
