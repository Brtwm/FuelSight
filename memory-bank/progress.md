# Progress

## Stable Baseline
- Core MVP flow стабилен: `login -> import/demo-data -> dashboard -> sales -> margin -> forecast`, бонусный `/news` доступен.
- Top-level backend groups и envelope `{ data, error, meta }` не менялись.
- `Phase A` contracts/docs baseline зафиксирован в capability-matrix формате.

## Newly Completed Slices

### Phase B (Visual Polish + Mobile Readiness)
- `AppShell` переведён на responsive hybrid navigation (`permanent drawer` desktop, `temporary drawer + bottom nav` mobile).
- Mobile-first reading order внедрён для `/login`, `/dashboard`, `/forecast`, `/news`.
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
- Статус лучше считать `implemented + worktree`, так как docs sync и финальный defense-facing polish ещё остаются.

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
- `ChatService` теперь вызывает cloud/local synthesis только поверх evidence pack и затем прогоняет verification; provider failures возвращают cited `retrieval_only`.
- `unsupported_claim_terms` больше не ведёт сразу к скучному blocked fallback: repairable cloud answers переводятся в `repaired`, invented numeric claims получают `fallback_verified` retrieval answer.
- `RagIndexService` и retrieval query embeddings используют provider registry с deterministic fallback.
- `/news` UI показывает provider/model/degradation из `meta.llm_provider`; mode badges переведены на русские labels.

## Testing Evidence
- Backend:
  - `uv run pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_news_api.py tests/test_news_service.py tests/test_news_integrations.py tests/test_pipeline_tasks.py tests/test_phase9_llm_off_smoke_api.py` -> `26 passed`.
  - `uv run pytest` -> `120 passed`.
- Frontend:
  - `corepack pnpm --filter frontend test -- src/features/news/components/ChatThread.test.tsx src/lib/api/chat.test.ts` -> `37 files / 103 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
  - `corepack pnpm --filter frontend test` -> `37 files / 102 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
- E2E:
  - `corepack pnpm --filter frontend exec playwright test --project=chromium --project=iphone-13 --project=pixel-7`
  - desktop + mobile flows green (`4 passed`, project-specific skips expected).

## Remaining Work
- Next product slice: `Phase J. Defense Mode + Executive Outputs`.
- После Phase I: defense profile должен управлять `offline-safe` и `cloud-enhanced` запуском, включая provider diagnostics.
- Для GigaChat остаётся только live-key verification в реальном окружении; auth/token lifecycle покрыт adapter tests.
- Defense/export track (`Phase J`) остаётся после стабилизации chat mode contracts.

## Known Gaps
- Cloud adapter calls зависят от реального provider API/key; в тестах покрыт OpenAI-compatible request shape через mocked HTTP client.
- GigaChat live calls зависят от `GIGACHAT_AUTH_KEY`; без ключа optional live smoke tests пропускаются.
- Screenshot artifacts в `frontend/output/playwright/` часто меняются после mobile smoke и требуют отдельного контроля перед commit.
