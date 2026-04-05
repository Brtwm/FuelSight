# FuelSight

FuelSight is a local-only diploma MVP for fuel sales/procurement analytics, margin control, and demand forecasting.

Current status: `Phase 7` (Airflow operationalization + reproducible demo-run).

## What Is Implemented
- Core MVP flow: `login -> import/demo-data -> dashboard -> sales analytics -> margin analytics -> forecast`.
- Backend domains: `auth`, `imports`, `kpi`, `analytics`, `forecasts`, `backtests`.
- Frontend routes:
  - `/login`
  - `/import`
  - `/dashboard`
  - `/analytics/sales`
  - `/analytics/margin`
  - `/forecast`
  - `/news` (bonus contour entry)
- Airflow Phase 7:
  - custom Airflow image with backend modules;
  - DAG IDs: `ingest_internal_sales_daily`, `ingest_internal_purchases_daily`, `build_feature_store_daily`, `train_models_weekly`, `ingest_external_indicators_daily`;
  - paused-by-default DAG behavior for controlled demo triggers.
- Pipeline task-layer + CLI:
  - `uv run fuelsight-pipeline ...`
- Structured JSON logs for API/pipeline events.

## Stack
- Frontend: `React + Vite + TypeScript + MUI + ECharts + TanStack Query`
- Backend: `FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL`
- Pipelines: `Airflow`
- ML: `CatBoost` + `Seasonal Naive`

## Quick Start
### 1) Core stack
```bash
docker compose -f compose/docker-compose.yml --profile core up -d
```

### 2) Core + Airflow
```bash
docker compose -f compose/docker-compose.yml --profile core --profile airflow up -d
```

### 3) Stop
```bash
docker compose -f compose/docker-compose.yml --profile core --profile airflow down
```

## Full Demo Chain (Phase 7)
One command to run end-to-end demo preparation and smoke checks:
```bash
python scripts/run_full_demo.py
```

Wrappers:
```powershell
./scripts/demo-run.ps1
```

```bash
./scripts/demo-run.sh
```

Machine-readable report:
- `scripts/last-smoke-result.json`

## Backend Commands
```bash
cd backend
uv sync
uv run alembic upgrade head
uv run fuelsight-seed-core
uv run pytest
```

Pipeline CLI examples:
```bash
uv run fuelsight-pipeline generate-demo-data --replace-existing --start-date 2025-01-01 --end-date 2025-12-31
uv run fuelsight-pipeline build-feature-store-daily
uv run fuelsight-pipeline train-models-weekly --window-type rolling
```

## Frontend Commands
```bash
corepack pnpm --filter frontend install
corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000
corepack pnpm --filter frontend test
corepack pnpm --filter frontend build
```

## Environment Files
- `.env.example`
- `backend/.env.example`
- `compose/env/db.env`
- `compose/env/backend.env`
- `compose/env/frontend.env`
- `compose/env/airflow.env`

## Source Of Truth
- `AGENTS.md`
- `memory-bank/*`
- `docs_fuelsight/*`

## Notes
- `v1` is single-station (no `stations` entity).
- `ENABLE_LLM=false` by default; core MVP must work without LLM.
- Keep API envelope contract `{ data, error, meta }` unchanged.
