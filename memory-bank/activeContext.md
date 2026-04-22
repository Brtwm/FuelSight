# Active Context

## Current Focus
- На 2026-04-22 закрыт `Phase F. Real News Ingestion Baseline` в статусе `implemented + worktree`.
- `Phase D` подтверждён как `implemented`: `external_indicators_daily`, `event_catalog`, manifest-first quality/fallback semantics и offline-safe ladder работают в коде и тестах.
- `Phase E` подтверждён как `implemented + worktree`: `/forecast` уже содержит `base vs scenario`, `model_freshness`, `retrain_status`, provider/freshness context и тестовый coverage.
- News contour переведён с fixture ingest на real-provider baseline с `RSS/APIs only`, local cache и `manual_snapshot` fallback.

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
  - `uv run pytest` -> `114 passed`.
  - targeted suites for news/pipeline/chat/forecast pass with new real-news ingest baseline.
- Frontend:
  - `corepack pnpm --filter frontend test -- src/features/news/components/NewsDigestPanel.test.tsx src/features/news/components/NewsSearchDrawer.test.tsx src/features/news/components/ChatThread.test.tsx src/pages/NewsPage.tsx src/pages/ForecastPage.states.test.tsx` -> `37 files / 102 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.

## Next Likely Steps
- Следующий крупный срез: `Phase G. RAG-First Chat Core`.
- Цель следующего шага: перевести chat c `template_rag + 503 on LLM off` на grounded retrieval-first ladder `cloud_llm -> local_llm -> retrieval_only`.

## Active Decisions
- Breaking redesign ограничен `KPI + Analytics`; `forecast/news` остаются на current generic meta shape.
- Analyst-first UX сохраняется: что случилось / почему важно / можно ли доверять данным.
- Core flow (`import`, `kpi`, `analytics`, `forecast`) остаётся независимым от LLM.
- Для `Phase F` принят source policy: `RSS/APIs only`, без HTML scraping.
- Для news schema принят additive путь: новые normalized поля добавлены в `news_raw`, legacy `source_name/impact_hint` пока сохранены для совместимости.

## Risks To Remember
- `frontend/output/playwright/*` screenshots обновляются при mobile smoke и могут шуметь в git diff.
- Для demo-машин нужен установленный Playwright WebKit (`iphone-13` project).
- Chat runtime всё ещё MVP (`template_rag`, `LLM off -> 503`) до Phase G, хотя retrieval уже читает реальные `news_raw`.
