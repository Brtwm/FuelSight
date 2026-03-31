# Progress

## What Works
- Репозиторий больше не docs-only: создан и проверен запускаемый skeleton.
- Frontend skeleton собирается (`pnpm build`) и имеет базовые маршруты + защищённый shell.
- Frontend lint проходит (`pnpm lint`).
- Frontend тестовый контур подключён (`pnpm test` проходит).
- Backend core расширен до Фазы 1:
  - единый envelope/error contract для `404/422/500`;
  - SQLAlchemy models для `roles`, `users`, `products`, `sales_daily`, `purchases_daily`, `import_jobs`;
  - Alembic migration `20260329_0001` (core schema v1);
  - seed entrypoint `uv run fuelsight-seed-core`.
- Backend тесты проходят (`uv run pytest`: 4 passed).
- Backend lint проходит (`uv run ruff check .`).
- Compose-конфигурация валидна для `core` и `airflow` профилей.
- Реальный запуск подтверждён:
  - `docker compose --profile core up -d db backend frontend`
  - `docker compose --profile airflow up -d airflow-init airflow-webserver airflow-scheduler`
  - последующий `docker compose ... down` выполняется корректно.

## Completed Artifacts
- Root:
  - `README.md`
  - `.env.example`
  - `.gitignore`
  - `.editorconfig`
  - `.node-version`
  - `.python-version`
  - `pnpm-workspace.yaml`
  - `package.json`
- Frontend:
  - `frontend/src/app/*` providers/router/layout
  - `frontend/src/pages/*` skeleton pages
  - `frontend/src/features/auth/*` mock auth + route guard
  - `frontend/src/lib/api/client.ts` (health check)
  - `frontend/src/lib/config/env.ts`
  - `frontend/Dockerfile`
- Backend:
  - `backend/app/main.py`, `app/core/*`, `app/api/v1/*`
  - `backend/app/models/*` (core v1)
  - `backend/app/scripts/seed_core.py`
  - `backend/alembic/versions/20260329_0001_phase1_core_schema.py`
  - `backend/tests/test_health.py`
  - `backend/tests/test_error_envelope.py`
  - `backend/pyproject.toml`, `backend/uv.lock`
  - `backend/alembic/*` scaffold + metadata wiring
  - `backend/Dockerfile`
- Docs sync:
  - `docs_fuelsight/project/backend/backend-docs.md`
  - `docs_fuelsight/project/backend/api-endpoints.md`
- Compose and scripts:
  - `compose/docker-compose.yml`
  - `compose/env/*.env`
  - `scripts/start-demo.*`, `scripts/stop-demo.*`

## Remaining Work
- Auth endpoints и role dependencies.
- Вертикальный slice импорта и демо-данных.
- Runtime-подтверждение миграций/seed на живом PostgreSQL (`uv run alembic upgrade head`, `uv run fuelsight-seed-core`).

## Known Issues
- Frontend bundle warning о размере чанка (ожидаемо для skeleton + heavy deps, non-blocking).
- Airflow-профиль тяжёлый по pull/first startup на слабом канале.
- Первый старт compose может быть долгим из-за сборки образов и загрузки `apache/airflow`.
- В текущей сессии отсутствует доступный локальный PostgreSQL (`localhost:5432`), поэтому online migration/seed не выполнены; offline Alembic SQL генерация проходит.

## Maintenance Rule
- После каждой фазы обновлять как минимум:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При изменении архитектурных правил обновлять также:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
