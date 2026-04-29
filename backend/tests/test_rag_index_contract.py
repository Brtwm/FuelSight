from __future__ import annotations

from pathlib import Path


def test_phase_h_migration_enables_pgvector_and_creates_rag_chunks() -> None:
    migration = Path("alembic/versions/20260427_0008_phase_h_rag_quality.py").read_text(
        encoding="utf-8"
    )

    assert "CREATE EXTENSION IF NOT EXISTS vector" in migration
    assert "rag_chunks" in migration
    assert "embedding vector(" in migration
    assert "USING hnsw" in migration
    assert "vector_cosine_ops" in migration
    assert "source_type" in migration
    assert "source_id" in migration
