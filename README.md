# FuelSight

FuelSight is a local-only diploma product for fuel sales/procurement analytics, margin control, demand forecasting and an optional `news + chat` contour.

Current project status is tracked capability-by-capability, not by a single phase label.

## Capability Snapshot
| capability | status | note |
| --- | --- | --- |
| Core analyst flow `login -> dashboard -> analytics -> forecast` | stable | implemented and covered by current route/test baseline |
| Admin import and diagnostics flow | stable | neutral analyst copy and admin-only diagnostics are already in place |
| Shared explainable UI/meta layer (`dashboard`, `sales`, `margin`) | stable + worktree | KPI/analytics migrated to unified `meta.explainability` + common Chart/DataState design system |
| External indicators foundation | stable | schema, adapters, cache/fallback ladder and pipeline ingest are present |
| CatBoost-first forecast contour | stable + in refinement | richer health/meta contracts and scenario UX are already in code/worktree |
| News digest/search | stable + worktree | real-provider ingest is wired through RSS/API adapters with cache and manual snapshot fallback |
| Chat with citations | advanced RAG worktree | `retrieval_only` fallback, citations, confidence and verification metadata are implemented; cloud/local generation remains Phase I |
| Real news + verified RAG chat | partial + worktree | real news baseline and verified retrieval-first chat are implemented; pgvector chunk index baseline is now wired for Phase H |
| Visual/mobile readiness for defense | stable + worktree | desktop regression + `iphone-13`/`pixel-7` smoke pass; sales/margin mobile rhythm aligned |
| Defense mode / executive outputs | target | smoke runner exists, full defense layer still planned |

Detailed `as-built` baseline:
- `docs_fuelsight/as-built-baseline.md`

Execution backlog and doc-to-code mapping:
- `docs_fuelsight_2/phase0-gap-matrix.md`

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

## Full Demo Chain
One command to run end-to-end demo preparation and smoke checks:
```bash
python scripts/run_full_demo.py
```

Optional: include Playwright E2E in the same report:
```bash
python scripts/run_full_demo.py --with-e2e
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
uv run fuelsight-pipeline generate-demo-data --replace-existing
uv run fuelsight-pipeline ingest-external-indicators-daily --provider auto --lookback-days 365
uv run fuelsight-pipeline build-feature-store-daily
uv run fuelsight-pipeline train-models-weekly --window-type rolling
uv run fuelsight-pipeline refresh-news-daily --provider auto --lookback-days 14
uv run fuelsight-pipeline refresh-rag-index-daily
```

## Frontend Commands
```bash
corepack pnpm --filter frontend install
corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000
corepack pnpm --filter frontend test
corepack pnpm --filter frontend build
corepack pnpm --filter frontend test:e2e
```

## Environment Files
- `.env.example`
- `backend/.env.example`
- `compose/env/db.env`
- `compose/env/backend.env`
- `compose/env/frontend.env`
- `compose/env/airflow.env`

Important readiness notes:
- Compose uses `pgvector/pgvector:pg16`; if you run `uv run alembic upgrade head` against a
  manually created PostgreSQL, that database must have the `vector` extension available.
- Import uploads are capped by `IMPORT_MAX_UPLOAD_BYTES` and `IMPORT_MAX_ROWS`; defaults are
  10 MiB and 50,000 rows.
- Demo accounts are enabled for local diploma flow by `FUELSIGHT_SEED_DEMO_USERS=true` and
  `VITE_ENABLE_DEMO_CREDENTIALS=true`. Disable both before any network-facing demo.
- `cloud-enhanced` defense mode sends the prepared evidence/citation pack to the configured LLM
  provider. Use it only deliberately, with approved credentials.
- `.env` is ignored by git but may contain cloud credentials on a demo machine. Remove or rotate
  those credentials before handing off an archive or environment.

## Source Of Truth
- `AGENTS.md`
- `memory-bank/*`
- `docs_fuelsight/as-built-baseline.md`
- `docs_fuelsight/*`
- `docs_fuelsight_2/v2-roadmap.md`
- `docs_fuelsight_2/phase0-gap-matrix.md`
- `docs_fuelsight_2/*` (`target-spec` для улучшенной версии)

## Notes
- `v1` is single-station (no `stations` entity).
- `ENABLE_LLM=false` by default; core MVP must work without LLM.
- Compose uses `pgvector/pgvector:pg16` because Phase H stores RAG chunks with `embedding vector(64)`.
- non-local/non-test startup requires `JWT_SECRET_KEY` with at least 32 characters.
- Keep API envelope contract `{ data, error, meta }` unchanged.
- If top-level docs disagree, prefer `memory-bank -> code -> docs_fuelsight -> README`.
