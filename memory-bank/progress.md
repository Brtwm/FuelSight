# Progress

## Stable Baseline
- Core MVP flow стабилен: `login -> import/demo-data -> dashboard -> sales -> margin -> forecast`, бонусный `/news` доступен.
- Top-level backend groups и envelope `{ data, error, meta }` не менялись.
- `Phase A` contracts/docs baseline зафиксирован в capability-matrix формате.

## Newly Completed Slices

### P2 (Production-Readiness Polishing)
- Shared chart logic добавлен без создания отдельного chart framework:
  - общий `frontend/src/lib/charts/chartOptions.ts` покрывает chart heights, axis/date formatting, tooltip shell, legend defaults, `dataZoom` и единицы измерения;
  - `DemandSnapshotChart`, `SalesTrendChart`, `PriceVsMarginChart`, `ForecastChart` используют общий слой, сохраняя P0-3 improvements: dark palette, custom tooltip, desktop dataZoom, forecast confidence area band and Russian labels.
- `/import` получил фактический drag-and-drop upload:
  - file picker fallback сохранён;
  - добавлены состояния drag-active, selected file, uploading/error through existing mutation flow;
  - frontend early validation mirrors backend defaults: CSV/XLSX, 10 MiB, 50 000 rows.
- UX copy polish:
  - runtime UI больше не предлагает пользователю проверять `backend`;
  - provider/source chips используют business copy вроде `сохранённые данные`, `проверено`, `по источникам`.
- Backend refactor выполнен минимально:
  - чистые analytics helpers вынесены в `backend/app/services/analytics_helpers.py`;
  - public `AnalyticsService` static method facade сохранён для совместимости tests/imports.

### Phase B (Visual Polish + Mobile Readiness)
- `AppShell` переведён на responsive hybrid navigation (`permanent drawer` desktop, `temporary drawer + bottom nav` mobile).
- P0-2 `AppShell Cleanup` закрыт: top bar теперь содержит только продуктовую навигационную основу, роль и `Выйти`; global health/provider/freshness badges и `AppShellSlotsContext` удалены.
- Mobile-first reading order внедрён для `/login`, `/dashboard`, `/forecast`, `/news`.
- P1-2 News/Chat UX закреплён contract tests: mobile tabs `[Сводка | Поиск | Чат]`, desktop digest/search + sticky chat, fixed chat pane and chat auto-scroll/disabled-send behavior.
- Dual mobile Playwright profile (`iphone-13`, `pixel-7`) добавлен и используется в smoke flow.

### Phase C (Explainable Analytics Completion) + Phase A Gate Fix
- Backend KPI/analytics migrated to `meta.explainability`:
  - `summary`;
  - `chart.annotations|overlays|thresholds|supporting_refs`;
  - `trust` (`data_freshness`, `mode`, `data_mode`);
  - `state` (`ready|empty|degraded|error`, reason).
- `dashboard`, `sales`, `margin` приведены к единому explainable design system:
  - `ChartCard`, `BusinessSummaryCard`, `FreshnessBadgeGroup`, `DataStatePanel`.
- Role-aware empty/degraded states:
  - `admin` -> operational CTA (`/import`);
  - `analyst` -> объяснение + ожидание обновления.
- Sales/margin mobile blocks получили compact card/table rhythm.
- `dashboard` filters переведены на URL sync.
- Matrix consistency test updated to current backlog strategy (cross-cutting + feature/screen rows).

### Phase D (Data Realism + External Context Hardening)
- `external_indicators_daily` и `event_catalog` подтверждены как рабочий baseline.
- Pipeline quality/fallback manifests и `external_context` contracts реально подключены к KPI, analytics, forecast и news.
- Offline-safe ladder `live -> cached -> manual_snapshot` закреплён и покрыт тестами.

### Phase E (CatBoost-First Forecast Finalization)
- `/forecast` уже даёт `base vs scenario`, `model_freshness`, `retrain_status`, `provider_mode` и enriched health/meta story.
- Forecast pipeline формирует deterministic manifests для feature refresh, train/backtest и model freshness.
- Статус: `implemented`; docs sync и defense-facing polish закреплены последующими Phase J/K срезами.

