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
- Auth: `JWT access + refresh`, роли `admin` и `analyst`
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
- `analyst`:
  - доступ к KPI, аналитике, прогнозу;
  - просмотр latest backtest;
  - доступ к сводке и чату;
  - без доступа к импортам и системным настройкам.

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
```

Security hardening rule:
- если `APP_ENV` не `local`/`test`, backend требует `JWT_SECRET_KEY` длиной минимум 32 символа и завершает старт с ошибкой при нарушении.

## Тестирование backend
- API tests: авторизация, role guards, envelope responses, типовые happy-path и validation errors.
- Repository/service tests: импорт, расчёт KPI, агрегации маржи, сценарный прогноз.
- ML tests: формирование лагов, baseline forecast, расчёт MAE/RMSE/SMAPE.
- Contract tests: согласованность схем между frontend и backend для ключевых эндпоинтов.
- Operational smoke (Phase 9):
  - `uv run pytest`
  - `corepack pnpm --filter frontend test`
  - `corepack pnpm --filter frontend build`
  - `corepack pnpm --filter frontend test:e2e`
  - `python scripts/run_full_demo.py --with-e2e`

## Связанные документы
- API-контракты: `@docs_fuelsight/project/backend/api-endpoints.md`
- Схема данных: `@docs_fuelsight/project/backend/database.md`
- ML и Airflow: `@docs_fuelsight/project/backend/ml-pipeline.md`
- Docker Compose и локальный запуск: `@docs_fuelsight/project/backend/deployment.md`
