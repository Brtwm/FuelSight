# Active Context

## Current State
- Фаза 0 реализована: репозиторий перешёл из docs-only в запускаемый skeleton.
- Добавлены рабочие каталоги `frontend/`, `backend/`, `compose/`, `scripts/`.
- Повторно проверен запуск core-стека (`db + backend + frontend`) и airflow-профиля через Docker Compose, затем выполнен clean shutdown.

## Recently Completed
- Инициализирован git-репозиторий и базовая repo hygiene: `.gitignore`, `.editorconfig`, `.env.example`.
- Добавлен root `README.md` с режимами запуска `hybrid` и `full docker`.
- Frontend bootstrap:
  - `Vite + React + TypeScript`;
  - skeleton-маршруты `/login`, `/import`, `/dashboard`, `/analytics/sales`, `/analytics/margin`, `/forecast`, `/news`;
  - `AppShell`, mock `AuthProvider`, `ProtectedRoute`;
  - health-check API client к `/api/v1/health`.
- Backend bootstrap:
  - FastAPI app skeleton с `request_id` middleware;
  - единый envelope `{ data, error, meta }`;
  - endpoint `GET /api/v1/health`;
  - базовые exception handlers;
  - `pytest` smoke test.
- Alembic scaffolding добавлен без доменных миграций.
- Compose:
  - профиль `core`: `db`, `backend`, `frontend`;
  - профиль `airflow`: `airflow-init`, `airflow-webserver`, `airflow-scheduler`;
  - volumes `postgres_data`, `model_artifacts`, `news_index`, `airflow_logs`.
- Исправлен `frontend` healthcheck в compose: проверка через `node fetch(...)` вместо `wget` для совместимости контейнера.
- Подтверждены quality checks по frontend: `lint`, `test`, `build`.
- Добавлены helper scripts:
  - `scripts/start-demo.ps1`, `scripts/stop-demo.ps1`
  - `scripts/start-demo.sh`, `scripts/stop-demo.sh`

## Current Focus
- Переход к Фазе 1: backend core и схема данных v1 (`roles`, `users`, `products`, `sales_daily`, `purchases_daily`, `import_jobs`).

## Active Decisions
- `ENABLE_LLM=false` по умолчанию.
- MVP остаётся single-station (`v1` без `stations`).
- Airflow и bonus contour изолированы профилями/этапами и не блокируют core-flow.

## Risks To Remember
- В Фазе 1 важно не смешивать bootstrap и бизнес-логику в одном слое.
- При добавлении auth/import не нарушить envelope-контракт и role boundaries.
- Следить за синхронизацией docs_fuelsight и реализации после каждой большой фазы.
