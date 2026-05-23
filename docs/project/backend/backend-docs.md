# Backend: FuelSight

## Назначение
Backend FuelSight отвечает за аутентификацию, импорт данных, REST API для аналитики и прогноза, хранение метаданных моделей и организацию фоновых пайплайнов. Архитектура должна быть достаточно строгой для дипломного проекта, но без избыточной сложности enterprise-платформы.

## Стек
- Language: `Python 3.12`
- Framework: `FastAPI`
- Validation: `Pydantic v2`
- ORM: `SQLAlchemy 2.0`
- Migrations: `Alembic`
- Database: `PostgreSQL`
- Auth: `JWT access + refresh`, роли `admin`, `sales`, `accounting`,
  `analyst`, `director`
- Scheduler: `Airflow`
- Package Manager: `uv`
- Dev Port: `8061`

## Архитектурные ограничения
- База `v1` не содержит сущность `stations`; система проектируется под одну точку продаж.
- Все API-эндпоинты располагаются под префиксом `/api/v1`.
- Бонусный NLP/LLM-контур обязан быть отключаемым через конфигурацию без поломки основного продукта.
- Демо-данные являются частью поддерживаемого сценария, а не временной заглушкой.

## Предлагаемая структура проекта
```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── imports.py
│   │       ├── kpi.py
│   │       ├── analytics.py
│   │       ├── forecasts.py
│   │       ├── backtests.py
│   │       ├── news.py
│   │       └── chat.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── dependencies/
├── ml/
│   ├── datasets/
│   ├── features/
│   ├── models/
│   ├── backtesting/
│   └── inference/
├── airflow/
│   ├── dags/
│   └── plugins/
├── scripts/
├── tests/
└── alembic/
```

## Серверные домены
- `auth`: логин, refresh, профиль пользователя, logout.
- `imports`: загрузка продаж и закупок, история импортов, генерация демо-данных.
- `kpi`: агрегированные показатели главной панели и список алертов.
- `analytics`: временные ряды продаж, цены, маржа, аномалии.
- `forecasts`: on-demand прогноз и what-if сценарии.
- `backtests`: метрики качества и запуск переобучения/валидации.
- `news`: новостные выгрузки, digest, поиск по материалам.
- `chat`: RAG-диалог с обязательными citations.

## Правила API
- Единый envelope ответа:
```json
{
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid"
  }
}
```
- Ошибки уровня приложения возвращаются в `error.code`, `error.message`, `error.details`.
- `422` используется для ошибок схемы и валидации.
- `403` возвращается при нарушении ролей.
- Для аналитических запросов по умолчанию применяются разумные интервалы, если клиент не передал период.

## Авторизация и роли
- `admin`:
  - загрузка CSV/XLSX;
  - генерация демо-данных;
  - ручной запуск backtest/retraining;
  - запуск обновления новостей;
  - управление пользователями и справочником продуктов в будущем.
- `sales`:
  - импорт продаж;
  - чтение KPI, аналитики продаж, прогноза и latest backtest.
- `accounting`:
  - импорт закупок;
  - чтение KPI, истории закупочных импортов и аналитики маржи.
- `analyst`:
  - доступ к KPI, аналитике продаж/маржи, прогнозу;
  - просмотр latest backtest;
  - доступ к новостной сводке, поиску, RAG-чату и управленческому отчету;
  - без доступа к импортам и системным настройкам.
- `director`:
  - доступ к executive dashboard, KPI, маржинальным рискам, прогнозу,
    новостному контексту и управленческому отчету;
  - без доступа к импортам, refresh/retraining и backend RAG chat actions.

## Фоновые задачи и пайплайны
- Импорт файлов ведётся через `import_jobs`.
- Ежедневные и еженедельные процессы описываются DAG-ами Airflow.
- Модели и артефакты хранятся в файловой системе контейнера, а метаданные — в PostgreSQL.
- Индекс новостей и RAG-артефакты допускается хранить на локальном volume.

## Команды backend
- `uv sync`
- `uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload`
- `uv run alembic upgrade head`
- `uv run fuelsight-seed-core`
- `uv run pytest`
- `uv run ruff check .`

