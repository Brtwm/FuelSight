# FuelSight

FuelSight is a local-only diploma MVP for fuel sales, procurement, margin analytics, and demand forecasting.

Current status: `Phase 0` repository skeleton. The project already includes a runnable `frontend`, `backend`, `docker compose` setup, and project documentation, but business modules are still mostly stubs. It is not a SaaS product and `v1` is intentionally limited to a single point of sale.

## English Summary
- Local internal analytics system for petroleum product sales, закупки, margin analysis, and short-term demand forecast.
- Tech stack: `React + Vite + TypeScript + MUI + FastAPI + PostgreSQL + Alembic + Airflow`.
- Current repository state: runnable skeleton with verified frontend/backend checks and `GET /api/v1/health`.
- `LLM` and news/chat are optional; core MVP must work with `ENABLE_LLM=false`.
- Source of truth lives in `AGENTS.md`, `memory-bank/`, and `docs_fuelsight/`.

## О проекте
FuelSight - внутренний локальный дипломный MVP для анализа продаж, закупок, маржи и прогноза спроса на нефтепродукты. Проект задуман как production-like стенд, который заменяет связку `Excel + 1C + ручной анализ`, но при этом остается реалистичным для локального запуска и демонстрации на защите.

## Границы v1
- Одна точка продаж, без сущности `stations`.
- Основной MVP flow: `login -> import/demo-data -> dashboard -> sales analytics -> margin analytics -> forecast`.
- UI и пользовательские тексты должны быть на русском языке.
- `LLM`-контур опционален и по умолчанию выключен.
- Продукт не проектируется как multi-tenant SaaS.

## Current Status
Статус репозитория: `Phase 0`.

Что это означает сейчас:
- monorepo-структура уже собрана;
- frontend и backend поднимаются локально;
- `docker compose` поддерживает `core` и `airflow` профили;
- документация и `memory-bank` уже выступают основным источником контекста;
- бизнесовые фичи пока не реализованы end-to-end.

## Implemented Now
- `frontend/`
  - `Vite + React + TypeScript`
  - маршруты-скелеты:
    - `/login`
    - `/import`
    - `/dashboard`
    - `/analytics/sales`
    - `/analytics/margin`
    - `/forecast`
    - `/news`
  - `AppShell`, mock auth provider, route guard
  - health-check клиента к backend
- `backend/`
  - `FastAPI` skeleton
  - `GET /api/v1/health`
  - response envelope `{ data, error, meta }`
  - `request_id` middleware
  - базовые global exception handlers
  - `Alembic` scaffold без бизнес-миграций
- `compose/`
  - профиль `core`: `db`, `backend`, `frontend`
  - профиль `airflow`: `airflow-init`, `airflow-webserver`, `airflow-scheduler`
- quality checks
  - `corepack pnpm --filter frontend lint`
  - `corepack pnpm --filter frontend test`
  - `corepack pnpm --filter frontend build`
  - `uv run pytest`

## Planned Next
- `Phase 1`: core schema v1 и seed-данные
  - `roles`
  - `users`
  - `products`
  - `sales_daily`
  - `purchases_daily`
  - `import_jobs`
- auth endpoints вместо demo-auth
- import/demo-data vertical slice
- KPI и analytics поверх реальных данных
- forecast flow с quality metrics

## Repository Layout
```text
.
├── backend/        FastAPI app, Alembic, tests, ML skeleton
├── compose/        Docker Compose and env files
├── docs_fuelsight/ Product, feature, screen, and architecture docs
├── frontend/       React SPA skeleton
├── memory-bank/    Session-to-session project context
└── scripts/        Helper scripts for local demo runs
```

## Architecture Overview
- `frontend`
  - `React + Vite + TypeScript + MUI + TanStack Query + React Hook Form + Zod + ECharts`
  - primary UI shell and analytics pages
- `backend`
  - `FastAPI + Pydantic v2 + SQLAlchemy 2.0 + Alembic`
  - future domains: `auth`, `imports`, `kpi`, `analytics`, `forecasts`, `backtests`, `news`, `chat`
- `PostgreSQL`
  - основное хранилище для справочников, фактов, импортов, моделей и прогнозов
- `Airflow`
  - опциональный pipeline layer для import, feature generation, training, news refresh
- `ML`
  - primary: `CatBoost`
  - baseline: `Seasonal Naive`

## Source Of Truth
Перед изменениями в проекте сначала смотри сюда:
- [AGENTS.md](./AGENTS.md)
- [memory-bank/projectbrief.md](./memory-bank/projectbrief.md)
- [memory-bank/productContext.md](./memory-bank/productContext.md)
- [memory-bank/systemPatterns.md](./memory-bank/systemPatterns.md)
- [memory-bank/techContext.md](./memory-bank/techContext.md)
- [memory-bank/activeContext.md](./memory-bank/activeContext.md)
- [memory-bank/progress.md](./memory-bank/progress.md)
- [docs_fuelsight/project-idea.md](./docs_fuelsight/project-idea.md)
- [docs_fuelsight/project/frontend/frontend-docs.md](./docs_fuelsight/project/frontend/frontend-docs.md)
- [docs_fuelsight/project/backend/backend-docs.md](./docs_fuelsight/project/backend/backend-docs.md)

