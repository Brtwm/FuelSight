# FuelSight As-Built Baseline

## Назначение
Этот документ фиксирует реальное `as-built` состояние репозитория на текущем срезе и нужен как основной ответ на вопросы:
- что уже реализовано;
- что реализовано, но ещё находится в `worktree`;
- что пока существует только как `target` в `docs_fuelsight_2/`.

Документ intentionally capability-based и не опирается на phase-label как на единственный источник истины.

## Порядок источников истины
Если документы расходятся между собой, использовать следующий приоритет:
1. явный запрос пользователя;
2. `AGENTS.md`;
3. `memory-bank/*`;
4. кодовая база;
5. `docs_fuelsight/*`;
6. `README.md`.

## Легенда статусов
- `implemented`: подтверждено кодом и поддерживается текущим baseline.
- `implemented_mvp`: работает, но ещё не соответствует целевому v2-поведению.
- `implemented + worktree`: capability уже есть, но важная часть улучшений ещё не зафиксирована коммитом.
- `partial`: capability есть фрагментарно или без нужного polish/responsive/ops слоя.
- `docs_only`: решение описано в `docs_fuelsight_2`, но ещё не реализовано в рантайме.

## Capability Matrix
| capability | current_status | primary routes / scope | evidence in code | evidence in tests / docs | note |
| --- | --- | --- | --- | --- | --- |
| Auth, roles, session refresh | implemented | `/login`, `/api/v1/auth/*` | `backend/app/api/v1/auth.py`, `frontend/src/features/auth/*` | `backend/tests/test_auth_api.py`, `frontend/src/pages/LoginPage.integration.test.tsx` | `preferred_landing_route` уже добавлен, analyst-first default включён |
| Admin import operations | implemented | `/import`, `/api/v1/import/*` | `backend/app/api/v1/imports.py`, `frontend/src/pages/ImportPage.tsx` | `backend/tests/test_import_api.py`, `frontend/src/pages/ImportPage.integration.test.tsx` | admin-only diagnostics и neutral labels уже есть |
| KPI dashboard with enriched meta | implemented | `/dashboard`, `/api/v1/kpi/*` | `backend/app/api/v1/kpi.py`, `backend/app/api/v1/meta_builders.py`, `frontend/src/pages/DashboardPage.tsx` | `backend/tests/test_kpi_api.py`, `frontend/src/pages/DashboardPage.states.test.tsx` | business summary, annotations and overlays приходят готовым контрактом |
| Sales analytics explainable slice | implemented | `/analytics/sales`, `/api/v1/analytics/sales` | `backend/app/api/v1/analytics.py`, `frontend/src/pages/SalesAnalyticsPage.tsx` | `backend/tests/test_analytics_api.py`, `frontend/src/pages/SalesAnalyticsPage.states.test.tsx` | URL filters и shared meta есть, но visual/mobile polish ещё нужен |
| Margin analytics explainable slice | implemented | `/analytics/margin`, `/api/v1/analytics/margin` | `backend/app/api/v1/analytics.py`, `frontend/src/pages/MarginAnalyticsPage.tsx` | `backend/tests/test_analytics_api.py`, `frontend/src/pages/MarginAnalyticsPage.states.test.tsx` | risk panel and threshold explanation уже есть |
| Shared frontend primitives | implemented | shared UI layer | `frontend/src/components/common/*`, `frontend/src/app/layout/AppShell.tsx` | component tests for `ChartCard`, `DataStatePanel`, `FreshnessBadgeGroup`, `SourceModeBadge` | AppShell slot/status injection уже работает |
| External indicators schema + ingest foundation | implemented | backend integrations and pipeline | `backend/app/models/external_indicator_daily.py`, `backend/app/services/external_indicators_service.py`, `backend/app/integrations/external_indicators/*` | `backend/alembic/versions/20260408_0005_phase0_external_indicators.py`, `backend/tests/test_pipeline_tasks.py` | live/cache/manual snapshot ladder уже реализован |
| Realistic initial data hooks | partial | generator, feature store, pipeline | `backend/app/services/data_generator.py`, `backend/app/pipeline/tasks.py` | `memory-bank/activeContext.md`, `backend/tests/test_pipeline_tasks.py` | external context уже подключается к forecasting, но realism-story ещё надо дожать в docs и demo |
| CatBoost-first forecast UX and meta | implemented + worktree | `/forecast`, `/api/v1/forecasts/*`, `/api/v1/backtests/*` | `backend/app/services/forecast_service.py`, `backend/app/pipeline/tasks.py`, `frontend/src/pages/ForecastPage.tsx` | `backend/tests/test_forecast_api.py`, `backend/tests/test_forecast_service.py`, `frontend/src/pages/ForecastPage.states.test.tsx` | richer meta, manifests и `base vs scenario` уже есть, но docs sync и final smoke ещё нужны |
| News digest and search | implemented_mvp | `/news`, `/api/v1/news/*` | `backend/app/services/news_service.py`, `frontend/src/pages/NewsPage.tsx` | `backend/tests/test_news_api.py`, `frontend/src/features/news/components/NewsDigestPanel.test.tsx` | runtime всё ещё строится на fixture-news, а не на real providers |
| Chat with citations | implemented_mvp | `/api/v1/chat/*`, `/news` | `backend/app/services/chat_service.py`, `backend/app/api/v1/chat.py`, `frontend/src/features/news/components/ChatThread.tsx` | `backend/tests/test_chat_api.py`, `frontend/src/features/news/components/ChatThread.test.tsx` | citations обязательны, но текущий режим `template_rag` и `LLM off -> 503` не соответствует v2 |
| Retrieval-first fallback chat | docs_only | `/news`, `/api/v1/chat/*` | target: `backend/app/integrations/llm/*`, `backend/app/services/chat_service.py` | `docs_fuelsight_2/features/news-digest-chat.md`, `docs_fuelsight_2/project/backend/api-endpoints.md` | целевой режим: `cloud_llm -> local_llm -> retrieval_only` |
| Real news ingest with cache and normalized providers | docs_only | `/news`, pipeline, cache | target: `backend/app/integrations/news/*`, `backend/app/services/news_service.py`, `backend/app/pipeline/tasks.py` | `docs_fuelsight_2/integrations-and-data-sources.md` | Phase F/G target, в рантайме ещё не начато |
| Visual polish for commission | partial | all analyst-facing routes | `frontend/src/theme/theme.ts`, page-level layouts | mobile screenshots under `frontend/output/playwright/*` | UI уже читаем на desktop, но mobile shell/layout ещё явно desktop-first |
| Mobile readiness | partial | `/login`, `/dashboard`, `/forecast`, `/news` | current layouts in `frontend/src/pages/*`, `frontend/src/app/layout/AppShell.tsx` | local screenshots show mixed results | mobile should become separate tracked slice, not hidden inside generic frontend work |
| Defense mode and executive outputs | docs_only | `scripts/run_full_demo.py`, export/reporting | partial base exists in `scripts/run_full_demo.py` | `docs_fuelsight_2/operability-and-defense-mode.md` | current smoke runner exists, but full defense report/export story ещё не реализованы |

