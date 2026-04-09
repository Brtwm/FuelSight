# Tech Context

## Main Stack
- Frontend: `React + Vite + TypeScript + MUI + Apache ECharts + React Router + TanStack Query + React Hook Form + Zod`
- Backend: `FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + PostgreSQL`
- Pipelines: `Airflow`
- ML: `CatBoost` primary, `Seasonal Naive` baseline

## Ports
- Frontend dev: `3000`
- Backend dev: `8061`
- PostgreSQL: `5432`
- Airflow webserver: `8080`

## Environment Constraints
- Поддерживаются `hybrid` и `full docker` режимы.
- `ENABLE_LLM=false` по умолчанию.
- Core MVP не зависит от LLM/чат-контура.
- Для `APP_ENV` вне `local/test` требуется `JWT_SECRET_KEY` длиной >= 32.
- В текущем рабочем состоянии defaults смещены к external indicators:
  - `ENABLE_EXTERNAL_INDICATORS=true`;
  - `EXTERNAL_INDICATORS_MODE=live`;
  - `EXTERNAL_CACHE_DIR=/opt/fuelsight/artifacts/external`.

## File Layout Today
- `frontend/` — SPA core MVP routes.
- `backend/` — FastAPI domains + ML services + pipeline task-layer.
- `backend/airflow/` — custom Airflow image, DAG files, inbox mounts.
- `compose/` — profile-based stack (`core`, `airflow`) и env/init.
- `scripts/` — helper scripts + full demo runner.
- `docs_fuelsight/`, `memory-bank/` — source-of-truth docs/context.
- `docs_fuelsight_2/` — target-spec документация улучшенной версии.

## Toolchain Versions
- Node: `24.14.1`
- pnpm: `10.33.0`
- Python: `3.12.x`
- uv: `0.10.8+`
- Docker Compose: `v5.x`

## Phase 7 Additions
- CLI entrypoint: `uv run fuelsight-pipeline ...`
- Pipeline modules:
  - `backend/app/pipeline/tasks.py`
  - `backend/app/scripts/pipeline_runner.py`
- Structured logging:
  - `backend/app/core/logging.py`
  - request/pipeline logs with JSON fields.
- Airflow DAG IDs:
  - `ingest_internal_sales_daily`
  - `ingest_internal_purchases_daily`
  - `build_feature_store_daily`
  - `train_models_weekly`
  - `ingest_external_indicators_daily`
- Airflow metadata isolation:
  - product DB: `fuelsight`
  - metadata DB: `airflow`
- External indicators ingestion additions (uncommitted state):
  - adapters: `backend/app/integrations/external_indicators/adapters.py`;
  - cache manager: `backend/app/integrations/external_indicators/cache.py`;
  - registry/types: `backend/app/integrations/external_indicators/registry.py`, `types.py`;
  - ingestion service: `backend/app/services/external_indicators_service.py`;
  - repository: `backend/app/repositories/external_indicators_repository.py`;
  - pipeline task writes manifest with coverage/fallback summary to `EXTERNAL_CACHE_DIR/manifests/<date>/`.

## Commands To Preserve
### Frontend
- `corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000`
- `corepack pnpm --filter frontend test`
- `corepack pnpm --filter frontend build`
- `corepack pnpm --filter frontend test:e2e`
- `corepack pnpm --filter frontend exec playwright install chromium` (one-time on fresh machine)

### Backend
- `uv sync`
- `uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload`
- `uv run alembic upgrade head`
- `uv run fuelsight-seed-core`
- `uv run fuelsight-pipeline train-models-weekly --window-type rolling`
- `uv run fuelsight-pipeline ingest-external-indicators-daily --provider auto --lookback-days 365`
- `uv run pytest`

### Compose / Demo
- `docker compose -f compose/docker-compose.yml --profile core up -d`
- `docker compose -f compose/docker-compose.yml --profile core --profile airflow up -d`
- `docker compose -f compose/docker-compose.yml --profile core --profile airflow down`
- `python scripts/run_full_demo.py`
- `python scripts/run_full_demo.py --with-e2e`
- В v2 ожидается расширение demo-runner для defense mode, но текущие команды остаются базой совместимости.
