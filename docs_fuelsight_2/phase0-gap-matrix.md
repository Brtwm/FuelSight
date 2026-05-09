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
- `partial`
- `docs_only`
- `blocked_external`

## Mandatory Sync Rule
Любое изменение code capability, API payload, demo story, Phase status или supported degraded mode должно в том же срезе обновлять `memory-bank/*`, релевантные `docs_fuelsight/*` и этот `phase0-gap-matrix.md`. `README.md` остаётся кратким capability snapshot и не заменяет source-of-truth документы.

## Cross-Cutting Track
| doc_item | scope | current_status | current_code_modules | test_target | demo_scenario | next_slice |
| --- | --- | --- | --- | --- | --- | --- |
| project-idea.md | whole product baseline | implemented | `README.md`, `docs_fuelsight/project-idea.md`, `memory-bank/projectbrief.md` | manual docs review | explain product scope to commission | keep as-built and target docs separated |
| project/frontend/frontend-docs.md | frontend architecture | implemented | `frontend/src/app/layout/AppShell.tsx`, `frontend/src/components/common/*`, `frontend/src/pages/*`, `frontend/playwright.config.ts` | `pnpm test` (`112 passed`), `pnpm build`, split Playwright persona/device scripts | show Cinematic Dark analyst UI narrative on desktop + mobile | keep split E2E and screenshot artifacts stable |
| project/backend/backend-docs.md | backend architecture | implemented | `backend/app/api/v1/*`, `backend/app/services/*`, `backend/app/integrations/*`, `backend/app/pipeline/tasks.py`, `backend/app/models/rag_chunk.py` | `uv run pytest`, `backend/tests/test_phase_k_enriched_payload_contracts.py` | explain API/domains/pipeline/RAG/defense structure | keep contracts and docs sync guarded by Phase K tests |
| project/backend/api-endpoints.md | API contract | implemented | `backend/app/schemas/*`, `backend/app/api/v1/*`, `frontend/src/lib/api/*.types.ts` | targeted API suites, `backend/tests/test_phase_k_enriched_payload_contracts.py` | demonstrate envelope + enriched meta | preserve enriched payload contract across KPI/analytics/forecast/news/chat/health |
| integrations-and-data-sources.md | external providers and cache strategy | implemented | `backend/app/integrations/external_indicators/*`, `backend/app/integrations/news/*`, `backend/app/integrations/llm/*`, `backend/app/services/chat_retrieval.py` | `backend/tests/test_pipeline_tasks.py`, `backend/tests/test_chat_service.py`, `backend/tests/test_llm_integrations.py` | explain live/cache/manual snapshot story and verified retrieval ladder; offline-safe UI labels it as verified quality context | keep offline-safe fallback mandatory |
| operability-and-defense-mode.md | smoke/ops/defense | blocked_external | `scripts/run_full_demo.py`, `backend/app/pipeline/tasks.py`, `backend/app/services/defense_report_service.py` | `backend/tests/test_defense_report_service.py`, `backend/tests/test_run_full_demo.py` | run local demo prep and produce JSON/PDF defense report | repeat compose smoke after Debian apt mirror is available |

