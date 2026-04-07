# Active Context

## Current State
- Фаза 8 реализована: bonus contour `news + chat` доступен на `/news`.
- Фаза 9 завершена: hardening + test expansion + docs sync.
- Core MVP API-контракты сохранены: `/api/v1/*` и envelope `{ data, error, meta }`.
- Airflow остаётся в режиме task-layer через backend (без HTTP-обхода), DAG-и paused-by-default.

## Recently Completed
- Backend hardening:
  - runtime guard для `JWT_SECRET_KEY` (>=32 символов вне `local/test`);
  - env/examples обновлены на безопасный placeholder.
- Phase 9 backend tests:
  - `test_config_security.py` (env-aware JWT guard);
  - `test_phase9_core_flow_api.py` (core API smoke flow);
  - `test_phase9_llm_off_smoke_api.py` (`digest/search` + `chat 503 llm_disabled`).
- Frontend hardening:
  - route-level lazy loading в `AppRouter`;
  - Vite manual chunk split для снижения bundle warning.
- Добавлен browser E2E контур:
  - `frontend/playwright.config.ts`;
  - `frontend/e2e/happy-path.spec.ts`;
  - команда `pnpm test:e2e`.
- `scripts/run_full_demo.py` расширен:
  - `core_api_flow_smoke`;
  - `llm_off_smoke`;
  - опциональный `--with-e2e` шаг в общем machine-readable отчёте;
  - Windows-safe e2e command fallback (`corepack` -> `pnpm`) в demo-run.

## Active Decisions
- LLM/news/chat остаётся bonus contour и не блокирует core MVP.
- При `LLM off` digest/search остаются доступными; chat generation возвращает `503`.
- Источники в чате обязательны: ответы без citations считаются невалидными.
- Источник новостей в базовом варианте: `GDELT` (fixture-driven для локального MVP).

## Risks To Remember
- Airflow image сборка остаётся тяжёлой по времени на свежей машине.
- Playwright E2E требует установленный Chromium (`playwright install chromium`) в средах без предустановленного браузера.
