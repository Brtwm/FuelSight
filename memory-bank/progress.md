# Progress

## What Works
- Фазы 0–6 реализованы end-to-end:
  - bootstrap/skeleton;
  - backend core schema + seed;
  - auth + protected shell;
  - import/demo-data vertical slice;
  - KPI dashboard + KPI API;
  - sales/margin analytics + anomalies API/UI;
  - forecast/backtests + ML contour.
- Backend:
  - `/api/v1/auth/*` и `/api/v1/import/*` стабильны;
  - добавлены `/api/v1/kpi/summary`, `/api/v1/kpi/alerts`, `/api/v1/kpi/snapshot`;
  - добавлены `/api/v1/analytics/sales`, `/api/v1/analytics/margin`, `/api/v1/analytics/anomalies`;
  - добавлены `/api/v1/forecasts/run`, `/api/v1/forecasts/latest`, `/api/v1/backtests/run`, `/api/v1/backtests/latest`;
  - добавлены миграции `20260404_0002` (view `vw_margin_daily`) и `20260404_0003` (ML tables);
  - KPI/analytics-агрегации учитывают частичное покрытие закупками и возвращают `purchase_data_missing`.
- Frontend:
  - `/dashboard` больше не stub, показывает KPI, snapshot chart, alerts;
  - `/analytics/sales` и `/analytics/margin` больше не stub;
  - `/forecast` больше не stub;
  - фильтры `product/date/granularity` синхронизируются с URL query params;
  - фильтры `product/horizon/scenario` синхронизируются в `/forecast`;
  - переходы из KPI/alerts ведут в аналитические разделы с сохранением контекста.
- Проверки:
  - backend tests: `uv run pytest` → `57 passed`;
  - frontend lint/test/build: `corepack pnpm --filter frontend lint|test|build` → `28 passed`, build OK.

## Completed Artifacts
- Backend:
  - `backend/alembic/versions/20260404_0003_phase6_forecast_backtests.py`
  - `backend/app/api/v1/forecasts.py`
  - `backend/app/api/v1/backtests.py`
  - `backend/app/dependencies/forecast.py`
  - `backend/app/services/forecast_service.py`
  - `backend/app/schemas/forecasts.py`
  - `backend/app/schemas/backtests.py`
  - `backend/app/models/model_record.py`
  - `backend/app/models/forecast_record.py`
  - `backend/app/models/backtest_run.py`
  - `backend/ml/features/*`
  - `backend/ml/models/*`
  - `backend/ml/backtesting/*`
  - `backend/ml/inference/*`
  - `backend/tests/test_forecast_api.py`
  - `backend/tests/test_forecast_service.py`
  - `backend/alembic/versions/20260404_0002_phase4_kpi_margin_view.py`
  - `backend/app/api/v1/kpi.py`
  - `backend/app/api/v1/analytics.py`
  - `backend/app/dependencies/analytics.py`
  - `backend/app/dependencies/kpi.py`
  - `backend/app/services/analytics_service.py`
  - `backend/app/services/kpi_service.py`
  - `backend/app/schemas/analytics.py`
  - `backend/app/schemas/kpi.py`
  - `backend/tests/test_analytics_api.py`
  - `backend/tests/test_analytics_service.py`
  - `backend/tests/test_kpi_api.py`
  - `backend/tests/test_kpi_service.py`
- Frontend:
  - `frontend/src/pages/ForecastPage.tsx`
  - `frontend/src/lib/api/forecast.ts`
  - `frontend/src/lib/api/forecast.types.ts`
  - `frontend/src/lib/api/forecast.test.ts`
  - `frontend/src/features/forecast/urlFilters.ts`
  - `frontend/src/features/forecast/urlFilters.test.ts`
  - `frontend/src/features/forecast/components/*`
  - `frontend/src/lib/api/analytics.ts`
  - `frontend/src/lib/api/analytics.types.ts`
  - `frontend/src/lib/api/analytics.test.ts`
  - `frontend/src/lib/api/kpi.ts`
  - `frontend/src/lib/api/kpi.types.ts`
  - `frontend/src/pages/SalesAnalyticsPage.tsx`
  - `frontend/src/pages/MarginAnalyticsPage.tsx`
  - `frontend/src/features/analytics/urlFilters.ts`
  - `frontend/src/features/analytics/urlFilters.test.ts`
  - `frontend/src/features/sales/components/*`
  - `frontend/src/features/margin/components/*`
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/features/kpi/components/KpiSummaryCards.tsx`
  - `frontend/src/features/kpi/components/DemandSnapshotChart.tsx`
  - `frontend/src/features/kpi/components/AlertFeed.tsx`
  - `frontend/src/features/kpi/formatters.ts`
  - `frontend/src/lib/api/kpi.test.ts`
  - `frontend/src/features/kpi/formatters.test.ts`
- Docs sync:
  - `docs_fuelsight/project/backend/api-endpoints.md`
  - `docs_fuelsight/features/demand-forecast.md`
  - `docs_fuelsight/features/sales-analytics.md`
  - `docs_fuelsight/features/kpi-dashboard.md`
  - `docs_fuelsight/features/data-import.md`
  - `docs_fuelsight/features/procurement-margin.md`
  - `docs_fuelsight/project/backend/deployment.md`
  - `docs_fuelsight/screens/screen-procurement-margin.md`

## Remaining Work
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
