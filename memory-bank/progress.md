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

## Testing Evidence
- Backend:
  - `uv run pytest` -> `114 passed`.
- Frontend:
  - `corepack pnpm --filter frontend test` -> `37 files / 102 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
- E2E:
  - `corepack pnpm --filter frontend exec playwright test --project=chromium --project=iphone-13 --project=pixel-7`
  - desktop + mobile flows green (`4 passed`, project-specific skips expected).

## Remaining Work
- Next product slice: `Phase G. RAG-First Chat Core`.
- После Phase G: `Phase H/I` quality layer и cloud/local retrieval ladder.
- Defense/export track (`Phase J`) остаётся после стабилизации chat mode contracts.

## Known Gaps
- Chat runtime по-прежнему MVP (`template_rag`, `LLM off -> 503` для generation path), хотя digest/search уже работают поверх реальных `news_raw`.
- Screenshot artifacts в `frontend/output/playwright/` часто меняются после mobile smoke и требуют отдельного контроля перед commit.