## Feature And Screen Backlog
| doc_item | route | current_status | current_code_modules | test_target | demo_scenario | next_slice |
| --- | --- | --- | --- | --- | --- | --- |
| features/auth.md | `/login` | implemented | `backend/app/api/v1/auth.py`, `backend/app/schemas/auth.py`, `frontend/src/pages/LoginPage.tsx`, `frontend/src/features/auth/components/LoginForm.tsx` | `backend/tests/test_auth_api.py`, `frontend/src/pages/LoginPage.integration.test.tsx` | analyst logs in and lands on `/dashboard` | keep current baseline, no large code changes needed before next slice |
| screens/screen-login.md | `/login` | implemented | `frontend/src/pages/LoginPage.tsx`, `frontend/src/theme/theme.ts`, `frontend/e2e/mobile-smoke.spec.ts` | `frontend/src/pages/LoginPage.integration.test.tsx`, `pnpm test`, `corepack pnpm --filter frontend test:e2e:mobile` | cinematic dark login demo | keep login defaults stable for analyst/admin demos |
| features/data-import.md | `/import` | implemented | `backend/app/api/v1/imports.py`, `backend/app/schemas/imports.py`, `frontend/src/pages/ImportPage.tsx`, `frontend/src/features/import/components/ImportJobsTable.tsx` | `backend/tests/test_import_api.py`, `frontend/src/pages/ImportPage.integration.test.tsx` | admin refreshes initial history and opens diagnostics | keep as-built docs synced with neutral copy and admin-only diagnostics |
| screens/screen-data-import.md | `/import` | implemented | `frontend/src/pages/ImportPage.tsx`, `frontend/src/components/common/DiagnosticsDrawer.tsx` | `frontend/src/pages/ImportPage.integration.test.tsx`, `frontend/e2e/admin-operational-flow.spec.ts` | admin operational flow | add responsive layout notes for tablet/mobile admin view |
| features/kpi-dashboard.md | `/dashboard` | implemented | `backend/app/api/v1/kpi.py`, `backend/app/api/v1/meta_builders.py`, `frontend/src/pages/DashboardPage.tsx` | `backend/tests/test_kpi_api.py`, `frontend/src/pages/DashboardPage.states.test.tsx` | analyst opens KPI overview | keep URL-synced filters + explainability copy stable for defense narrative |
| screens/screen-kpi-dashboard.md | `/dashboard` | implemented | `frontend/src/pages/DashboardPage.tsx`, `frontend/src/features/kpi/components/DemandSnapshotChart.tsx`, `frontend/src/app/layout/AppShell.tsx` | `frontend/src/pages/DashboardPage.states.test.tsx`, `frontend/src/features/kpi/components/DemandSnapshotChart.test.tsx`, `corepack pnpm --filter frontend test:e2e:mobile` | commission sees KPI summary and badges on phone width without layout breakage | keep badge/degraded state tests current |
| features/sales-analytics.md | `/analytics/sales` | implemented | `backend/app/api/v1/analytics.py`, `backend/app/schemas/analytics.py`, `frontend/src/pages/SalesAnalyticsPage.tsx` | `backend/tests/test_analytics_api.py`, `frontend/src/pages/SalesAnalyticsPage.states.test.tsx` | analyst analyzes demand dynamics | maintain explainability state quality and real-data clarity |
| screens/screen-sales-analytics.md | `/analytics/sales` | implemented | `frontend/src/pages/SalesAnalyticsPage.tsx`, `frontend/src/features/sales/components/*` | `frontend/src/pages/SalesAnalyticsPage.states.test.tsx`, `frontend/e2e/analyst-first-flow.spec.ts` | analyst reviews sales page | preserve compact rhythm and legend readability |
| features/procurement-margin.md | `/analytics/margin` | implemented | `backend/app/api/v1/analytics.py`, `frontend/src/pages/MarginAnalyticsPage.tsx`, `frontend/src/features/margin/components/*` | `backend/tests/test_analytics_api.py`, `frontend/src/pages/MarginAnalyticsPage.states.test.tsx`, `frontend/src/pages/MarginAnalyticsPage.selection.test.tsx` | analyst investigates low-margin day | keep thresholds/supporting refs language stable |
| screens/screen-procurement-margin.md | `/analytics/margin` | implemented | `frontend/src/pages/MarginAnalyticsPage.tsx` | `frontend/src/pages/MarginAnalyticsPage.states.test.tsx`, `frontend/e2e/analyst-first-flow.spec.ts` | margin risk explanation | keep selection flow and mobile cards coherent under live/cached/degraded modes |
| features/demand-forecast.md | `/forecast` | implemented | `backend/app/services/forecast_service.py`, `backend/app/pipeline/tasks.py`, `frontend/src/pages/ForecastPage.tsx`, `frontend/src/features/forecast/components/*` | `backend/tests/test_forecast_api.py`, `backend/tests/test_forecast_service.py`, `frontend/src/pages/ForecastPage.states.test.tsx` | analyst runs base/scenario forecast and reads model health | preserve enriched health/provider/baseline/meta contracts |
| screens/screen-demand-forecast.md | `/forecast` | implemented | `frontend/src/pages/ForecastPage.tsx`, `frontend/src/features/forecast/components/ForecastChart.tsx`, `frontend/src/features/forecast/components/ForecastControlPanel.tsx` | `frontend/src/pages/ForecastPage.states.test.tsx`, `frontend/src/features/forecast/components/ForecastChart.test.tsx`, `corepack pnpm --filter frontend test:e2e:mobile` | forecast is shown as flagship feature on desktop and mobile | monitor compact table readability after real-data rehearsal |
| features/news-digest-chat.md | `/news` | implemented | `backend/app/services/news_service.py`, `backend/app/services/chat_service.py`, `backend/app/services/chat_retrieval.py`, `backend/app/services/rag_index_service.py`, `backend/app/api/v1/chat.py`, `frontend/src/pages/NewsPage.tsx` | `backend/tests/test_news_api.py`, `backend/tests/test_chat_api.py`, `backend/tests/test_chat_service.py`, `frontend/src/features/news/components/ChatThread.test.tsx` | analyst opens digest and asks cited verified question | keep confidence/verification/provider behavior stable |
| screens/screen-news-digest-chat.md | `/news` | implemented | `frontend/src/pages/NewsPage.tsx`, `frontend/src/features/news/components/NewsSearchDrawer.tsx`, `frontend/e2e/mobile-smoke.spec.ts` | `frontend/src/features/news/components/NewsDigestPanel.test.tsx`, `frontend/src/features/news/components/NewsSearchDrawer.test.tsx`, `corepack pnpm --filter frontend test:e2e:mobile` | commission sees digest, citations and page-level provider badges in mobile reading order | keep retrieval-mode UX aligned with page-level health badges |

## Execution Notes
1. `implemented_mvp` означает, что capability работает, но runtime ещё не соответствует целевому v2 contract.
2. `blocked_external` означает, что код реализован, но полная проверка зависит от внешнего окружения или сети.
3. Для следующей крупной кодовой задачи use this file as:
   - doc-to-code map;
   - quick test index;
   - demo planning sheet.
