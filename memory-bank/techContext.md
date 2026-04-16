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
  - `LLM_PROVIDER_MODE`
  - `DEFENSE_MODE`
  - `DEFENSE_PROFILE`

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
- `uv run fuelsight-pipeline generate-demo-data --replace-existing --start-date 2025-01-01 --end-date 2025-12-31`
- `uv run fuelsight-pipeline ingest-external-indicators-daily --provider auto --lookback-days 365`
- `uv run fuelsight-pipeline build-feature-store-daily`
- `uv run fuelsight-pipeline train-models-weekly --window-type rolling`
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
- `frontend`: `corepack pnpm --filter frontend test -- src/pages/ForecastPage.states.test.tsx` -> `35 files / 92 tests passed`

## Operational Notes
- Worktree сейчас грязный и содержит незакоммиченные изменения в forecast pipeline/UI и в `memory-bank`; не считать `HEAD` точным отражением текущего состояния.
- `frontend/output/` и `git_diff_output.txt` выглядят как локальные/generated artifacts и не являются частью устойчивого продуктового baseline.
- `README.md` всё ещё формулирует статус через `Phase 9 complete`, тогда как `docs_fuelsight_2/v2-roadmap.md` использует phases `1-7`; при следующих обновлениях лучше описывать состояние через capabilities, а не только phase-label.
