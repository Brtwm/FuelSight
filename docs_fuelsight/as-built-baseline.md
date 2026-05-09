# FuelSight As-Built Baseline

## Назначение
Этот документ фиксирует реальное `as-built` состояние репозитория на текущем срезе и нужен как основной ответ на вопросы:
- что уже реализовано;
- что реализовано и подтверждено кодом/тестами;
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
- `partial`: capability есть фрагментарно или без нужного polish/responsive/ops слоя.
- `docs_only`: решение описано в `docs_fuelsight_2`, но ещё не реализовано в рантайме.
- `blocked_external`: capability реализована, но полная compose-проверка зависит от внешнего окружения.

## Mandatory Sync Rule
При любом изменении code capability, статуса фазы, demo story или пользовательского контракта в одном PR/срезе синхронно обновляются:
- `memory-bank/*` как operational continuity layer;
- релевантные документы в `docs_fuelsight/*` как as-built описание;
- `docs_fuelsight_2/phase0-gap-matrix.md` как doc-to-code/test/demo map.

`README.md` остаётся кратким capability snapshot и не используется как phase tracker.

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
| Realistic initial data hooks | implemented | generator, feature store, pipeline | `backend/app/services/data_generator.py`, `backend/app/pipeline/tasks.py`, `scripts/run_full_demo.py` | `scripts/last-smoke-result.json`, `backend/tests/test_pipeline_tasks.py` | demo-chain генерирует rolling окно до текущей даты, чтобы dashboard/analytics/forecast открывались на фактических данных |
| CatBoost-first forecast UX and meta | implemented | `/forecast`, `/api/v1/forecasts/*`, `/api/v1/backtests/*` | `backend/app/services/forecast_service.py`, `backend/app/pipeline/tasks.py`, `frontend/src/pages/ForecastPage.tsx` | `backend/tests/test_forecast_api.py`, `backend/tests/test_forecast_service.py`, `frontend/src/pages/ForecastPage.states.test.tsx` | richer meta, manifests и `base vs scenario` закреплены contract tests |
| News digest and search | implemented | `/news`, `/api/v1/news/*` | `backend/app/services/news_service.py`, `backend/app/integrations/news/*`, `frontend/src/pages/NewsPage.tsx` | `backend/tests/test_news_api.py`, `backend/tests/test_news_integrations.py`, `frontend/src/features/news/components/NewsDigestPanel.test.tsx` | runtime переведён на real-provider baseline с cache/manual snapshot ladder |
| Chat with citations | implemented | `/api/v1/chat/*`, `/news` | `backend/app/services/chat_service.py`, `backend/app/services/chat_retrieval.py`, `frontend/src/features/news/components/ChatThread.tsx` | `backend/tests/test_chat_api.py`, `backend/tests/test_chat_service.py`, `frontend/src/features/news/components/ChatThread.test.tsx` | `LLM off` возвращает `retrieval_only` ответ с citations/evidence или честный blocked uncertainty |
| Advanced RAG quality layer | implemented | `/api/v1/chat/*`, RAG index | `backend/app/models/rag_chunk.py`, `backend/app/services/rag_index_service.py`, `backend/app/services/chat_retrieval.py` | `backend/tests/test_rag_index_contract.py`, `backend/tests/test_rag_index_service.py`, `backend/tests/test_chat_service.py` | pgvector chunks, query normalization, hybrid scoring, provider adapters, verification metadata and confidence baseline реализованы |
| Real news ingest with cache and normalized providers | implemented | `/news`, pipeline, cache | `backend/app/integrations/news/*`, `backend/app/services/news_service.py`, `backend/app/pipeline/tasks.py` | `backend/tests/test_news_api.py`, `backend/tests/test_news_service.py`, `scripts/last-smoke-result.json` | runtime использует GDELT + curated RSS/API providers с cache/manual snapshot fallback |
| Visual polish for commission | implemented | all analyst-facing routes | `frontend/src/app/layout/AppShell.tsx`, `frontend/src/components/common/*`, `frontend/src/pages/*` | `corepack pnpm --filter frontend test`, Playwright persona/device scripts | analyst path works on desktop and mobile |
| Mobile readiness | implemented | `/login`, `/dashboard`, `/forecast`, `/news` | `frontend/src/pages/*`, `frontend/src/features/forecast/components/*`, `frontend/e2e/mobile-smoke.spec.ts` | dual profile smoke (`mobile-iphone-13`, `mobile-pixel-7`) + screenshots in `frontend/output/playwright/*` | targeted Phase B scope закрыт |
| Defense mode and executive outputs | blocked_external | `scripts/run_full_demo.py`, export/reporting | profile-driven runner, `build-defense-report`, defense JSON/PDF, health badges, compose profiles | `backend/tests/test_defense_report_service.py`, `backend/tests/test_pipeline_tasks.py`, `backend/tests/test_run_full_demo.py` | implemented; container smoke remains blocked by Debian apt mirror during backend rebuild |

