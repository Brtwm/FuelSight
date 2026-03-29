# Progress

## What Works
- Репозиторий больше не docs-only: создан и проверен запускаемый skeleton.
- Frontend skeleton собирается (`pnpm build`) и имеет базовые маршруты + защищённый shell.
- Frontend lint проходит (`pnpm lint`).
- Frontend тестовый контур подключён (`pnpm test` проходит).
- Backend skeleton запускается и отдает `GET /api/v1/health` в envelope-формате.
- Backend тесты проходят (`uv run pytest`: health contract).
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
  - `backend/tests/test_health.py`
  - `backend/pyproject.toml`, `backend/uv.lock`
  - `backend/alembic/*` scaffold
  - `backend/Dockerfile`
- Compose and scripts:
  - `compose/docker-compose.yml`
  - `compose/env/*.env`
  - `scripts/start-demo.*`, `scripts/stop-demo.*`

## Remaining Work
- Фаза 1: модели SQLAlchemy + Alembic migration chain для core tables.
- Seed roles/users/products (`AI_92`, `AI_95`, `DT`).
- Auth endpoints и role dependencies.
- Вертикальный slice импорта и демо-данных.

## Known Issues
- Frontend bundle warning о размере чанка (ожидаемо для skeleton + heavy deps, non-blocking).
- Airflow-профиль тяжёлый по pull/first startup на слабом канале.
- Первый старт compose может быть долгим из-за сборки образов и загрузки `apache/airflow`.

## Maintenance Rule
- После каждой фазы обновлять как минимум:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При изменении архитектурных правил обновлять также:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
