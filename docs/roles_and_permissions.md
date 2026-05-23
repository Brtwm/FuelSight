# FuelSight: роли и permissions

## Назначение

Документ фиксирует фактическое поведение FuelSight после внедрения пяти-ролевой
модели. Source of truth: `backend/app/core/roles.py`, backend dependencies,
frontend `ROUTE_ACCESS`, seed data и тесты RBAC.

FuelSight использует простую role-list модель через `require_roles(...)`.
Технический slug `admin` не переименовывается в `system_admin`: в UI и
документации он описывается как `Системный администратор`, но API payloads,
seed data и проверки доступа используют `admin`.

## Роли

| Role slug | Display name | Бизнес-смысл | Основная ответственность |
| --- | --- | --- | --- |
| `admin` | Системный администратор | Техническое сопровождение | seed/demo data, диагностика, import history, полный локальный доступ |
| `sales` | Отдел продаж | Работа с реализацией | импорт продаж, аналитика продаж, прогноз спроса |
| `accounting` | Бухгалтерия | Финансовый контроль | импорт закупок, себестоимость, валовая маржа, низкомаржинальные позиции |
| `analyst` | Аналитический отдел | Комплексная аналитика | продажи, маржа, прогнозы, аномалии, новости/RAG, отчеты |
| `director` | Генеральный директор | Управленческий контроль | KPI, риски, forecast summary, управленческий отчет |

## Backend API permissions

| Backend action | Endpoint | Roles |
| --- | --- | --- |
| Auth profile/logout | `/api/v1/auth/me`, `/api/v1/auth/logout` | `admin`, `sales`, `accounting`, `analyst`, `director` |
| KPI read | `/api/v1/kpi/summary`, `/api/v1/kpi/alerts`, `/api/v1/kpi/snapshot` | `admin`, `sales`, `accounting`, `analyst`, `director` |
| Sales analytics | `/api/v1/analytics/sales`, `/api/v1/analytics/anomalies?metric=sales` | `admin`, `sales`, `analyst` |
| Margin analytics | `/api/v1/analytics/margin`, `/api/v1/analytics/anomalies?metric=margin\|purchase_price` | `admin`, `accounting`, `analyst`, `director` |
| Forecast read/run | `/api/v1/forecasts/latest`, `/api/v1/forecasts/run` | `admin`, `sales`, `analyst`, `director` |
| Backtest read | `/api/v1/backtests/latest` | `admin`, `sales`, `analyst`, `director` |
| Backtest run | `/api/v1/backtests/run` | `admin` |
| News digest/search | `/api/v1/news/digests/latest`, `/api/v1/news/search` | `admin`, `sales`, `analyst`, `director` |
| News refresh | `/api/v1/news/refresh` | `admin` |
| RAG chat | `/api/v1/chat/*` | `admin`, `analyst` |
| Executive report | `POST /api/v1/reports/executive` | `admin`, `analyst`, `director` |

Backend `NEWS_READ_ROLES` includes `sales`, but frontend navigation does not
expose `/news` for the `sales` role. Public/demo documentation should describe
the UI-visible role flow and not present sales as a news/RAG persona.

## Frontend route permissions

| Route | `admin` | `sales` | `accounting` | `analyst` | `director` |
| --- | --- | --- | --- | --- | --- |
| `/dashboard` | yes | yes | yes | yes | yes |
| `/executive/dashboard` | yes | yes | yes | yes | yes |
| `/import/sales` | yes | yes | no | no | no |
| `/import/purchases` | yes | no | yes | no | no |
| `/import/history` | yes | yes | yes | no | no |
| `/analytics/sales` | yes | yes | no | yes | no |
| `/analytics/margin` | yes | no | yes | yes | yes |
| `/forecast` | yes | yes | no | yes | yes |
| `/news` | yes | no | no | yes | yes |
| `/reports/executive` | yes | no | no | yes | yes |

`admin` is a frontend superuser. Direct links to unknown import subroutes remain
forbidden even for admin.

## Import permissions

| Backend action | Endpoint | `admin` | `sales` | `accounting` | `analyst` | `director` |
| --- | --- | --- | --- | --- | --- | --- |
| Sales import | `POST /api/v1/import/sales` | yes | yes | no | no | no |
| Purchase import | `POST /api/v1/import/purchases` | yes | no | yes | no | no |
| Demo generation | `POST /api/v1/import/generate-demo` | yes | no | no | no | no |
| Import history list | `GET /api/v1/import/jobs` | yes, all rows | yes, sales rows only | yes, purchase rows only | no | no |
| Import job details | `GET /api/v1/import/jobs/{job_id}` | yes, all rows | yes, sales rows only | yes, purchase rows only | no | no |

## Role behavior notes

- `sales` owns sales uploads and sales demand analysis, but does not see purchase
  import, margin analytics route, admin diagnostics, `/news`, or `/reports/executive`.
- `accounting` owns purchase uploads and financial/margin checks, but does not
  see sales import, sales analytics, admin diagnostics, `/news`, or `/reports/executive`.
- `analyst` reads sales, margin, forecast, news/RAG and reports, but does not
  perform imports or demo generation.
- `director` receives an executive dashboard, margin risks, forecast/news summary
  and `/reports/executive`, but does not see imports or admin diagnostics.
  Backend RAG chat actions remain restricted to `admin` and `analyst`.
- Demo generation remains an `admin` technical operation for local demo
  preparation, not a normal business import flow.
