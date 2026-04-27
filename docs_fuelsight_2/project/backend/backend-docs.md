# Backend: FuelSight v2

## Назначение
Backend v2 сохраняет доменную разбивку MVP, но усиливает три направления:
- explainable analytics metadata;
- CatBoost-first model ops;
- real integrations with cache/fallback.

## Базовые ограничения
- single-station only;
- `/api/v1` сохраняется;
- envelope сохраняется: `{ data, error, meta }`;
- `admin` и `analyst` сохраняются;
- LLM и live providers не должны ломать core product.

## Архитектурная форма
- `frontend` SPA
- `backend` REST API
- `PostgreSQL`
- `Airflow`
- `ML module`
- `provider adapters` для news/indicators/LLM

## Доменная разбивка
- `auth`
- `imports`
- `kpi`
- `analytics`
- `forecasts`
- `backtests`
- `news`
- `chat`
- `pipeline`
- `integrations`:
  - external indicators adapters
  - news ingest adapters
  - LLM provider adapters

## New Durable Patterns
### Metadata-first responses
- Backend возвращает richer `meta` и auxiliary blocks, чтобы frontend не придумывал локальную логику.
- Особенно важно для:
  - chart annotations;
  - business explanations;
  - provider modes;
  - data/model freshness;
  - retrain status.

### CatBoost-first forecasting
- Active model per `product x horizon`.
- Seasonal Naive остаётся benchmark baseline.
- Winner selection, freshness и retrain cadence документируются и возвращаются через API.

### Hybrid integrations
- Live provider -> cache snapshot -> degraded status.
- Все adapters должны быть testable и возвращать явный mode.

### Provider-neutral LLM/RAG
- `chat` строится как `retrieval -> evidence pack -> synthesis -> verification -> answer`, без web search и autonomous agent loop.
- Первым cloud profile используется `NeuralDeep` через OpenAI-compatible adapter: chat, embeddings и reranker доступны за одним `base_url`.
- `GigaChat` остаётся альтернативным cloud adapter и не должен менять API contract.
- Provider-specific auth, request shape, retries and timeout logic живут внутри `backend/app/integrations/llm/*`.
- `retrieval_only` является полноценным mode, а не ошибкой: backend обязан вернуть cited answer, если retrieval нашёл evidence.
- Phase G baseline реализует retrieval-first contract и deterministic `retrieval_only` formatter без реальных cloud/local LLM вызовов.
- `chat_retrieval.py` собирает evidence pack из `news_raw`, `news_digests`, `kpi`, `analytics`, `forecast`; dense retrieval/rerank остаются Phase H.
- Cloud adapters получают только агрегированный evidence pack; raw fact tables, import files и user data не отправляются наружу.

### Analyst-first surface
- Технический provenance initial data скрывается с analyst-facing поверхностей.
- Admin-only diagnostics раскрывают источник, cache mode, quality issues и отчёты.

## Pipeline Responsibilities
- daily external indicators refresh;
- daily feature store refresh;
- weekly train/backtest;
- news refresh;
- defense report materialization.

## Observability
- structured JSON logs;
- pipeline run IDs;
- provider mode in logs and DB metadata;
- smoke-friendly machine-readable outputs.
