# FuelSight Roadmap

This roadmap keeps future work separate from the implemented baseline in
`docs/as-built-baseline.md`. It focuses on improvements that strengthen the
diploma defense and public portfolio value without expanding FuelSight into a
multi-tenant SaaS product.

## Already Implemented

- Local role-based web app with `admin`, `sales`, `accounting`, `analyst`, and `director` paths.
- CSV/XLSX import, demo data generation, KPI dashboard, sales analytics, margin analytics, forecast, news digest, and cited chat.
- CatBoost-first forecasting with Seasonal Naive baseline and quality metrics.
- External indicators, news ingestion, RAG index, optional provider-neutral LLM adapters, and retrieval-only fallback.
- Airflow DAGs and `scripts/run_full_demo.py` for offline-safe and cloud-enhanced demo profiles.
- Backend, frontend, dependency audit, Docker, full-demo, and Playwright validation commands.

## Near-Term Public Polish

- Add desktop screenshots for the README portfolio section; mobile Playwright screenshots are already committed.
- Add a localhost-only Docker Compose override for safer public demo instructions.
- Add CI for backend lint/tests and frontend test/build.
- Keep demo report wording focused on expected offline-safe fallback instead of exposing low-level degraded implementation details.

## Product Improvements

- Add a backend-backed browser smoke test in addition to mocked frontend Playwright flows.
- Improve the one-page legacy demo report artifact with clearer executive wording and selected screenshots.
- Expand forecast model validation notes with MAE, RMSE, SMAPE, and baseline comparison examples.
- Keep optional cloud mode provider-neutral and evidence-grounded; never make LLM calls required for import, KPI, analytics, or forecast.

## Scope Guardrails

- Do not add multi-tenant SaaS, billing, or public account management.
- Do not introduce `stations` without a deliberate schema, UI, and documentation update.
- Keep API responses in the `{ data, error, meta }` envelope.
- Keep user-facing UI copy in Russian; keep API paths, filenames, and identifiers in English.
- Chat answers must be based on backend evidence and citations, not autonomous web browsing.
