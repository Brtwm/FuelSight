# Tech Context

## Main Stack
- Frontend: `React 19 + Vite 8 + TypeScript 5.9 + MUI 7 + Apache ECharts 6 + React Router 7 + TanStack Query 5 + React Hook Form + Zod`
- Backend: `Python 3.12 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + PostgreSQL`
- Pipelines: `Airflow`
- ML: `CatBoost` primary, `Seasonal Naive` baseline/fallback
- Tooling: `uv`, `corepack pnpm`, `pytest`, `vitest`, `Playwright`

## Ports And Runtime
- Frontend dev: `3000`
- Backend dev: `8061`
- PostgreSQL: `5432`
- Airflow webserver: `8080`
- Backend package entrypoints:
  - `fuelsight-seed-core`
  - `fuelsight-pipeline`

## Important Environment Rules
- `ENABLE_LLM=false` остаётся безопасным и поддерживаемым режимом.
- Core flow должен работать без LLM и без обязательного внешнего интернета.
- Для non-`local`/`test` окружений backend требует `JWT_SECRET_KEY` длиной не меньше `32`.
- Для текущего data/pipeline baseline важны флаги:
  - `ENABLE_EXTERNAL_INDICATORS`
  - `EXTERNAL_INDICATORS_MODE`
  - `EXTERNAL_CACHE_DIR`
  - `LLM_PROVIDER`
  - `LLM_PROVIDER_MODE`
  - `LLM_OPENAI_COMPAT_BASE_URL`
  - `LLM_API_KEY`
  - `LLM_CHAT_MODEL`
  - `LLM_EMBEDDING_MODEL`
  - `LLM_RERANKER_MODEL`
  - `DEFENSE_MODE`
  - `DEFENSE_PROFILE`

## LLM/RAG Provider Direction
- First cloud-enhanced demo provider: `NeuralDeep` through OpenAI-compatible API.
- Alternative cloud adapter: `GigaChat`.
- Required safety fallback: `retrieval_only`.
- Cloud providers receive only aggregated evidence packs with citations, not raw operational tables or user data.
- Current Phase G runtime is retrieval-first: `backend/app/services/chat_retrieval.py` builds evidence packs and deterministic `retrieval_only` answers; real cloud/local LLM calls are still future Phase I work.
- Current Phase H worktree adds pgvector-backed `rag_chunks`, deterministic local embeddings, retrieval confidence, final verification metadata, and blocked uncertainty responses.
- `ENABLE_LLM=false` is expected to keep chat usable through cited retrieval-only answers when evidence exists.

## Current Repo Layout
- `frontend/` — SPA, shared UI primitives, route pages, feature modules
- `backend/app/api/v1/` — REST endpoints по доменам
- `backend/app/services/`, `repositories/`, `models/`, `schemas/` — доменная логика
- `backend/app/integrations/` — provider/integration layer для `external_indicators`, `news`, `llm`
- `backend/app/pipeline/tasks.py` — общий task-layer
- `backend/ml/` — feature engineering, backtesting, inference, model wrappers
- `backend/airflow/dags/` — orchestration DAG-ы
- `compose/` — Docker Compose profiles и env wiring
- `scripts/` — demo/smoke helpers
- `memory-bank/` — continuity layer между сессиями

## Key Files To Re-Read Before Forecast Work
- `backend/app/pipeline/tasks.py`
- `backend/app/services/forecast_service.py`
- `backend/ml/features/dataset.py`
- `frontend/src/pages/ForecastPage.tsx`
- `frontend/src/features/forecast/components/ModelHealthPanel.tsx`
- `frontend/src/features/forecast/components/ForecastChart.tsx`
- `frontend/src/components/common/*`
- `scripts/run_full_demo.py`

## Key Docs To Re-Read Before The Next Major Slice
- `docs_fuelsight/as-built-baseline.md`
- `docs_fuelsight_2/v2-roadmap.md`
- `docs_fuelsight_2/phase0-gap-matrix.md`
- `memory-bank/activeContext.md`
- `memory-bank/progress.md`

## Commands To Preserve
### Frontend
- `corepack pnpm --filter frontend install`
- `corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000`
- `corepack pnpm --filter frontend test`
- `corepack pnpm --filter frontend build`
- `corepack pnpm --filter frontend test:e2e`
- `corepack pnpm --filter frontend exec playwright install chromium`

### Backend
- `uv sync`
- `uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload`
- `uv run alembic upgrade head`
- `uv run fuelsight-seed-core`
- `uv run fuelsight-pipeline generate-demo-data --replace-existing`
- `uv run fuelsight-pipeline ingest-external-indicators-daily --provider auto --lookback-days 365`
- `uv run fuelsight-pipeline build-feature-store-daily`
- `uv run fuelsight-pipeline train-models-weekly --window-type rolling`
- `uv run fuelsight-pipeline refresh-news-daily --provider auto --lookback-days 14`
- `uv run fuelsight-pipeline refresh-rag-index-daily`
- `uv run pytest`

### Compose / Demo
- `docker compose -f compose/docker-compose.yml --profile core up -d`
- `docker compose -f compose/docker-compose.yml --profile core --profile airflow up -d`
- `docker compose -f compose/docker-compose.yml --profile core --profile airflow down`
- `python scripts/run_full_demo.py`
- `python scripts/run_full_demo.py --without-airflow`
- `python scripts/run_full_demo.py --with-e2e`

## Verification Snapshot From 2026-04-16
- `backend`: `uv run pytest tests/test_forecast_api.py tests/test_forecast_service.py tests/test_pipeline_tasks.py` -> `11 passed`
- `backend`: `uv run pytest tests/test_news_api.py tests/test_chat_api.py` -> `8 passed`
- `frontend`: `corepack pnpm --filter frontend test -- src/pages/ForecastPage.states.test.tsx` -> `35 files / 92 tests passed`

## Verification Snapshot From 2026-04-27
- `backend`: `uv run pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_news_api.py tests/test_news_service.py tests/test_news_integrations.py tests/test_pipeline_tasks.py tests/test_phase9_llm_off_smoke_api.py` -> `26 passed`
- `backend`: `uv run pytest` -> `120 passed`
- `frontend`: `corepack pnpm --filter frontend test -- src/features/news/components/ChatThread.test.tsx src/lib/api/chat.test.ts` -> `37 files / 103 tests passed`
- `frontend`: `corepack pnpm --filter frontend build` -> `PASS`

## Operational Notes
- Worktree сейчас грязный и содержит незакоммиченные изменения в forecast pipeline/UI и в `memory-bank`; не считать `HEAD` точным отражением текущего состояния.
- `frontend/output/` и `git_diff_output.txt` выглядят как локальные/generated artifacts и не являются частью устойчивого продуктового baseline.
- После `Phase A` верхнеуровневый docs-layer уже переведён на capability-based tracking; при следующих срезах важно поддерживать это правило и не возвращаться к phase-label-only описанию.