### Phase F (Real News Ingestion Baseline)
- Fixture ingest удалён из runtime `NewsService`; ingest теперь строится через `backend/app/integrations/news/*`.
- Добавлены реальные `news` adapters для `GDELT` и curated Russian-context RSS feeds с cache/last-good/manual snapshot ladder.
- `news_raw` расширена additive normalized fields: `provider_name`, `provider_mode`, `confidence`, `cached_at`, `metadata_json`.
- Digest builder теперь строит `news_digests` только по реально сохранённым `news_raw`.
- Добавлены pipeline step `refresh_news_daily`, CLI `refresh-news-daily` и integration в `scripts/run_full_demo.py`.
- `/news` UI теперь явно показывает `provider_mode` и `cached_at` для digest/search, без fixture assumptions.

### Phase G (RAG-First Chat Core)
- Chat API больше не возвращает `503 llm_disabled` по умолчанию при `ENABLE_LLM=false`; при наличии evidence возвращается `200` с `mode=retrieval_only`.
- Добавлен `backend/app/services/chat_retrieval.py`:
  - session-aware query context;
  - retrieval по `news_raw`, `news_digests`, `kpi`, `analytics`, `forecast`;
  - evidence pack, diagnostics и unified citations.
- `data.citations[*]` теперь несёт обязательные `provider_mode`, `confidence`, `source_type`.
- `meta.llm_provider` и `meta.retrieval` добавлены в chat response.
- Mode ladder реализован как contract/resolver без реальных cloud calls: `cloud_first/local_only/LLM off -> retrieval_only` при отсутствии adapter.
- Добавлен Airflow DAG `refresh_news_daily`, закрывающий orchestration gap Phase F.
- `/news` chat UI остаётся доступным в retrieval-only/offline-safe и показывает source mode/confidence у citations.

### Phase H (Advanced RAG Quality Layer)
- Добавлен pgvector-backed `rag_chunks` baseline и compose DB переведён на `pgvector/pgvector:pg16`.
- Добавлены query normalization, RU/EN product aliases, date hints, deterministic local embedding fallback, hybrid scoring and source diversity.
- Unsupported questions больше не получают unrelated latest-news fallback; chat возвращает blocked uncertainty response with verification metadata.
- `chat_sessions.running_summary` участвует в session memory, а `chat_messages.metadata_json` хранит confidence/verification для истории.
- `/news` chat показывает `Уверенность`, `Проверено/Не подтверждено` и даёт компактные toggles для `news_raw` и `forecast`.

### Phase I (Cloud LLM Primary + Provider-Neutral Fallback)
- Добавлен provider-neutral слой `backend/app/integrations/llm/*` для `chat`, `embed_texts`, `rerank`, `health`.
- Реализован OpenAI-compatible adapter с NeuralDeep defaults (`base_url`, chat/embedding/reranker models) и env override.
- `GigaChat` реализован как отдельный native adapter с OAuth token cache, chat completions и embeddings; rerank мягко деградирует к local scoring.
- `ChatService` теперь вызывает cloud/local synthesis только поверх evidence pack и затем прогоняет verification; provider failures возвращают cited `retrieval_only` с `fallback_verified/provider_unavailable`.
- Cloud fallback chain зафиксирован как `NeuralDeep -> GigaChat -> retrieval_only` при наличии `GIGACHAT_AUTH_KEY`.
- `/news` page-level LLM status теперь берёт режим из `/api/v1/health.data.llm_active`, а не из legacy digest `llm_mode`.
- `unsupported_claim_terms` больше не ведёт сразу к скучному blocked fallback: repairable cloud answers переводятся в `repaired`, invented numeric claims получают `fallback_verified` retrieval answer.
- `RagIndexService` и retrieval query embeddings используют provider registry с deterministic fallback.
- `/news` UI показывает provider/model/degradation из `meta.llm_provider`; mode badges переведены на русские labels.

