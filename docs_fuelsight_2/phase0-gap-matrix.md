# Phase A Backlog Matrix (Contracts Freeze + Docs Sync)

Этот backlog связывает:
- `doc item`;
- текущие кодовые модули;
- проверочные тесты;
- демонстрационный сценарий;
- и явный фактический статус.

## Легенда статусов
- `implemented`
- `implemented_mvp`
- `implemented + worktree`
- `partial`
- `docs_only`

## Cross-Cutting Track
| doc_item | scope | current_status | current_code_modules | test_target | demo_scenario | next_slice |
| --- | --- | --- | --- | --- | --- | --- |
| project-idea.md | whole product baseline | implemented | `README.md`, `docs_fuelsight/project-idea.md`, `memory-bank/projectbrief.md` | manual docs review | explain product scope to commission | keep as-built and target docs separated |
| project/frontend/frontend-docs.md | frontend architecture | implemented | `frontend/src/app/*`, `frontend/src/components/common/*`, `frontend/src/pages/*` | `corepack pnpm --filter frontend test` | show analyst UI narrative | add explicit mobile/responsive rules |
| project/backend/backend-docs.md | backend architecture | implemented | `backend/app/api/v1/*`, `backend/app/services/*`, `backend/app/integrations/*`, `backend/app/pipeline/tasks.py` | `uv run pytest` | explain API/domains/pipeline structure | add real news + verified RAG target in backend docs |
| project/backend/api-endpoints.md | API contract | partial | `backend/app/schemas/*`, `backend/app/api/v1/*`, `frontend/src/lib/api/*.types.ts` | targeted API suites | demonstrate envelope + enriched meta | sync news/chat fallback semantics and forecast as-built contracts |
| integrations-and-data-sources.md | external providers and cache strategy | partial | `backend/app/integrations/external_indicators/*`, `backend/app/services/external_indicators_service.py` | `backend/tests/test_pipeline_tasks.py` | explain live/cache/manual snapshot story | add concrete real-news provider plan |
| operability-and-defense-mode.md | smoke/ops/defense | partial | `scripts/run_full_demo.py`, `backend/app/pipeline/tasks.py` | smoke/manual demo | run local demo prep | define defense report/export implementation backlog |

