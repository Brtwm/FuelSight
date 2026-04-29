"""phase h advanced rag quality layer

Revision ID: 20260427_0008
Revises: 20260422_0007
Create Date: 2026-04-27 20:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260427_0008"
down_revision: str | None = "20260422_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column(
        "chat_sessions", sa.Column("running_summary", sa.String(length=2000), nullable=True)
    )
    op.add_column(
        "chat_messages",
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )
    op.execute(
        """
        CREATE TABLE rag_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_type VARCHAR(32) NOT NULL,
            source_id VARCHAR(255) NOT NULL,
            title TEXT NOT NULL,
            snippet TEXT,
            full_text_chunk TEXT NOT NULL,
            external_ref VARCHAR(255),
            provider_mode VARCHAR(32) NOT NULL,
            confidence FLOAT,
            embedding vector(64),
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            published_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.create_index("idx_rag_chunks_source", "rag_chunks", ["source_type", "source_id"])
    op.create_index("idx_rag_chunks_published_at", "rag_chunks", ["published_at"])
    op.create_index(
        "idx_rag_chunks_metadata",
        "rag_chunks",
        ["metadata_json"],
        postgresql_using="gin",
    )
    op.execute(
        """
        CREATE INDEX idx_rag_chunks_embedding_hnsw
        ON rag_chunks
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.drop_index("idx_rag_chunks_embedding_hnsw", table_name="rag_chunks")
    op.drop_index("idx_rag_chunks_metadata", table_name="rag_chunks")
    op.drop_index("idx_rag_chunks_published_at", table_name="rag_chunks")
    op.drop_index("idx_rag_chunks_source", table_name="rag_chunks")
    op.drop_table("rag_chunks")
    op.drop_column("chat_messages", "metadata_json")
    op.drop_column("chat_sessions", "running_summary")
