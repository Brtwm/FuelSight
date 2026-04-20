# Active Context

## Current Focus
- На 2026-04-19 закрыт `Phase C. Explainable Analytics Completion` после `Phase A gate fix`.
- `Phase A gate fix`: matrix/docs consistency тест обновлён под текущий формат backlog (`phase0-gap-matrix` с cross-cutting + feature/screen rows).
- KPI + Analytics (`/kpi/*`, `/analytics/*`) переведены на breaking meta shape `meta.explainability.*` при сохранении envelope `{ data, error, meta }`.

## Worktree Snapshot
- `backend/app/schemas/common.py`, `backend/app/schemas/kpi.py`, `backend/app/schemas/analytics.py`
  - добавлены explainability payload models и новые meta contracts для KPI/analytics.
- `backend/app/api/v1/meta_builders.py`
  - единый explainability builder (`summary/chart/trust/state`), legacy keys для KPI/analytics удалены из финального payload.
- `backend/app/services/kpi_service.py`, `backend/app/services/analytics_service.py`
  - structured `supporting_refs` для snapshot/sales;
  - structured `thresholds` для margin;
  - meta prepared for explainability rendering.
- `frontend/src/pages/DashboardPage.tsx`
  - URL-synced filters;
  - role-aware empty/degraded states через `DataStatePanel`;
  - explainability-aware chart/summary wiring.
- `frontend/src/pages/SalesAnalyticsPage.tsx`, `frontend/src/pages/MarginAnalyticsPage.tsx`
  - unified explainable flow: chart + summary + refs/trust/state;
  - role-aware degraded/empty behavior;
  - mobile-friendly rhythm for charts/tables.
- `frontend/src/components/common/{ChartCard.tsx,DataStatePanel.tsx}`
  - `degraded` state support + optional role-aware action CTA.
- `frontend/src/features/{sales,margin}/components/*`
  - compact mobile card/table patterns for anomaly and low-margin blocks.

## What Was Verified Today
- Backend:
  - `uv run pytest` -> `104 passed`.
  - targeted suites for phase0/matrix + KPI/analytics meta contracts pass.
- Frontend:
  - `corepack pnpm --filter frontend test` -> `37 files / 101 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
- E2E:
  - `corepack pnpm --filter frontend exec playwright test --project=chromium --project=iphone-13 --project=pixel-7`
  - `4 passed / 5 skipped` (expected project-specific skips), desktop and mobile smoke/flows green.

## Next Likely Steps
- Перейти к `Phase D. Data Realism + External Context Hardening` (event catalog + external indicators quality/fallback metrics).
- После этого закрыть `Phase E. CatBoost-First Forecast Finalization` и только затем идти в `Phase F/G` news+RAG track.

## Active Decisions
- Breaking redesign ограничен `KPI + Analytics`; `forecast/news` остаются на current generic meta shape.
- Analyst-first UX сохраняется: что случилось / почему важно / можно ли доверять данным.
- Core flow (`import`, `kpi`, `analytics`, `forecast`) остаётся независимым от LLM.

## Risks To Remember
- `frontend/output/playwright/*` screenshots обновляются при mobile smoke и могут шуметь в git diff.
- Для demo-машин нужен установленный Playwright WebKit (`iphone-13` project).
- News/chat runtime всё ещё MVP (`fixture ingest`, `template_rag`) до Phase F/G.