## Feature And Screen Backlog
| doc_item | route | current_status | current_code_modules | test_target | demo_scenario | next_slice |
| --- | --- | --- | --- | --- | --- | --- |
| features/auth.md | `/login` | implemented | `backend/app/api/v1/auth.py`, `backend/app/schemas/auth.py`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/features/auth/components/LoginForm.tsx` | `backend/tests/test_auth_api.py`, `frontend/src/pages/LoginPage.integration.test.tsx` | analyst logs in and lands on `/dashboard` | keep current baseline, no large code changes needed before next slice |
| screens/screen-login.md | `/login` | partial | `frontend/src/pages/LoginPage.tsx`, `frontend/src/theme/theme.ts` | `frontend/src/pages/LoginPage.integration.test.tsx` | mobile-friendly login demo | strengthen visual polish and mobile typography/spacing |
| features/data-import.md | `/import` | implemented | `backend/app/api/v1/imports.py`, `backend/app/schemas/imports.py`, `frontend/src/pages/ImportPage.tsx`, `frontend/src/features/import/components/ImportJobsTable.tsx` | `backend/tests/test_import_api.py`, `frontend/src/pages/ImportPage.integration.test.tsx` | admin refreshes initial history and opens diagnostics | keep as-built docs synced with neutral copy and admin-only diagnostics |
| screens/screen-data-import.md | `/import` | implemented | `frontend/src/pages/ImportPage.tsx`, `frontend/src/components/common/DiagnosticsDrawer.tsx` | `frontend/src/pages/ImportPage.integration.test.tsx`, `frontend/e2e/admin-operational-flow.spec.ts` | admin operational flow | add responsive layout notes for tablet/mobile admin view |
| features/kpi-dashboard.md | `/dashboard` | implemented | `backend/app/api/v1/kpi.py`, `backend/app/api/v1/meta_builders.py`, `frontend/src/pages/DashboardPage.tsx` | `backend/tests/test_kpi_api.py`, `frontend/src/pages/DashboardPage.states.test.tsx` | analyst opens KPI overview | finalize docs for business summary/freshness/meta as-built |
| screens/screen-kpi-dashboard.md | `/dashboard` | partial | `frontend/src/pages/DashboardPage.tsx`, `frontend/src/features/kpi/components/*` | `frontend/src/pages/DashboardPage.states.test.tsx` | commission sees KPI summary and badges | add mobile layout track and visual polish backlog |
| features/sales-analytics.md | `/analytics/sales` | implemented | `backend/app/api/v1/analytics.py`, `backend/app/schemas/analytics.py`, `frontend/src/pages/SalesAnalyticsPage.tsx` | `backend/tests/test_analytics_api.py`, `frontend/src/pages/SalesAnalyticsPage.states.test.tsx` | analyst analyzes demand dynamics | keep as-built docs honest about current chart system and mobile gaps |
| screens/screen-sales-analytics.md | `/analytics/sales` | partial | `frontend/src/pages/SalesAnalyticsPage.tsx`, `frontend/src/features/sales/components/*` | `frontend/src/pages/SalesAnalyticsPage.states.test.tsx`, `frontend/output/playwright/mobile-sales.png` | analyst mobile review of sales page | make shell responsive and compress chart/layout for mobile |
| features/procurement-margin.md | `/analytics/margin` | implemented | `backend/app/api/v1/analytics.py`, `frontend/src/pages/MarginAnalyticsPage.tsx`, `frontend/src/features/margin/components/*` | `backend/tests/test_analytics_api.py`, `frontend/src/pages/MarginAnalyticsPage.states.test.tsx`, `frontend/src/pages/MarginAnalyticsPage.selection.test.tsx` | analyst investigates low-margin day | sync threshold/reason panel contracts in docs |
| screens/screen-procurement-margin.md | `/analytics/margin` | partial | `frontend/src/pages/MarginAnalyticsPage.tsx` | `frontend/src/pages/MarginAnalyticsPage.states.test.tsx` | margin risk explanation | add explicit responsive selection behavior and mobile reading order |
| features/demand-forecast.md | `/forecast` | implemented + worktree | `backend/app/services/forecast_service.py`, `backend/app/pipeline/tasks.py`, `frontend/src/pages/ForecastPage.tsx`, `frontend/src/features/forecast/components/*` | `backend/tests/test_forecast_api.py`, `backend/tests/test_forecast_service.py`, `frontend/src/pages/ForecastPage.states.test.tsx` | analyst runs base/scenario forecast and reads model health | commit-ready docs sync for health/provider/baseline/meta contracts |
| screens/screen-demand-forecast.md | `/forecast` | partial | `frontend/src/pages/ForecastPage.tsx`, `frontend/src/features/forecast/components/ModelHealthPanel.tsx`, `frontend/output/playwright/mobile-forecast.png` | `frontend/src/pages/ForecastPage.states.test.tsx` | forecast is shown as flagship feature | move to mobile-first forecast layout and visual polish |
| features/news-digest-chat.md | `/news` | implemented_mvp | `backend/app/services/news_service.py`, `backend/app/services/chat_service.py`, `backend/app/api/v1/news.py`, `backend/app/api/v1/chat.py`, `frontend/src/pages/NewsPage.tsx` | `backend/tests/test_news_api.py`, `backend/tests/test_chat_api.py`, `frontend/src/features/news/components/NewsDigestPanel.test.tsx`, `frontend/src/features/news/components/ChatThread.test.tsx` | analyst opens digest and asks cited question | replace fixture news + `template_rag` with real ingest + retrieval-first ladder |
| screens/screen-news-digest-chat.md | `/news` | partial | `frontend/src/pages/NewsPage.tsx`, `frontend/src/features/news/components/CitationList.tsx`, `frontend/src/features/news/components/NewsSearchDrawer.tsx` | news component tests, future e2e | commission sees digest, citations and provider badges | add provider badges, retrieval-only messaging and mobile-specific layout |

## Execution Notes
1. `implemented + worktree` означает, что код уже содержит важные улучшения, но README/docs могут ещё отставать от текущего среза.
2. `implemented_mvp` означает, что capability работает, но runtime ещё не соответствует целевому v2 contract.
3. Для следующей крупной кодовой задачи use this file as:
   - doc-to-code map;
   - quick test index;
   - demo planning sheet.