### Phase J (Defense Mode + Executive Outputs)
- `compose/env/backend.env` очищен от committed cloud credentials; `LLM_API_KEY` и `GIGACHAT_AUTH_KEY` остаются пустыми placeholders.
- Добавлены key-optional compose profiles:
  - `compose/docker-compose.offline-safe.yml`;
  - `compose/docker-compose.cloud-enhanced.yml`.
- `scripts/run_full_demo.py` стал profile-driven:
  - `--profile offline-safe|cloud-enhanced`, default `offline-safe`;
  - offline-safe использует `manual_snapshot` для news/external indicators и `retrieval_only` для LLM;
  - cloud-enhanced использует `cloud_first`, NeuralDeep при `LLM_API_KEY`, GigaChat при `GIGACHAT_AUTH_KEY`, иначе controlled degraded `retrieval_only`;
  - Airflow DAG contract теперь включает `build_defense_report`;
  - финальный шаг пишет `scripts/last-defense-report.json`.
- Добавлен backend defense report слой без нового top-level API group:
  - `backend/app/schemas/defense.py`;
  - `backend/app/services/defense_report_service.py`;
  - `build-defense-report` в `backend/app/pipeline/tasks.py` и `backend/app/scripts/pipeline_runner.py`;
  - JSON/PDF artifacts пишутся в artifacts directory.
- Добавлен one-page PDF export через `reportlab`; backend Dockerfile получил `fonts-dejavu-core`.
- Добавлен Airflow DAG `backend/airflow/dags/build_defense_report.py`.
- `/api/v1/health` расширен defense/provider diagnostics для page-level UI status.
- `/news` и provider status UI показывают active LLM mode, provider/freshness modes и controlled degradation; `AppShell` intentionally clean и не показывает эти diagnostics в top bar.
- Добавлен `.dockerignore`, чтобы fresh Docker build не отправлял `.venv`, caches и generated artifacts в build context.
- Статус: `implemented`; локальные backend/frontend проверки зелёные, container-level smoke заблокирован внешним `apt-get update`/Debian mirror во время backend rebuild.

### Phase K (Hardening, Tests, Docs Discipline)
- Добавлены backend contract tests for enriched payloads across KPI, analytics, forecast, backtests, news, chat and health.
- Добавлен docs-sync guard, который запрещает stale claims про `Defense docs_only`, `503 llm_disabled`, old Phase I cloud status и грязный worktree.
- Playwright split переведён из `test.skip` внутри specs в explicit projects/scripts:
  - `desktop-analyst`;
  - `desktop-admin`;
  - `mobile-iphone-13`;
  - `mobile-pixel-7`.
- `scripts/run_full_demo.py` использует `test:e2e:desktop` для desktop persona flows и `test:e2e:mobile` для mobile device-class smoke.
- Mandatory sync rule закреплён: изменения code capability/status/demo story/API payload синхронно обновляют `memory-bank/*`, релевантные `docs_fuelsight/*` и `docs_fuelsight_2/phase0-gap-matrix.md`.
- Статус: `implemented`; container-level Phase J smoke по-прежнему ожидает восстановления Debian apt mirror для backend rebuild.

### Demo Data Quality Copy
- `run_full_demo.py` сохраняет полный offline-safe контур без live-зависимостей; плановый `manual_snapshot` при полном покрытии теперь классифицируется как качественный локальный контекст, а не как degraded fallback.
- Пользовательский UI больше не называет этот режим “demo/generated/snapshot”; вместо этого показывает нейтральные labels “проверенный контур” и “данные корректные”.
- Старые уже сохранённые manifests с полным покрытием нормализуются на UI/API чтении, поэтому hot-reload frontend больше не показывает красные `fallback_ratio/manual_snapshot` diagnostics до полного пересоздания контейнеров.