## Route Coverage Snapshot
| route | current as-built state | main evidence |
| --- | --- | --- |
| `/login` | analyst-first login, session refresh, preferred landing route | `frontend/src/pages/LoginPage.tsx`, `frontend/src/features/auth/components/LoginForm.tsx` |
| `/import` | admin-only operational panels + diagnostics drawer | `frontend/src/pages/ImportPage.tsx` |
| `/dashboard` | KPI cards + demand snapshot + business summary + freshness badges | `frontend/src/pages/DashboardPage.tsx` |
| `/analytics/sales` | explainable chart + seasonality + comparisons + anomalies | `frontend/src/pages/SalesAnalyticsPage.tsx` |
| `/analytics/margin` | risk-aware margin chart + low margin selection + reason panel | `frontend/src/pages/MarginAnalyticsPage.tsx` |
| `/forecast` | base/scenario forecast + model health + backtest summary + table | `frontend/src/pages/ForecastPage.tsx` |
| `/news` | digest + search + chat shell with citations, but still MVP news/chat backend behavior | `frontend/src/pages/NewsPage.tsx`, `backend/app/services/news_service.py`, `backend/app/services/chat_service.py` |

## Confirmed Verification Snapshot
| verification | result | interpretation |
| --- | --- | --- |
| `uv run pytest tests/test_forecast_api.py tests/test_forecast_service.py tests/test_pipeline_tasks.py` | `11 passed` | forecast/pipeline worktree slice подтверждён точечными backend tests |
| `uv run pytest tests/test_news_api.py tests/test_chat_api.py` | `8 passed` | current MVP news/chat contracts работают как задокументированный baseline |
| `corepack pnpm --filter frontend test` | `35 files / 92 tests passed` | frontend shared components and route states проходят suite |

## Known Mismatches To Keep Visible
1. `README.md` больше не должен описывать состояние через `Phase 9 complete`; фактическое состояние capability-based и частично опережает старую формулировку.
2. `docs_fuelsight_2/v2-roadmap.md` раньше описывал roadmap phases `1-7`, но текущая рабочая стратегия уже включает отдельные треки `visual/mobile`, `real news`, `RAG chat`, `defense`.
3. `news/chat` в коде уже имеют schemas и tests под richer contracts, но runtime всё ещё использует fixture ingest и `template_rag`.
4. `forecast` capability глубже, чем отражено в старых верхнеуровневых docs: manifests, provider summaries и richer health fields уже есть.
5. Mobile story недостаточно формализована в старом roadmap, хотя для защиты это now critical path.

## Immediate Use
Перед любой новой большой задачей:
1. Сверяйся с этим документом как с `as-built baseline`.
2. Смотри `docs_fuelsight_2/v2-roadmap.md` как на target-plan.
3. Используй `docs_fuelsight_2/phase0-gap-matrix.md` как execution backlog и doc-to-code map.
