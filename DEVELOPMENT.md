# FuelSight Development Guide

This file keeps the durable engineering and product constraints for contributors.

## Product Boundaries

- FuelSight is a local diploma MVP and portfolio project, not a public SaaS.
- `v1` supports one sales point. Do not add `stations` without updating docs and schema.
- The core flow must work with `ENABLE_LLM=false`.
- User-facing UI copy is in Russian. Technical identifiers, API paths, and file names are in English.
- The primary MVP path is `login -> import/demo-data -> dashboard -> sales analytics -> margin analytics -> forecast`.

## Stack

- Frontend: `React + Vite + TypeScript + MUI + Apache ECharts + React Router + TanStack Query + React Hook Form + Zod`
- Backend: `FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + PostgreSQL`
- Pipelines: `Airflow`
- ML: `CatBoost` primary model, `Seasonal Naive` baseline

## API And Data Rules

- API base path: `/api/v1`.
- Response envelope: `{ data, error, meta }`.
- Main API groups: `auth`, `import`, `kpi`, `analytics`, `forecasts`, `backtests`, `news`, `chat`.
- Preserve role boundaries:
  - `admin`: imports, demo refresh, retraining/backtest operations.
  - `analyst`: reads analytics and runs forecasts.
- Fact grain stays `day x product`.
- Chat answers must include citations or return a blocked/uncertain response.

## Local Commands

Backend:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run pytest
uv run ruff check .
```

Frontend:

```bash
corepack pnpm --filter frontend install
corepack pnpm --filter frontend test
corepack pnpm --filter frontend build
corepack pnpm --filter frontend test:e2e
```

Docker:

```bash
docker compose -f compose/docker-compose.yml -f compose/docker-compose.offline-safe.yml --profile core up -d --build
python scripts/run_full_demo.py
```

## Contribution Expectations

- Keep changes scoped to the requested behavior.
- Match existing domain boundaries: `auth`, `imports`, `kpi`, `analytics`, `forecasts`, `backtests`, `news`, `chat`.
- Keep frontend filters synced with URL query params.
- Keep empty states visible and actionable.
- Do not surface raw ML jargon as the primary UX.
- Do not commit `.env`, `compose/env/*.env`, generated reports, model artifacts, Playwright output, or local caches.
- Keep public project documentation in `docs/`; do not add AI-agent continuity notes or private planning logs.
