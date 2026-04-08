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

## Why Only One New Table
- `external_indicators_daily` нужен как стабильный мост между:
  - генератором initial data;
  - feature store;
  - forecast explanations;
  - chart reference overlays.
- Остальные v2-расширения предпочтительно делать через existing JSON fields и service logic, чтобы не раздувать схему.

## Scope Guardrails
- Не добавлять `stations`.
- Не переходить к multi-tenant схемам.
- Не хранить cloud credentials в БД.
