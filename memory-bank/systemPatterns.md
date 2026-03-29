# System Patterns

## Architecture Shape
- Архитектура разбита на четыре крупных слоя:
  - frontend SPA;
  - backend REST API;
  - PostgreSQL как основное хранилище;
  - ML/pipeline контур с Airflow и файловыми артефактами.

## Key Design Decisions
- Frontend и backend разделены.
- Все серверные маршруты идут под `/api/v1`.
- Базовый backend-контракт уже зафиксирован на уровне skeleton: envelope `{ data, error, meta }` и `request_id` middleware.
- Используется role-based access с двумя ролями.
- `v1` сознательно исключает multi-station модель.
- Новостной и чат-контур проектируется как расширение, но с теми же доменными терминами и API-правилами.

## Domain Breakdown
- `auth`
- `imports`
- `kpi`
- `analytics`
- `forecasts`
- `backtests`
- `news`
- `chat`

## Data Patterns
- Основная зернистость фактов: `day x product`.
- KPI и аналитика строятся поверх `sales_daily` и `purchases_daily`.
- Прогноз опирается на лаги, календарные и ценовые признаки.
- What-if ограничен ценовым сценарием, а не произвольным sandbox-моделированием.

## UX Patterns
- Единый app shell после логина.
- Общие фильтры по продукту и периоду.
- У каждой data-heavy страницы должны быть `loading`, `empty`, `error`, `ready` состояния.
- ASCII-экраны считаются обязательной частью источника правды для UI.

## Documentation Patterns
- Источник правды разбит по слоям: идея, GTM, техдоки, фичи, экраны, AGENTS.
- Feature docs описывают user flow, состояния UI, API-контракты, frontend/backend требования и edge cases.
- Memory Bank не заменяет основную документацию, а даёт короткий оперативный контекст поверх неё.
