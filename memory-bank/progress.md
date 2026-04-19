# Progress

## Stable Baseline
- Core MVP flow стабилен: `login -> import/demo-data -> dashboard -> sales -> margin -> forecast`, бонусный `/news` доступен.
- Domain backend и response envelope contracts (`{ data, error, meta }`) не менялись.
- Phase A docs synchronization уже был выполнен и сохранён.

## Newly Completed Slice (Phase B)
- `AppShell` переведён на responsive hybrid navigation:
  - desktop: `permanent drawer`;
  - mobile/tablet: `temporary drawer + bottom navigation`.
- Mobile-first reading order внедрён для:
  - `/dashboard`;
  - `/forecast`;
  - `/news`.
- `/login` получил дополнительный mobile polish по отступам и типографике.
- Compact UI primitives:
  - `FreshnessBadgeGroup` и `SourceModeBadge` поддерживают `compact` режим.
- Mobile chart rules внедрены для:
  - `DemandSnapshotChart`;
  - `ForecastChart`.
- `/forecast` теперь имеет responsive values presentation:
  - desktop table;
  - mobile card list.

## Testing Evidence (Phase B)
- `corepack pnpm --filter frontend test` -> `37 files / 100 tests passed`.
- `corepack pnpm --filter frontend build` -> `PASS`.
- `corepack pnpm --filter frontend test:e2e:mobile` -> `PASS` (`iphone-13`, `pixel-7`).
- `corepack pnpm --filter frontend exec playwright test --project=chromium` -> `2 passed`, desktop flows не деградировали.
- Added coverage:
  - `AppShell` mobile/desktop behavior;
  - compact badges;
  - mobile forecast card rendering;
  - compact chart option rules;
  - mobile smoke spec with screenshots.

## Ops / Smoke Updates
- `frontend/playwright.config.ts` теперь содержит mobile projects (`iphone-13`, `pixel-7`).
- Добавлен `frontend/e2e/mobile-smoke.spec.ts` c сохранением скриншотов в `frontend/output/playwright/`.
- Добавлен npm script `test:e2e:mobile`.
- `scripts/run_full_demo.py` поддерживает optional флаг `--with-mobile-e2e`.

## Remaining Work
- Forecast quality/health refinement всё ещё остаётся в worktree и требует отдельной фиксации.
- Следующий функциональный этап: `Phase F. Real News Ingestion Baseline`.
- После него: `Phase G. RAG-First Chat Core`.

## Known Gaps
- News/chat runtime по-прежнему MVP (`fixture ingest`, `template_rag`, `LLM off -> 503` для generation path).
- Для demo-машин нужно гарантировать наличие Playwright WebKit для `iphone-13` профиля.
