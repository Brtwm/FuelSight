# Active Context

## Current Focus
- На 2026-04-18 закрыт `Phase B. Visual Polish + Mobile Readiness` в worktree.
- Основной UX-blocker (`AppShell` desktop-only drawer) снят: mobile теперь работает через `bottom navigation + temporary drawer`.
- В analyst-critical маршрутах (`/login`, `/dashboard`, `/forecast`, `/news`) внедрён mobile-first порядок чтения и compact visual rules.

## Worktree Snapshot
- `frontend/src/app/layout/AppShell.tsx`
  - hybrid navigation: desktop `permanent drawer`, mobile `temporary drawer + bottom nav`;
  - compact top status row (`freshness/source/health/session`) для малой ширины;
  - route-aware selection для `/analytics/*` и key analyst routes.
- `frontend/src/pages/DashboardPage.tsx`
  - mobile-first sequence: summary + alerts перед chart на узкой ширине.
- `frontend/src/pages/ForecastPage.tsx`
  - health summary перед chart;
  - responsive forecast values (`desktop table` + `mobile cards`).
- `frontend/src/pages/NewsPage.tsx`
  - mobile order `digest -> chat -> search`.
- `frontend/src/features/forecast/components/ForecastChart.tsx`
  - compact legend labels + hidden interval series by default on `<= sm`.
- `frontend/src/features/kpi/components/DemandSnapshotChart.tsx`
  - compact labels, overlay toggle defaults и summary above chart.
- `frontend/playwright.config.ts`
  - добавлены mobile projects: `iphone-13`, `pixel-7`.
- `frontend/e2e/mobile-smoke.spec.ts`
  - mobile smoke flow `login -> dashboard -> forecast -> news` + screenshots.
- `scripts/run_full_demo.py`
  - новый optional флаг `--with-mobile-e2e`.

## What Was Verified Today
- `corepack pnpm --filter frontend test -- ...` (фактически весь suite) -> `37 files / 100 tests passed`.
- `corepack pnpm --filter frontend build` -> `PASS`.
- `corepack pnpm --filter frontend test:e2e:mobile` -> `PASS` (`iphone-13`, `pixel-7`).
- `corepack pnpm --filter frontend exec playwright test --project=chromium` -> `PASS` (desktop analyst/admin), `mobile-smoke` корректно `skipped`.

## Next Likely Steps
- Досинхронизировать forecast contracts/docs после текущего worktree refinement (`model_freshness`, `baseline_comparison`, `provider_mode`, `training_window`).
- Перейти к следующему большому product slice: `Phase F. Real News Ingestion Baseline`.
- Затем открыть `Phase G. RAG-First Chat Core` (retrieval-first ladder и non-failing behavior при `LLM off`).

## Active Decisions
- Analyst-first narrative остаётся основным demo path.
- Mobile readiness больше не считается optional polish; это обязательная часть defense story.
- Core flow (`import`, `kpi`, `analytics`, `forecast`) остаётся независимым от LLM.
- Chat target pattern не менялся: `stateful verified RAG`, не autonomous web agent.

## Risks To Remember
- Часть forecasting improvements всё ещё в worktree и требует отдельной фиксации в commit/docs.
- Mobile smoke зависит от установленных Playwright browsers (особенно WebKit для `iphone-13`).
- News/chat runtime пока остаётся MVP-level (`fixture ingest`, `template_rag`), несмотря на улучшенный UI-shell.