## Route Coverage Snapshot
| route | current as-built state | main evidence |
| --- | --- | --- |
| `/login` | analyst-first login, session refresh, preferred landing route | `frontend/src/pages/LoginPage.tsx`, `frontend/src/features/auth/components/LoginForm.tsx` |
| `/import` | admin-only operational panels + diagnostics drawer | `frontend/src/pages/ImportPage.tsx` |
| `/dashboard` | KPI cards + demand snapshot + business summary + freshness badges + mobile-first reading order | `frontend/src/pages/DashboardPage.tsx`, `frontend/src/features/kpi/components/DemandSnapshotChart.tsx` |
| `/analytics/sales` | explainable chart + seasonality + comparisons + anomalies | `frontend/src/pages/SalesAnalyticsPage.tsx` |
| `/analytics/margin` | risk-aware margin chart + low margin selection + reason panel | `frontend/src/pages/MarginAnalyticsPage.tsx` |
| `/forecast` | base/scenario forecast + health summary + backtest + responsive values view (`table`/`cards`) | `frontend/src/pages/ForecastPage.tsx`, `frontend/src/features/forecast/components/ForecastChart.tsx` |
| `/news` | real-provider digest/search + verified retrieval chat, confidence/verification badges, mobile order `digest -> chat -> search` | `frontend/src/pages/NewsPage.tsx`, `backend/app/services/news_service.py`, `backend/app/services/chat_service.py` |

## Confirmed Verification Snapshot
| verification | result | interpretation |
| --- | --- | --- |
| `uv run pytest` | `176 passed, 2 skipped` на последнем полном backend snapshot | backend contracts, pipeline, news/chat, forecast and defense slices проходят baseline |
| `uv run pytest tests/test_news_api.py tests/test_news_service.py tests/test_news_integrations.py tests/test_chat_api.py tests/test_pipeline_tasks.py` | `17 passed` | real-news ingest, API compatibility и pipeline manifest flow подтверждены |
| `corepack pnpm --filter frontend test` | `38 files / 109 tests passed` на последнем полном frontend snapshot | frontend shared components, route states and badge/status integration проходят suite |

## Known Mismatches To Keep Visible
1. `README.md` больше не должен описывать состояние через fixed phase-label; фактическое состояние capability-based и синхронизируется через `memory-bank` + `docs_fuelsight` + `phase0-gap-matrix.md`.
2. `docs_fuelsight_2/v2-roadmap.md` раньше описывал roadmap phases `1-7`, но текущая рабочая стратегия уже включает отдельные треки `visual/mobile`, `real news`, `RAG chat`, `defense`.
3. `news` ingest больше не использует fixture в runtime; `chat` больше не падает при `LLM off`, а возвращает `retrieval_only` или blocked uncertainty.
4. `forecast` capability глубже, чем отражено в старых верхнеуровневых docs: manifests, provider summaries и richer health fields уже есть.
5. Full demo-chain сейчас строит данные до текущей даты и запускает `external_indicators_refresh -> build_feature_store -> train_models_weekly -> news_refresh`; старые инструкции с фиксированным окном `2025-01-01..2025-12-31` считать устаревшими.
6. Offline-safe `manual_snapshot` является плановым локальным контуром для защиты: при полном покрытии он отображается как качественный проверенный контекст, без пользовательских labels про demo/generated/snapshot.

## Immediate Use
Перед любой новой большой задачей:
1. Сверяйся с этим документом как с `as-built baseline`.
2. Смотри `docs_fuelsight_2/v2-roadmap.md` как на target-plan.
3. Используй `docs_fuelsight_2/phase0-gap-matrix.md` как execution backlog и doc-to-code map.
