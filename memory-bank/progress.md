# Progress

## What Works
- Фазы 0-8 реализованы end-to-end.
- Core product flow стабилен: `login -> import/demo-data -> dashboard -> sales -> margin -> forecast`.
- Bonus contour Phase 8 (`news + chat`) реализован и изолирован от core MVP:
  - backend домены `news` и `chat` под `/api/v1`;
  - таблицы и миграция `news_raw`, `news_digests`, `chat_sessions`, `chat_messages`;
  - UI `/news`: digest, поиск, чат с citations, режим `LLM off`;
  - role boundaries сохранены (`admin` refresh, `admin/analyst` read + chat).
- Airflow operationalization (Phase 7) остаётся рабочим:
  - custom Airflow image с backend runtime;
  - DAG runtime через `fuelsight-pipeline` task-layer;
  - 5 стандартизированных DAG ID загружаются в Airflow;
  - separate Airflow metadata DB (`airflow`);
  - shared volumes/inbox wiring для pipeline операций.
- Full demo-run automation добавлена (`scripts/run_full_demo.py`) с machine-readable отчётом.
- Structured logging добавлен для API/pipeline.

## Completed Artifacts (Phase 8)
- Backend:
  - `backend/alembic/versions/20260405_0004_phase8_news_chat.py`
  - `backend/app/api/v1/news.py`
  - `backend/app/api/v1/chat.py`
  - `backend/app/services/news_service.py`
  - `backend/app/services/chat_service.py`
  - `backend/app/models/news_raw.py`
  - `backend/app/models/news_digest.py`
  - `backend/app/models/chat_session.py`
  - `backend/app/models/chat_message.py`
- Frontend:
  - `frontend/src/pages/NewsPage.tsx`
  - `frontend/src/features/news/components/NewsDigestPanel.tsx`
  - `frontend/src/features/news/components/NewsSearchDrawer.tsx`
  - `frontend/src/features/news/components/ChatThread.tsx`
  - `frontend/src/features/news/components/CitationList.tsx`
  - `frontend/src/lib/api/news.ts`
  - `frontend/src/lib/api/chat.ts`
- Tests:
  - `backend/tests/test_news_api.py`
  - `backend/tests/test_chat_api.py`
  - `backend/tests/test_phase8_flow_api.py`
  - `frontend/src/features/news/components/*.test.tsx`
  - `frontend/src/lib/api/news.test.ts`
  - `frontend/src/lib/api/chat.test.ts`

## Validation Snapshot
- Backend tests: `uv run pytest` -> `74 passed`.
- Frontend tests: `corepack pnpm --filter frontend test -- --run` -> `40 passed`.
- Frontend build: `corepack pnpm --filter frontend build` -> success.
- Backend lint: `uv run ruff check .` -> success.

## Remaining Work
- Phase 9: hardening, e2e critical path polish, documentation polish.

## Known Issues
- Frontend bundle size warning остаётся.
- Dev JWT secret в local окружении демонстрационный (`change-me`).

## Maintenance Rule
- После каждой следующей фазы обновлять:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При архитектурных изменениях поддерживать синхронизацию:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
