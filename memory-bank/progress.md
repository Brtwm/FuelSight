# Progress

## What Works
- Фазы 0–4 реализованы end-to-end:
  - bootstrap/skeleton;
  - backend core schema + seed;
  - auth + protected shell;
  - import/demo-data vertical slice;
  - KPI dashboard + KPI API.
- Backend:
  - `/api/v1/auth/*` и `/api/v1/import/*` стабильны;
  - добавлены `/api/v1/kpi/summary`, `/api/v1/kpi/alerts`, `/api/v1/kpi/snapshot`;
  - добавлена миграция `20260404_0002` и view `vw_margin_daily`;
  - KPI-агрегации учитывают частичное покрытие закупками и возвращают coverage meta.
- Frontend:
  - `/dashboard` больше не stub, показывает KPI, snapshot chart, alerts;
  - фильтры периода и продукта работают с query cache;
  - переходы из KPI/alerts ведут в аналитические разделы.
- Проверки:
  - backend tests: `uv run pytest` → `39 passed`;
  - frontend lint/test/build: `corepack pnpm --filter frontend lint|test|build` → `17 passed`, build OK.

## Completed Artifacts
- Backend:
  - `backend/alembic/versions/20260404_0002_phase4_kpi_margin_view.py`
  - `backend/app/api/v1/kpi.py`
  - `backend/app/dependencies/kpi.py`
  - `backend/app/services/kpi_service.py`
  - `backend/app/schemas/kpi.py`
  - `backend/tests/test_kpi_api.py`
  - `backend/tests/test_kpi_service.py`
- Frontend:
  - `frontend/src/lib/api/kpi.ts`
  - `frontend/src/lib/api/kpi.types.ts`
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/features/kpi/components/KpiSummaryCards.tsx`
  - `frontend/src/features/kpi/components/DemandSnapshotChart.tsx`
  - `frontend/src/features/kpi/components/AlertFeed.tsx`
  - `frontend/src/features/kpi/formatters.ts`
  - `frontend/src/lib/api/kpi.test.ts`
  - `frontend/src/features/kpi/formatters.test.ts`
- Docs sync:
  - `docs_fuelsight/project/backend/api-endpoints.md`
  - `docs_fuelsight/features/kpi-dashboard.md`
  - `docs_fuelsight/features/data-import.md`
  - `docs_fuelsight/features/procurement-margin.md`
  - `docs_fuelsight/project/backend/deployment.md`
  - `docs_fuelsight/screens/screen-procurement-margin.md`

## Remaining Work
- Фаза 5: `/analytics/sales`, `/analytics/margin`, `/analytics/anomalies`.
- Фаза 6: forecast/backtests/ML baseline+catboost contour.
- Фаза 7+: Airflow operationalization, bonus news/chat contour, hardening.

## Known Issues
- Frontend bundle size warning сохраняется (ожидаемо для текущего набора зависимостей и графиков).
- JWT secret в dev-конфиге короткий и предназначен только для локальной разработки.

## Maintenance Rule
- После каждой следующей фазы обновлять:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При архитектурных изменениях также обновлять:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
