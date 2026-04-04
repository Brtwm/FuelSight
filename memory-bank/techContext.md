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
- Базовый сценарий поддерживает `hybrid` и `full docker` режимы.
- `ENABLE_LLM=false` по умолчанию.
- Core MVP не зависит от LLM/чат-контура.

## File Layout Today
- `frontend/` — SPA с auth-flow, import-flow и KPI dashboard (`/dashboard`) поверх `/api/v1/kpi/*`.
- `backend/` — FastAPI core + auth/import/kpi API + SQLAlchemy core models + Alembic.
- `compose/` — docker-compose с профилями `core` и `airflow`, env файлы.
- `scripts/` — helper scripts для demo run.
- `docs_fuelsight/` и `memory-bank/` — спецификации и оперативный контекст.

## Toolchain Versions
- Node: `24.14.1`
- pnpm: `10.33.0`
- Python: `3.12.x`
- uv: `0.10.8+`

## Key Dependencies To Remember
- Frontend deps: MUI/Router/Query/RHF/Zod/ECharts + `echarts-for-react`.
- Backend deps: FastAPI/Alembic/SQLAlchemy/Pydantic Settings/psycopg/bcrypt/PyJWT/CatBoost.
- Импорт: `openpyxl` (XLSX) и `python-multipart` (upload endpoints).

## API/DB Additions In Phase 4-6
- Endpoints:
  - `GET /api/v1/kpi/summary`
  - `GET /api/v1/kpi/alerts`
  - `GET /api/v1/kpi/snapshot`
  - `GET /api/v1/analytics/sales`
  - `GET /api/v1/analytics/margin`
  - `GET /api/v1/analytics/anomalies`
  - `POST /api/v1/forecasts/run`
  - `GET /api/v1/forecasts/latest`
  - `POST /api/v1/backtests/run`
  - `GET /api/v1/backtests/latest`
- DB view:
  - `vw_margin_daily` (через Alembic migration `20260404_0002`)
- DB tables:
  - `models`
  - `forecasts`
  - `backtest_runs` (через Alembic migration `20260404_0003`)
- Backend config:
  - `kpi_low_margin_threshold_rub_per_liter=3.0` (default)

## Frontend Additions In Phase 5-6
- API client:
  - `frontend/src/lib/api/analytics.ts`
  - `frontend/src/lib/api/analytics.types.ts`
  - `frontend/src/lib/api/forecast.ts`
  - `frontend/src/lib/api/forecast.types.ts`
- URL filter sync helper:
  - `frontend/src/features/analytics/urlFilters.ts`
  - `frontend/src/features/forecast/urlFilters.ts`
- Sales analytics components:
  - `frontend/src/features/sales/components/*`
- Margin analytics components:
  - `frontend/src/features/margin/components/*`
- Forecast components:
  - `frontend/src/features/forecast/components/*`

## Commands To Preserve
- Frontend:
  - `corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000`
  - `corepack pnpm --filter frontend lint`
  - `corepack pnpm --filter frontend test`
  - `corepack pnpm --filter frontend build`
- Backend:
  - `uv sync`
  - `uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload`
  - `uv run alembic upgrade head`
  - `uv run fuelsight-seed-core`
  - `uv run pytest`
- Local stack:
  - `docker compose -f compose/docker-compose.yml --profile core up -d`
  - `docker compose -f compose/docker-compose.yml --profile airflow up -d`
  - `docker compose -f compose/docker-compose.yml --profile core --profile airflow down`
