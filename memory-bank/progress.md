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

## Testing Evidence
- Backend:
  - `uv run pytest` -> `104 passed`.
- Frontend:
  - `corepack pnpm --filter frontend test` -> `37 files / 101 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
- E2E:
  - `corepack pnpm --filter frontend exec playwright test --project=chromium --project=iphone-13 --project=pixel-7`
  - desktop + mobile flows green (`4 passed`, project-specific skips expected).

## Remaining Work
- Next product slice: `Phase D. Data Realism + External Context Hardening`.
- После Phase D: `Phase E. CatBoost-First Forecast Finalization`.
- News/RAG track (`Phase F/G`) остаётся следующим крупным контуром после data/forecast hardening.

## Known Gaps
- News/chat runtime по-прежнему MVP (`fixture ingest`, `template_rag`, `LLM off -> 503` для generation path).
- Screenshot artifacts в `frontend/output/playwright/` часто меняются после mobile smoke и требуют отдельного контроля перед commit.