## Toolchain
- Node: `24.14.1`
- pnpm: `10.33.0`
- Python: `3.12.x`
- `uv`: lockfile already present in `backend/uv.lock`
- Docker: recommended for local DB and compose workflows

## Quick Start
### Option 1. Hybrid Mode
Подходит для повседневной разработки: приложение локально, PostgreSQL через Docker.

1. Поднять базу:
```bash
docker compose -f compose/docker-compose.yml --profile core up -d db
```

2. Запустить backend:
```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload
```

3. Запустить frontend:
```bash
corepack enable
corepack pnpm install --filter frontend
corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000
```

### Option 2. Full Docker
Подходит для smoke-демонстрации собранного skeleton.

Core stack:
```bash
docker compose -f compose/docker-compose.yml --profile core up -d
```

Airflow profile:
```bash
docker compose -f compose/docker-compose.yml --profile airflow up -d
```

## Helper Scripts
PowerShell:
- `scripts/start-demo.ps1`
- `scripts/stop-demo.ps1`

Bash:
- `scripts/start-demo.sh`
- `scripts/stop-demo.sh`

Пример:
```powershell
./scripts/start-demo.ps1
./scripts/start-demo.ps1 -WithAirflow
./scripts/stop-demo.ps1
```

## Development Commands
### Frontend
```bash
corepack pnpm --filter frontend install
corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000
corepack pnpm --filter frontend lint
corepack pnpm --filter frontend test
corepack pnpm --filter frontend build
```

### Backend
```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8061 --reload
uv run alembic upgrade head
uv run pytest
```

### Compose
```bash
docker compose -f compose/docker-compose.yml --profile core up -d
docker compose -f compose/docker-compose.yml --profile airflow up -d
docker compose -f compose/docker-compose.yml --profile core --profile airflow down
```

## Environment Files
- root example: `.env.example`
- backend example: `backend/.env.example`
- compose env:
  - `compose/env/db.env`
  - `compose/env/backend.env`
  - `compose/env/frontend.env`
  - `compose/env/airflow.env`

Ключевые переменные:
- `APP_PORT=8061`
- `DATABASE_URL=postgresql+psycopg://...`
- `VITE_API_BASE_URL=http://localhost:8061/api/v1`
- `ENABLE_LLM=false`

## Smoke And Quality Checks
Проверенные команды:

Backend health:
```bash
curl http://localhost:8061/api/v1/health
```

Ожидаемый контракт:
```json
{
  "data": {
    "ok": true
  },
  "error": null,
  "meta": {
    "request_id": "..."
  }
}
```

Frontend quality:
```bash
corepack pnpm --filter frontend lint
corepack pnpm --filter frontend test
corepack pnpm --filter frontend build
```

Backend quality:
```bash
cd backend
uv run pytest
```

Compose status:
```bash
docker compose -f compose/docker-compose.yml ps
```

## Known Limitations
- auth сейчас demo-only
  - логин работает через mock provider
  - роль выбирается на форме
  - сессия хранится локально, а не через целевой JWT + refresh flow
- большинство страниц пока являются stub-экранами
- backend пока реализует только `/api/v1/health`
- бизнесовые миграции и таблицы v1 еще не добавлены
- `LLM` и news/chat не являются обязательной частью core MVP
- часть UI-текста в текущем skeleton еще не доведена до целевого русского состояния из документации

## First Commit Checklist
Перед первым коммитом проверь:
- в индекс не попадают:
  - `.cursor/`
  - `node_modules/`
  - `dist/`
  - `.venv/`
  - `__pycache__/`
  - coverage и runtime artifacts
- в репозитории остаются:
  - `docs_fuelsight/`
  - `memory-bank/`
  - `compose/env/*.env`
  - `AGENTS.md`
  - `.env.example`
  - `backend/.env.example`

Удобные команды:
```bash
git status --short --ignored
git diff -- README.md .gitignore
```

## Roadmap
Ближайшая рабочая цель после `Phase 0`:
- перейти к `Phase 1` backend core и schema v1;
- добавить seed для `roles`, `users`, `products`;
- начать вертикальный slice `auth -> import/demo-data -> dashboard`.

Следующий cleanup, но не в этом проходе:
- локализовать оставшиеся английские пользовательские строки в frontend;
- явно пометить demo-auth в UI;
- при необходимости синхронизировать `frontend/README.md` с корневым README.

## Troubleshooting
- `pnpm: command not found`
  - Выполни `corepack enable` и используй `corepack pnpm ...`.
- Порт занят (`3000`, `5432`, `8061`, `8080`)
  - Останови конфликтующий процесс или измени mapping в `compose/docker-compose.yml`.
- Backend не стартует из-за БД
  - Проверь health `db`: `docker compose -f compose/docker-compose.yml ps`.
- Airflow поднимается долго
  - Это ожидаемо для первого запуска из-за pull образов и инициализации.

## License / Usage
На текущем этапе это учебный внутренний проект для дипломной разработки и локальной демонстрации. Если позже репозиторий будет опубликован на GitHub публично, стоит отдельно добавить выбранную лицензию и раздел contribution policy.
