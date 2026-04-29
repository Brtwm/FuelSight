# QA check before Phase H/Phase I, 2026-04-29

## Scope
- Sources reviewed: `AGENTS.md`, `memory-bank/*`, `docs_fuelsight/as-built-baseline.md`, `docs_fuelsight_2/v2-roadmap.md`, backend/API/database/news/forecast docs, and current Phase H code paths.
- Runtime baseline: local core stack without Airflow.
- Browser smoke: `browser-use:browser` with `iab` backend, session `FuelSight QA`.

## Commands and results
- `python scripts/run_full_demo.py --without-airflow --no-build` -> PASS.
- `uv run pytest` in `backend/` -> `136 passed`.
- `corepack pnpm --filter frontend test` -> `37 files / 105 tests passed`.
- `corepack pnpm --filter frontend lint` -> PASS.
- `corepack pnpm --filter frontend build` -> PASS.
- `corepack pnpm --filter frontend exec playwright test --project=chromium --project=iphone-13 --project=pixel-7` -> `4 passed, 5 skipped`.
- `docker compose -f compose/docker-compose.yml --profile core up -d --build backend` -> PASS; required because compose backend does not mount local backend source.

## Defects found and fixed
- `news_refresh` could fail before fallback on malformed live RSS XML.
  - Symptom: demo-chain failed at `refresh-news-daily` with `xml.etree.ElementTree.ParseError`.
  - Fix: catch `ElementTree.ParseError` in `NewsService._refresh_provider` so `auto` can continue to cache/last_good/manual_snapshot.
  - Regression: `test_refresh_provider_falls_back_when_live_rss_is_malformed`.
- Unsupported chat questions could inherit prior session memory and return unrelated oil/fuel citations.
  - Symptom: UI question `Что с рынком кофе?` returned a verified retrieval answer with petroleum citations.
  - Fix: `ChatRetrievalService.retrieve` now blocks out-of-domain current questions before applying running summary, previous user messages, or previous citation refs.
  - Regression: `test_retrieval_blocks_out_of_domain_question_before_session_memory`.

## Browser-use smoke summary
- Analyst login: `analyst@fuelsight.local / analyst12345` -> `/dashboard`, no console errors.
- Analyst `/import` -> access denied / no operational import UI.
- Admin login: `admin@fuelsight.local / admin12345` -> `/import`, sees `Начальная история`, `Диагностика`, history table with `Качество` and `Статус`.
- MVP routes checked: `/dashboard`, `/analytics/sales`, `/analytics/margin`, `/forecast`, `/news`.
- Sales URL sync checked by changing `/analytics/sales` from `AI_95/day` to `DT_W/week`; URL, controls, and chart canvas updated.
- Forecast scenario checked with `retail_price_delta_pct=2.5`; URL params, base/scenario values, MAE/RMSE/SMAPE, and single price-delta what-if control present.
- News/chat checked:
  - supported margin question returns confidence, verification, and citations;
  - unsupported coffee question now returns blocked uncertainty with no sources for the last answer;
  - with `Новости` toggle off and `Прогноз` on, answer includes forecast citation and no `news_raw` citation in the last answer.

## Artifacts
- Browser-use DOM snapshots: `frontend/output/browser-use-qa/*.snapshot.txt`.
- Mobile Playwright screenshots:
  - `frontend/output/playwright/iphone-13-mobile-login.png`
  - `frontend/output/playwright/iphone-13-mobile-dashboard.png`
  - `frontend/output/playwright/iphone-13-mobile-forecast.png`
  - `frontend/output/playwright/iphone-13-mobile-news.png`
  - `frontend/output/playwright/pixel-7-mobile-login.png`
  - `frontend/output/playwright/pixel-7-mobile-dashboard.png`
  - `frontend/output/playwright/pixel-7-mobile-forecast.png`
  - `frontend/output/playwright/pixel-7-mobile-news.png`
- Note: browser-use screenshot capture timed out through CDP in this session, so desktop evidence is DOM/log based; mobile visual evidence comes from Playwright screenshots.

## Residual risks
- `train_models_weekly` and external context are PASS but degraded because `fallback_ratio=0.6667`; this is acceptable for offline-safe smoke but should be explained in defense mode.
- Forecast-scope chat can include `news_digest` citations when `Новости` is off; it does not include `news_raw`, but scope semantics should be clarified if the UI intends to remove all news-derived context.
- Supported margin chat answer is cited and verified, but its first sentence can still prioritize a live news item over internal margin evidence; answer synthesis ranking may need product-facing polish.
- Worktree remains broad and dirty with Phase H changes plus generated artifacts; classify unrelated/generated files before any final commit.
