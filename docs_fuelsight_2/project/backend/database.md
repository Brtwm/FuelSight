# FuelSight v2 Database Design

## Базовые принципы
- single-station only;
- факт-гранулярность core tables сохраняется как `day x product`;
- envelope и route compatibility не требуют радикальной перестройки схемы;
- новая таблица добавляется только там, где она реально нужна для v2.

## Core Tables
- `roles`
- `users`
- `products`
- `sales_daily`
- `purchases_daily`
- `import_jobs`

Эти таблицы концептуально не меняются.

## ML Tables
- `models`
- `forecasts`
- `backtest_runs`

### v2 semantics
- `models.metrics_json` хранит:
  - winner metrics;
  - baseline comparison;
  - residual stats;
  - feature source summary;
  - freshness metadata.
- `backtest_runs.metrics_json` хранит:
  - winner;
  - comparison;
  - folds;
  - retrain status;
  - provider modes if external data were used.

## NLP Tables
- `news_raw`
- `news_digests`
- `chat_sessions`
- `chat_messages`

### v2 semantics
- `news_digests.source_ids_json` ссылается только на реально сохранённые записи.
- `chat_messages.citations_json` расширяется полями:
  - `provider_mode`
  - `confidence`
  - `source_type`

## New Table: `external_indicators_daily`
```sql
CREATE TABLE external_indicators_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  indicator_date DATE NOT NULL,
  indicator_code VARCHAR(64) NOT NULL,
  value_numeric NUMERIC(18,6) NOT NULL,
  unit VARCHAR(32) NOT NULL,
  provider_name VARCHAR(64) NOT NULL,
  provider_mode VARCHAR(32) NOT NULL,
  cache_key VARCHAR(255),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (indicator_date, indicator_code, provider_name)
);
```

## Why Additional Tables Stay Limited
- `external_indicators_daily` нужен как стабильный мост между:
  - генератором initial data;
  - feature store;
  - forecast explanations;
  - chart reference overlays.
- Phase H добавляет `rag_chunks`, потому что пользователь выбрал `pgvector` для verified RAG quality layer.
- Остальные v2-расширения предпочтительно делать через existing JSON fields и service logic, чтобы не раздувать схему.

## New Table: `rag_chunks`
```sql
CREATE EXTENSION IF NOT EXISTS vector;

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
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

`rag_chunks` индексирует news/internal refs для retrieval. Таблица не меняет core grain `day x product` и не вводит `stations`.
Dense retrieval использует pgvector cosine operator и HNSW индекс:
```sql
CREATE INDEX idx_rag_chunks_embedding_hnsw
ON rag_chunks USING hnsw (embedding vector_cosine_ops);
```

## Scope Guardrails
- Не добавлять `stations`.
- Не переходить к multi-tenant схемам.
- Не хранить cloud credentials в БД.
