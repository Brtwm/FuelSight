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
- Backend deps: FastAPI/Alembic/SQLAlchemy/Pydantic Settings/psycopg/bcrypt/PyJWT.
- Импорт: `openpyxl` (XLSX) и `python-multipart` (upload endpoints).

## API/DB Additions In Phase 4
- Endpoints:
  - `GET /api/v1/kpi/summary`
  - `GET /api/v1/kpi/alerts`
  - `GET /api/v1/kpi/snapshot`
- DB view:
  - `vw_margin_daily` (через Alembic migration `20260404_0002`)
- Backend config:
  - `kpi_low_margin_threshold_rub_per_liter=3.0` (default)

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
