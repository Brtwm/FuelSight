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

## Current Environment Reality
- Поддерживаются `hybrid` и `full docker` режимы.
- `ENABLE_LLM=false` остаётся безопасным дефолтом.
- Core flow не зависит от LLM.
- Для `APP_ENV` вне `local/test` требуется `JWT_SECRET_KEY` длиной не меньше `32`.
- External indicators уже входят в фактический baseline конфигурации:
  - `ENABLE_EXTERNAL_INDICATORS=true`
  - `EXTERNAL_INDICATORS_MODE=live`
  - `EXTERNAL_CACHE_DIR=/opt/fuelsight/artifacts/external`
- Конфиг также уже включает v2-ready флаги:
  - `LLM_PROVIDER_MODE`
  - `DEFENSE_MODE`
  - `DEFENSE_PROFILE`

## File Layout Today
- `frontend/` — SPA с MVP-маршрутами и уже добавленными shared v2 primitives.
- `backend/` — FastAPI домены, ML/pipeline сервисы, integration layer.
- `backend/app/integrations/` — общий каркас для `external indicators`, `news`, `llm`.
- `backend/airflow/` — Airflow image, DAG files и runtime wiring.
- `compose/` — docker profiles/env/init.
- `scripts/` — demo-run и operational helpers.
- `docs_fuelsight/` — текущий `as-built` слой.
- `docs_fuelsight_2/` — target-spec и roadmap.
- `memory-bank/` — session continuity слой.

## Key Files To Remember
- External indicators:
  - `backend/app/integrations/external_indicators/adapters.py`
  - `backend/app/integrations/external_indicators/cache.py`
  - `backend/app/integrations/external_indicators/registry.py`
  - `backend/app/services/external_indicators_service.py`
  - `backend/app/repositories/external_indicators_repository.py`
  - `backend/app/models/external_indicator_daily.py`
  - `backend/alembic/versions/20260408_0005_phase0_external_indicators.py`
- Shared API/meta:
  - `backend/app/api/v1/meta_builders.py`
  - `frontend/src/lib/api/common.types.ts`
- Shared frontend components:
  - `frontend/src/components/common/*`
  - `frontend/src/app/layout/AppShell.tsx`
- Import/analyst-first UX:
  - `frontend/src/features/auth/components/LoginForm.tsx`
  - `frontend/src/pages/ImportPage.tsx`
  - `backend/app/api/v1/auth.py`
  - `backend/app/api/v1/imports.py`

## Commands To Preserve
### Frontend
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
- `uv run fuelsight-pipeline ingest-external-indicators-daily --provider auto --lookback-days 365`
- `uv run fuelsight-pipeline build-feature-store-daily`
- `uv run fuelsight-pipeline train-models-weekly --window-type rolling`
- `uv run pytest`

### Compose / Demo
- `docker compose -f compose/docker-compose.yml --profile core up -d`
- `docker compose -f compose/docker-compose.yml --profile core --profile airflow up -d`
- `docker compose -f compose/docker-compose.yml --profile core --profile airflow down`
- `python scripts/run_full_demo.py`
- `python scripts/run_full_demo.py --with-e2e`

## Operational Notes
- Airflow metadata DB остаётся отделённой от product DB.
- DAG `ingest_external_indicators_daily` уже должен рассматриваться как реальный ingest, а не как stub.
- Demo runner и общий pipeline-контур остаются важной частью defense-ready story, но `DEFENSE_MODE` как полноценный продуктовый слой ещё впереди по roadmap.
- Верхнеуровневые обзорные документы ещё не везде догнали фактический state после `v2` Фазы 3, поэтому при старте новых задач сначала доверять `memory-bank/`, затем проверять код.
