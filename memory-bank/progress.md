# Progress

## What Works
- Репозиторий больше не docs-only: создан и проверен запускаемый skeleton.
- Frontend собирается (`pnpm build`) и имеет рабочий auth-flow с защищённым shell.
- Frontend lint проходит (`pnpm lint`).
- Frontend тестовый контур расширен (`pnpm test`: 12 passed).
- Backend core расширен до Фазы 1:
  - единый envelope/error contract для `404/422/500`;
  - SQLAlchemy models для `roles`, `users`, `products`, `sales_daily`, `purchases_daily`, `import_jobs`;
  - Alembic migration `20260329_0001` (core schema v1);
  - seed entrypoint `uv run fuelsight-seed-core`.
- Фаза 2 auth реализована:
  - `POST /api/v1/auth/login`;
  - `POST /api/v1/auth/refresh`;
  - `GET /api/v1/auth/me`;
  - `POST /api/v1/auth/logout`;
  - `get_current_user` и `require_roles` зависимости.
- Фаза 3 import реализована:
  - `POST /api/v1/import/sales`;
  - `POST /api/v1/import/purchases`;
  - `POST /api/v1/import/generate-demo`;
  - `GET /api/v1/import/jobs`;
  - `GET /api/v1/import/jobs/{job_id}`;
  - CSV/XLSX parsing, row-level validation, partial success, error report path в `import_jobs`;
  - продвинутый генератор исторических данных (AR(1) спрос, OU цены, праздники РФ, тренды, 4 продукта, период 3 года по умолчанию);
- Backend тесты проходят (`uv run pytest`: 29 passed, включая 10 статистических тестов).
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
  - `frontend/src/pages/*` (включая рабочий `ImportPage`)
  - `frontend/src/features/auth/*` API-auth provider + role/access guards + refresh retry utilities
  - `frontend/src/features/import/*` import forms, jobs table, schema, cache invalidation
  - `frontend/src/lib/api/client.ts` (health check)
  - `frontend/src/lib/api/auth.ts` (auth API client)
  - `frontend/src/lib/api/import.ts` (import API client)
  - `frontend/src/lib/config/env.ts`
  - `frontend/Dockerfile`
- Backend:
  - `backend/app/main.py`, `app/core/*`, `app/api/v1/*`
  - `backend/app/api/v1/imports.py`
  - `backend/app/models/*` (core v1)
  - `backend/app/services/import_service.py`
  - `backend/app/services/data_generator.py`
  - `backend/app/services/data_generator_config.py`
  - `backend/app/schemas/imports.py`
  - `backend/app/scripts/seed_core.py`
  - `backend/alembic/versions/20260329_0001_phase1_core_schema.py`
  - `backend/tests/test_health.py`
  - `backend/tests/test_error_envelope.py`
  - `backend/tests/test_auth_api.py`
  - `backend/tests/test_import_api.py`
  - `backend/tests/test_import_schemas.py`
  - `backend/tests/test_data_generator.py`
  - `backend/tests/test_security_tokens.py`
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
- KPI dashboard и производные витрины.
- Analytics, forecast/backtests, airflow operationalization, bonus news/chat.

## Known Issues
- Frontend bundle warning о размере чанка (ожидаемо для skeleton + heavy deps, non-blocking).
- Airflow-профиль тяжёлый по pull/first startup на слабом канале.
- Первый старт compose может быть долгим из-за сборки образов и загрузки `apache/airflow`.
- Для JWT в dev используется короткий секрет `change-me`; в production-like запуске нужен безопасный ключ.

## Maintenance Rule
- После каждой фазы обновлять как минимум:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При изменении архитектурных правил обновлять также:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
