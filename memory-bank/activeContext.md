# Active Context

## Current State
- Фаза 1 реализована: backend-фундамент расширен до core schema v1.
- Добавлены SQLAlchemy-модели и Alembic migration для `roles`, `users`, `products`, `sales_daily`, `purchases_daily`, `import_jobs`.
- Добавлен отдельный идемпотентный seed-entrypoint `uv run fuelsight-seed-core`.

## Recently Completed
- Усилен backend core:
  - типизированный `config.py`;
  - `get_db_session` в `database.py`;
  - единый error envelope для `HTTPException`, `RequestValidationError`, `Exception`.
- Добавлены модели домена `core v1` и связи между ними.
- В Alembic:
  - `target_metadata` подключен к `Base.metadata`;
  - создана первая migration `20260329_0001_phase1_core_schema.py`;
  - offline SQL-проверки `upgrade`/`downgrade` проходят.
- Добавлен seed-скрипт:
  - роли `admin`, `analyst`;
  - пользователи `admin@fuelsight.local`, `analyst@fuelsight.local`;
  - продукты `AI_92`, `AI_95`, `DT`.
- Обновлены backend docs:
  - `docs_fuelsight/project/backend/backend-docs.md` (seed command);
  - `docs_fuelsight/project/backend/api-endpoints.md` (error.code mapping).
- Тесты:
  - `uv run pytest` — 4 passed;
  - `uv run ruff check .` — clean.

## Current Focus
- Переход к Фазе 2: auth endpoints (`/api/v1/auth/*`) и защищённый shell-контур frontend.

## Active Decisions
- `ENABLE_LLM=false` по умолчанию.
- MVP остаётся single-station (`v1` без `stations`).
- Airflow и bonus contour изолированы профилями/этапами и не блокируют core-flow.
- Seed выполняется отдельной командой после миграций (`uv run fuelsight-seed-core`), не в startup и не в migration.

## Risks To Remember
- Для полного runtime-подтверждения Фазы 1 нужно повторить `uv run alembic upgrade head` на живом PostgreSQL (в текущей сессии локальный DB недоступен).
- При добавлении auth/import не нарушить envelope-контракт и role boundaries.
- Следить за синхронизацией docs_fuelsight и реализации после каждой большой фазы.