## Testing Evidence
- Demo data quality copy:
  - `uv run pytest tests/test_external_indicators_service.py tests/test_analytics_service.py` -> `10 passed`.
  - `uv run pytest tests/test_analytics_api.py tests/test_kpi_api.py tests/test_pipeline_tasks.py` -> `19 passed`.
  - `uv run pytest tests/test_run_full_demo.py tests/test_external_context_service.py tests/test_forecast_service.py` -> `16 passed`.
  - `uv run pytest tests/test_external_context_service.py tests/test_pipeline_tasks.py tests/test_external_indicators_service.py tests/test_analytics_service.py` -> `20 passed`.
  - `pnpm --filter frontend test -- SourceModeBadge ImportJobsTable` -> `2 files / 4 tests passed`.
  - `pnpm --filter frontend test -- DashboardPage SalesAnalyticsPage ForecastPage ModelHealthPanel` -> `3 files / 17 tests passed`.
  - `pnpm --filter frontend test -- DashboardPage SalesAnalyticsPage MarginAnalyticsPage ForecastPage SourceModeBadge ImportJobsTable` -> `7 files / 27 tests passed`.
  - `pnpm --filter frontend build` -> `PASS`.
- Frontend design overhaul 2026-05-06:
  - `pnpm test` в `frontend/` -> `39 files / 112 tests passed`.
  - `pnpm build` в `frontend/` -> `PASS`.
- P1-2 News/Chat UX hardening 2026-05-09:
  - `corepack pnpm --filter frontend exec vitest run src/pages/NewsPage.llmStatus.test.tsx src/features/news/components/ChatThread.test.tsx` -> `2 files / 13 tests passed`.
  - `corepack pnpm --filter frontend exec vitest run src/app/layout/AppShell.test.tsx` -> `1 file / 4 tests passed`.
- Backend:
  - `uv run pytest tests/test_llm_integrations.py tests/test_defense_report_service.py tests/test_pipeline_tasks.py tests/test_run_full_demo.py tests/test_health.py` -> `31 passed, 2 skipped`.
  - `uv run pytest tests/test_chat_service.py tests/test_llm_integrations.py tests/test_health.py tests/test_run_full_demo.py` -> `44 passed, 2 skipped`.
  - `uv run pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_news_api.py tests/test_news_service.py tests/test_news_integrations.py tests/test_pipeline_tasks.py tests/test_phase9_llm_off_smoke_api.py` -> `26 passed`.
  - `uv run pytest` -> `176 passed, 2 skipped`.
  - `uv run python -m app.scripts.pipeline_runner build-defense-report --profile offline-safe` against local PostgreSQL -> JSON/PDF artifacts created.
  - Docker backend build currently blocked by Debian mirror `apt-get update`; `.dockerignore` was added to keep build context small.
- Frontend:
  - `corepack pnpm --filter frontend test` -> `38 files / 109 tests passed`.
  - `corepack pnpm --filter frontend test -- src/features/news/components/ChatThread.test.tsx src/lib/api/chat.test.ts src/pages/NewsPage.llmStatus.test.tsx` -> `38 files / 109 tests passed`.
  - `corepack pnpm --filter frontend test -- src/features/news/components/ChatThread.test.tsx src/lib/api/chat.test.ts` -> `37 files / 103 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
  - `corepack pnpm --filter frontend test` -> `37 files / 102 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
- E2E:
  - `corepack pnpm --filter frontend exec playwright test --project=chromium --project=iphone-13 --project=pixel-7`
  - desktop + mobile flows green (`4 passed`, project-specific skips expected).

## Remaining Work
- Phase J container smoke нужно повторить после восстановления доступа к Debian apt mirror:
  - `python scripts/run_full_demo.py --profile offline-safe --no-build`;
  - optional cloud path: `python scripts/run_full_demo.py --profile cloud-enhanced --without-airflow --no-build`.
- Для GigaChat остаётся только live-key verification в реальном окружении; auth/token lifecycle покрыт adapter tests.
- После успешного container smoke можно считать Phase J не только `implemented`, но и `verified in compose`.

## Known Gaps
- Cloud adapter calls зависят от реального provider API/key; в тестах покрыт OpenAI-compatible request shape через mocked HTTP client.
- GigaChat live calls зависят от `GIGACHAT_AUTH_KEY`; без ключа optional live smoke tests пропускаются.
- Screenshot artifacts в `frontend/output/playwright/` часто меняются после mobile smoke и требуют отдельного контроля перед commit.
