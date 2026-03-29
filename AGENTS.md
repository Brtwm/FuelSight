# FuelSight Agent Rules

## About
- FuelSight — внутренний локальный дипломный MVP для анализа продаж, закупок, маржи и прогноза спроса на нефтепродукты.
- Продукт заменяет связку `Excel + 1C + ручной анализ`.
- UI и пользовательские тексты — на русском языке. Технические идентификаторы, API paths, file names — на английском.

## Product Boundaries
- `v1` поддерживает одну точку продаж. Не вводи `stations` без отдельного обновления документации.
- Бонусный NLP/LLM-контур опционален. При `LLM off` KPI, аналитика, импорт и прогноз должны продолжать работать.
- Не проектируй multi-tenant SaaS, публичный биллинг или внешнюю монетизацию.

## Stack
- Frontend: `React + Vite + TypeScript + MUI + Apache ECharts + React Router + TanStack Query + React Hook Form + Zod`
- Backend: `FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic + PostgreSQL`
- Pipelines: `Airflow`
- ML: `CatBoost` primary, `Seasonal Naive` baseline

## Key Routes
- `/login`
- `/import`
- `/dashboard`
- `/analytics/sales`
- `/analytics/margin`
- `/forecast`
- `/news`

## API Rules
- Base URL: `/api/v1`
- Main groups:
  - `/api/v1/auth/*`
  - `/api/v1/import/*`
  - `/api/v1/kpi/*`
  - `/api/v1/analytics/*`
  - `/api/v1/forecasts/*`
  - `/api/v1/backtests/*`
  - `/api/v1/news/*`
  - `/api/v1/chat/*`
- Response envelope is always `{ data, error, meta }`.
- Preserve role boundaries: `admin` manages imports and refresh/retraining, `analyst` reads analytics and runs forecasts.

## Data Rules
- Core tables: `roles`, `users`, `products`, `sales_daily`, `purchases_daily`, `import_jobs`
- ML tables: `models`, `forecasts`, `backtest_runs`
- NLP tables: `news_raw`, `news_digests`, `chat_sessions`, `chat_messages`
- Keep fact grain at `day x product`.

## Implementation Priorities
- Build MVP flow first: `login -> import/demo-data -> dashboard -> sales analytics -> margin analytics -> forecast`.
- Keep what-if forecasting constrained to price delta scenarios.
- Always expose forecast quality metrics (`MAE`, `RMSE`, `SMAPE`) alongside predictions.
- Chat answers are invalid without citations to internal refs or news records.

## Commands
- Frontend:
  - `pnpm install`
  - `pnpm dev --host 0.0.0.0 --port 3000`
  - `pnpm build`
  - `pnpm test`
- Backend:
  - `uv sync`
  - `uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload`
  - `uv run alembic upgrade head`
  - `uv run pytest`
- Local stack:
  - `docker compose up -d db backend frontend`
  - `docker compose up -d airflow-init airflow-webserver airflow-scheduler`

## Coding Expectations
- Prefer clear modular boundaries by domain: `auth`, `imports`, `kpi`, `analytics`, `forecasts`, `backtests`, `news`, `chat`.
- Keep frontend filters synced with URL query params.
- Keep business text simple and readable for non-technical users.
- Do not hide empty states; explain how to load demo data or imports.
- Do not surface raw SHAP or ML jargon as the primary UX.

## Docs To Read First
- `@docs_fuelsight/project-idea.md`
- `@docs_fuelsight/marketing/go-to-market.md`
- `@docs_fuelsight/project/frontend/frontend-docs.md`
- `@docs_fuelsight/project/backend/backend-docs.md`
- `@docs_fuelsight/project/backend/api-endpoints.md`
- `@docs_fuelsight/project/backend/database.md`
- `@docs_fuelsight/project/backend/ml-pipeline.md`
- `@docs_fuelsight/project/backend/deployment.md`
- `@docs_fuelsight/features/auth.md`
- `@docs_fuelsight/features/data-import.md`
- `@docs_fuelsight/features/kpi-dashboard.md`
- `@docs_fuelsight/features/sales-analytics.md`
- `@docs_fuelsight/features/procurement-margin.md`
- `@docs_fuelsight/features/demand-forecast.md`
- `@docs_fuelsight/features/news-digest-chat.md`
- `@docs_fuelsight/screens/screen-login.md`
- `@docs_fuelsight/screens/screen-data-import.md`
- `@docs_fuelsight/screens/screen-kpi-dashboard.md`
- `@docs_fuelsight/screens/screen-sales-analytics.md`
- `@docs_fuelsight/screens/screen-procurement-margin.md`
- `@docs_fuelsight/screens/screen-demand-forecast.md`
- `@docs_fuelsight/screens/screen-news-digest-chat.md`
