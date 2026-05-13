# FuelSight As-Built Baseline

## Purpose

This document records the current implemented state of FuelSight for diploma
review and public portfolio readers. It is capability-based: code, tests, and
demo commands are the primary evidence, while roadmap items are kept separate in
`docs/roadmap.md`.

## Source Priority

When documentation and implementation disagree, use this order:

1. Current code and tests.
2. `README.md` for public quick-start and demo commands.
3. `DEVELOPMENT.md` for contributor rules.
4. Detailed documentation in `docs/`.

## Capability Matrix

| capability | status | primary routes / scope | implementation evidence | verification evidence |
| --- | --- | --- | --- | --- |
| Auth, roles, refresh tokens | implemented | `/login`, `/api/v1/auth/*` | `backend/app/api/v1/auth.py`, `frontend/src/features/auth/*` | `backend/tests/test_auth_api.py`, `frontend/src/pages/LoginPage.integration.test.tsx` |
| Admin import operations | implemented | `/import`, `/api/v1/import/*` | `backend/app/api/v1/imports.py`, `frontend/src/pages/ImportPage.tsx` | `backend/tests/test_import_api.py`, import component tests |
| KPI dashboard | implemented | `/dashboard`, `/api/v1/kpi/*` | `backend/app/api/v1/kpi.py`, `frontend/src/pages/DashboardPage.tsx` | `backend/tests/test_kpi_api.py`, dashboard state tests |
| Sales analytics | implemented | `/analytics/sales`, `/api/v1/analytics/sales` | `backend/app/api/v1/analytics.py`, `frontend/src/pages/SalesAnalyticsPage.tsx` | `backend/tests/test_analytics_api.py`, sales page tests |
| Margin analytics | implemented | `/analytics/margin`, `/api/v1/analytics/margin` | analytics service/API, `frontend/src/pages/MarginAnalyticsPage.tsx` | analytics API and margin page tests |
| Forecast and backtests | implemented | `/forecast`, `/api/v1/forecasts/*`, `/api/v1/backtests/*` | `backend/app/services/forecast_service.py`, `frontend/src/pages/ForecastPage.tsx` | forecast API/service tests, forecast page tests |
| External indicators | implemented | pipeline, analytics, forecast, news context | `backend/app/integrations/external_indicators/*`, `backend/app/pipeline/tasks.py` | `backend/tests/test_pipeline_tasks.py`, external indicator tests |
| News digest and search | implemented | `/news`, `/api/v1/news/*` | `backend/app/integrations/news/*`, `backend/app/services/news_service.py` | news API/service/integration tests |
| Cited chat and RAG | implemented | `/api/v1/chat/*`, `/news` | `backend/app/services/chat_service.py`, `backend/app/services/chat_retrieval.py`, `backend/app/services/rag_index_service.py` | chat API/service tests, RAG index tests |
| Optional cloud LLM mode | implemented as optional | chat/news provider layer | `backend/app/integrations/llm/*` | LLM integration tests; live provider tests skip without keys |
| Airflow orchestration | implemented | backend Airflow DAGs | `backend/airflow/dags/*`, `backend/airflow/README.md` | demo runner Airflow DAG contract |
| Defense/demo runner | implemented | `scripts/run_full_demo.py` | profile-driven Docker/demo pipeline | full demo smoke and e2e smoke |

## Route Coverage

| route | current behavior |
| --- | --- |
| `/login` | analyst-first local login with demo credentials in local mode |
| `/import` | admin-only import, demo-data refresh, diagnostics |
| `/dashboard` | KPI cards, demand snapshot, summaries, freshness/status badges |
| `/analytics/sales` | trends, seasonality, comparisons, anomalies, URL-synced filters |
| `/analytics/margin` | procurement/margin analysis, low-margin detection, explanations |
| `/forecast` | CatBoost-first forecast, baseline comparison, scenario deltas, quality metrics |
| `/news` | news digest/search and cited retrieval-first chat |

## Confirmed Validation Snapshot

Last verified locally on 2026-05-12:

| command | result |
| --- | --- |
| `cd backend && uv run ruff check .` | passed |
| `cd backend && uv run pytest` | `197 passed, 2 skipped` |
| `cd backend && uv tool run pip-audit` | no known vulnerabilities |
| `corepack pnpm --filter frontend test` | `132 passed` |
| `corepack pnpm --filter frontend build` | passed |
| `cd frontend && corepack pnpm audit --prod` | no known vulnerabilities |
| `corepack pnpm --filter frontend test:e2e` | `4 passed` |
| `docker compose -f compose/docker-compose.yml -f compose/docker-compose.offline-safe.yml --profile core up -d --build` | core services healthy |
| `docker compose -f compose/docker-compose.yml -f compose/docker-compose.offline-safe.yml --profile core --profile airflow up -d --build` | core and Airflow services healthy |
| `python scripts/run_full_demo.py` | `PASS` |
| `python scripts/run_full_demo.py --with-e2e` | `PASS` |

## Known Boundaries

- `v1` supports one sales point; there is no `stations` entity.
- LLM/cloud mode is optional. The default public demo path is offline-safe and retrieval-only.
- Demo users and weak local passwords are local-only and must not be used for a network-facing deployment.
- Compose ports are published for local development; use a trusted machine/network or add a localhost-only override before wider exposure.
