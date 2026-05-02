# Active Context

## Current Focus
- На 2026-04-29 реализуется `Phase I. Cloud LLM Primary + Provider-Neutral Fallback`.
- На 2026-04-27 реализуется `Phase H. Advanced RAG Quality Layer` в статусе `implemented + worktree`.
- На 2026-04-27 реализован `Phase G. RAG-First Chat Core` в статусе `implemented + worktree`.
- На 2026-04-22 закрыт `Phase F. Real News Ingestion Baseline` в статусе `implemented + worktree`.
- `Phase D` подтверждён как `implemented`: `external_indicators_daily`, `event_catalog`, manifest-first quality/fallback semantics и offline-safe ladder работают в коде и тестах.
- `Phase E` подтверждён как `implemented + worktree`: `/forecast` уже содержит `base vs scenario`, `model_freshness`, `retrain_status`, provider/freshness context и тестовый coverage.
- News contour переведён с fixture ingest на real-provider baseline с `RSS/APIs only`, local cache и `manual_snapshot` fallback.
- Chat переведён с `template_rag + 503 on LLM off` на retrieval-first baseline: `ENABLE_LLM=false` возвращает cited `retrieval_only` answer при наличии evidence.

## Worktree Snapshot
- `backend/app/integrations/llm/{contracts.py,adapters.py,registry.py}`
  - добавлен provider-neutral LLM слой для `chat`, `embed_texts`, `rerank`, `health`;
  - добавлен OpenAI-compatible adapter для NeuralDeep/cloud profile;
  - GigaChat реализован как optional native adapter с OAuth token cache, chat completions и embeddings;
  - local adapter остаётся fallback для deterministic embeddings/rerank, без обязательной local chat generation.
- `backend/app/services/chat_service.py`, `backend/app/services/chat_retrieval.py`, `backend/app/services/rag_index_service.py`
  - chat вызывает cloud/local adapter только после evidence pack;
  - cloud получает только sanitized snippets/citations, не raw fact tables;
  - adapter failures и hard-block verification деградируют до cited `retrieval_only`;
  - repairable `unsupported_claim_terms` проходят deterministic repair/fallback с `repaired|fallback_verified`.
- `frontend/src/features/news/components/ChatThread.tsx`, `frontend/src/lib/api/chat.ts`
  - UI показывает provider/model/degradation из `meta.llm_provider`;
  - verification labels переведены на русские статусы: `Ответ проверен`, `Ответ исправлен`, `Ответ построен по источникам`, `Недостаточно данных`.
- `backend/app/models/rag_chunk.py`, `backend/alembic/versions/20260427_0008_phase_h_rag_quality.py`
  - добавлен pgvector-backed `rag_chunks` baseline, `chat_sessions.running_summary` и `chat_messages.metadata_json`.
- `backend/app/services/chat_retrieval.py`
  - query normalization, RU product aliases, date hints, deterministic local embeddings, hybrid scoring, source diversity, confidence and verification helpers.
- `backend/app/services/chat_service.py`
  - unsupported questions now return blocked uncertainty response instead of 422 with unanswered user turn;
  - successful verified answers update short running summary.
- `frontend/src/features/news/components/ChatThread.tsx`
  - confidence/verification chips and compact `news_raw`/`forecast` retrieval scope toggles.
- `compose/docker-compose.yml`
  - Postgres image switched to `pgvector/pgvector:pg16`.
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
- `backend/app/services/chat_retrieval.py`, `backend/app/services/chat_service.py`, `backend/app/api/v1/chat.py`
  - session-aware evidence pack по `news_raw`, `news_digests`, `kpi`, `analytics`, `forecast`;
  - unified citations with `provider_mode`, `confidence`, `source_type`;
  - mode resolver деградирует `cloud_first/local_only/LLM off` в `retrieval_only` без cloud вызовов.
- `backend/airflow/dags/refresh_news_daily.py`
  - добавлен Airflow orchestration gap-fix для Phase F news refresh.
- `frontend/src/features/news/components/{ChatThread.tsx,CitationList.tsx}`, `frontend/src/pages/NewsPage.tsx`
  - chat input доступен в retrieval-only/offline-safe;
  - citations показывают source mode и confidence.

## What Was Verified Today
- Backend:
  - `uv run pytest tests/test_chat_api.py tests/test_chat_service.py tests/test_news_api.py tests/test_news_service.py tests/test_news_integrations.py tests/test_pipeline_tasks.py tests/test_phase9_llm_off_smoke_api.py` -> `26 passed`.
  - `uv run pytest` -> `120 passed`.
  - targeted suites for news/pipeline/chat/forecast pass with new real-news ingest baseline.
- Frontend:
  - `corepack pnpm --filter frontend test -- src/features/news/components/ChatThread.test.tsx src/lib/api/chat.test.ts` -> `37 files / 103 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.
  - `corepack pnpm --filter frontend test -- src/features/news/components/NewsDigestPanel.test.tsx src/features/news/components/NewsSearchDrawer.test.tsx src/features/news/components/ChatThread.test.tsx src/pages/NewsPage.tsx src/pages/ForecastPage.states.test.tsx` -> `37 files / 102 tests passed`.
  - `corepack pnpm --filter frontend build` -> `PASS`.

## Next Likely Steps
- Следующий крупный срез после стабилизации Phase I: `Phase J. Defense Mode + Executive Outputs`.
- Для cloud-enhanced path принят provider-neutral подход: первым demo provider остаётся `NeuralDeep` через OpenAI-compatible adapter, `GigaChat` доступен как alternative optional cloud adapter при наличии `GIGACHAT_AUTH_KEY`.

## Active Decisions
- Breaking redesign ограничен `KPI + Analytics`; `forecast/news` остаются на current generic meta shape.
- Analyst-first UX сохраняется: что случилось / почему важно / можно ли доверять данным.
- Core flow (`import`, `kpi`, `analytics`, `forecast`) остаётся независимым от LLM.
- Для `Phase F` принят source policy: `RSS/APIs only`, без HTML scraping.
- Для news schema принят additive путь: новые normalized поля добавлены в `news_raw`, legacy `source_name/impact_hint` пока сохранены для совместимости.
- LLM не является источником фактов: chat должен строить answer только по retrieved evidence pack с citations.
- В cloud provider нельзя отправлять raw fact tables/import files/user data; только агрегированные snippets/evidence.
- Phase G сознательно не реализует реальные NeuralDeep/GigaChat calls; cloud/local adapter implementation остаётся Phase I.
- Phase I реализует NeuralDeep/OpenAI-compatible как cloud-enhanced profile, а не фундамент продукта.
- GigaChat для Phase I поддерживает auth/token lifecycle, chat и embeddings; reranker остаётся controlled unavailable.

## Risks To Remember
- `pgvector` теперь runtime dependency для compose DB; fresh local stack должен использовать `pgvector/pgvector:pg16`.
- `frontend/output/playwright/*` screenshots обновляются при mobile smoke и могут шуметь в git diff.
- Для demo-машин нужен установленный Playwright WebKit (`iphone-13` project).
- Phase G retrieval сейчас lexical/rule-based; dense retrieval, reranker и финальный verification pass остаются Phase H/I.