Для локального запуска вне Docker Compose база должна поддерживать расширение `pgvector`:
миграция RAG-индекса создаёт `rag_chunks.embedding vector(64)`. Compose уже использует
`pgvector/pgvector:pg16`, поэтому отдельная установка нужна только для вручную поднятого
PostgreSQL.

## Environment Variables
```env
APP_ENV=local
APP_PORT=8061
DATABASE_URL=postgresql+psycopg://fuelsight:fuelsight@db:5432/fuelsight
JWT_SECRET_KEY=change-me-at-least-32-characters-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_MIN=30
JWT_REFRESH_TTL_DAYS=7
AUTH_REFRESH_COOKIE_NAME=fuelsight_refresh_token
AUTH_REFRESH_COOKIE_PATH=/api/v1/auth
ENABLE_LLM=false
NEWS_PROVIDER=gdelt
MODEL_ARTIFACTS_DIR=/opt/fuelsight/artifacts/models
NEWS_INDEX_DIR=/opt/fuelsight/artifacts/news
IMPORT_MAX_UPLOAD_BYTES=10485760
IMPORT_MAX_ROWS=50000
FUELSIGHT_SEED_DEMO_USERS=true
```

News runtime сейчас использует real-provider baseline (`GDELT` + curated RSS/API providers) через cache/manual snapshot fallback. При `ENABLE_LLM=false` digest/search остаются доступны, а chat возвращает `200` с `mode=retrieval_only` и citations при наличии evidence либо честный blocked uncertainty без выдуманных фактов.

Import guardrails:
- `IMPORT_MAX_UPLOAD_BYTES` ограничивает размер CSV/XLSX upload; при превышении API
  возвращает envelope с HTTP `413`.
- `IMPORT_MAX_ROWS` ограничивает число строк данных в одном import job; при превышении job
  завершается ошибкой с понятным сообщением.

Demo/security notes:
- `FUELSIGHT_SEED_DEMO_USERS=true` оставляет локальные демо-учётки
  `admin@fuelsight.local`, `sales@fuelsight.local`, `accounting@fuelsight.local`,
  `analyst@fuelsight.local` и `director@fuelsight.local`.
- Для показа в сети или передачи окружения выставить `FUELSIGHT_SEED_DEMO_USERS=false`,
  удалить или ротировать локальный `.env` и пересоздать пользователей вручную.

Security hardening rule:
- если `APP_ENV` не `local`/`test`, backend требует `JWT_SECRET_KEY` длиной минимум 32 символа и завершает старт с ошибкой при нарушении.

## Тестирование backend
- API tests: авторизация, role guards, envelope responses, типовые happy-path и validation errors.
- Repository/service tests: импорт, расчёт KPI, агрегации маржи, сценарный прогноз.
- ML tests: формирование лагов, baseline forecast, расчёт MAE/RMSE/SMAPE.
- Contract tests: согласованность схем между frontend и backend для ключевых эндпоинтов.
- Operational smoke and docs discipline:
  - `uv run pytest`
  - `corepack pnpm --filter frontend test`
  - `corepack pnpm --filter frontend build`
  - `corepack pnpm --filter frontend test:e2e:analyst`
  - `corepack pnpm --filter frontend test:e2e:admin`
  - `corepack pnpm --filter frontend test:e2e:mobile`
  - `python scripts/run_full_demo.py --with-e2e`

## Documentation Discipline
- Documentation sync rule: любое изменение code capability, API payload, demo story или поддерживаемого degraded mode должно в том же срезе обновлять `README.md` при изменении quick-start/demo flow и релевантные документы в `docs/`.
- `README.md` остаётся кратким public snapshot; подробные контракты живут в `docs/`.

## Связанные документы
- API-контракты: `@docs/project/backend/api-endpoints.md`
- Схема данных: `@docs/project/backend/database.md`
- ML и Airflow: `@docs/project/backend/ml-pipeline.md`
- Docker Compose и локальный запуск: `@docs/project/backend/deployment.md`
