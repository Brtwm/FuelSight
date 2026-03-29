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
- `frontend/` — рабочий SPA skeleton.
- `backend/` — рабочий FastAPI skeleton + alembic scaffold + tests.
- `compose/` — docker-compose с профилями `core` и `airflow`, env файлы.
- `scripts/` — helper scripts для demo run.
- `docs_fuelsight/` и `memory-bank/` — спецификации и оперативный контекст.

## Toolchain Versions
- Node: `24.14.1`
- pnpm: `10.33.0`
- Python: `3.12.x`
- uv: `0.10.8+`

## Key Dependencies To Remember
- Frontend foundation deps уже подключены (MUI/Router/Query/RHF/Zod/ECharts).
- Backend deps уже подключены (FastAPI/Alembic/SQLAlchemy/Pydantic Settings/psycopg/passlib).

## Commands To Preserve
- Frontend:
  - `corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000`
  - `corepack pnpm --filter frontend lint`
  - `corepack pnpm --filter frontend build`
  - `corepack pnpm --filter frontend test`
- Backend:
  - `uv sync`
  - `uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload`
  - `uv run alembic upgrade head`
  - `uv run pytest`
- Local stack:
  - `docker compose -f compose/docker-compose.yml --profile core up -d`
  - `docker compose -f compose/docker-compose.yml --profile airflow up -d`
  - `docker compose -f compose/docker-compose.yml --profile core --profile airflow down`
