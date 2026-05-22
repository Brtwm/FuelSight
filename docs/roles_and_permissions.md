# FuelSight: роли и backend permissions

## Назначение

Документ фиксирует фактическое поведение backend после Phase 3: разделение прав на ключевые API по бизнес-ролям и синхронизацию с frontend navigation.

FuelSight использует простую role-list модель через `require_roles(...)`. Новый RBAC framework в этой фазе не вводится.

## Роли

| Role slug | Бизнес-смысл |
| --- | --- |
| `admin` | Системный администратор. Техническое управление, demo generation, диагностика и полный backend-доступ к импортам. Slug остается `admin` и не переименовывается в `system_admin`. |
| `sales` | Отдел продаж. Загружает продажи и видит историю импортов продаж. |
| `accounting` | Бухгалтерия. Загружает закупки и видит историю импортов закупок. |
| `analyst` | Аналитический отдел. Читает аналитику, прогнозы, новости и RAG-чат, но не выполняет импорты и не читает техническую историю импортов в Phase 3. |
| `director` | Генеральный директор. Должен работать с управленческими/сводными данными, но не выполняет импорты и не читает техническую историю импортов в текущем backend MVP. |

## API permissions

| Backend action | Endpoint | Roles |
| --- | --- | --- |
| Auth profile/logout | `/api/v1/auth/me`, `/api/v1/auth/logout` | `admin`, `sales`, `accounting`, `analyst`, `director` |
| KPI read | `/api/v1/kpi/summary`, `/api/v1/kpi/alerts`, `/api/v1/kpi/snapshot` | `admin`, `sales`, `accounting`, `analyst`, `director` |
| Sales analytics | `/api/v1/analytics/sales`, `/api/v1/analytics/anomalies?metric=sales` | `admin`, `sales`, `analyst` |
| Margin analytics | `/api/v1/analytics/margin`, `/api/v1/analytics/anomalies?metric=margin\|purchase_price` | `admin`, `accounting`, `analyst`, `director` |
| Forecast read/run | `/api/v1/forecasts/latest`, `/api/v1/forecasts/run` | `admin`, `sales`, `analyst`, `director` |
| Backtest read | `/api/v1/backtests/latest` | `admin`, `sales`, `analyst`, `director` |
| Backtest run | `/api/v1/backtests/run` | `admin` |
| News read | `/api/v1/news/digests/latest`, `/api/v1/news/search` | `admin`, `sales`, `analyst`, `director` |
| News refresh | `/api/v1/news/refresh` | `admin` |
| RAG chat | `/api/v1/chat/*` | `admin`, `analyst` |
| Executive report | `POST /api/v1/reports/executive` | `admin`, `analyst`, `director` |

## Import permissions

| Backend action | Endpoint | `admin` | `sales` | `accounting` | `analyst` | `director` |
| --- | --- | --- | --- | --- | --- | --- |
| Sales import | `POST /api/v1/import/sales` | yes | yes | no | no | no |
| Purchase import | `POST /api/v1/import/purchases` | yes | no | yes | no | no |
| Demo generation | `POST /api/v1/import/generate-demo` | yes | no | no | no | no |
| Import history list | `GET /api/v1/import/jobs` | yes, all rows | yes, sales rows only | yes, purchase rows only | no | no |
| Import job details | `GET /api/v1/import/jobs/{job_id}` | yes, all rows | yes, sales rows only | yes, purchase rows only | no | no |

## Import history filtering

`ImportJob.entity_type` is treated as reliable backend metadata in Phase 2:

- `sales` can read only jobs with `entity_type == "sales"`;
- `accounting` can read only jobs with `entity_type == "purchases"`;
- `admin` can read all import jobs, including `historical_data`;
- `analyst` and `director` receive `403 Forbidden` for import history endpoints.

If `sales` explicitly requests `entity_type=purchases`, or `accounting` explicitly requests `entity_type=sales`, backend returns `403 Forbidden`.

For job details, backend preserves the distinction between missing and forbidden resources:

- missing job id returns `404 Not Found`;
- existing job outside the current role's allowed import type returns `403 Forbidden`.

## Notes

- Demo generation remains an `admin`-only technical operation for local demo and system preparation.
- Phase 3 does not change import file formats, import parsing, database models, or migrations.
- Existing seeded roles and demo users are kept: `admin`, `sales`, `accounting`, `analyst`, `director`.
- Frontend route `/reports/executive` отображает бизнес-функцию “Управленческий отчет” для `admin`, `analyst`, `director`; `sales` и `accounting` не видят пункт меню и получают `403` при прямом переходе.
- Phase 7 frontend ограничивает роль `sales` рабочими разделами отдела продаж: dashboard “Продажи”, импорт продаж, аналитика продаж и прогноз спроса. `sales` не видит purchase import, demo generation, admin tools, user management, полный маржинально-финансовый контур, news/RAG route и полный управленческий отчет. Ограниченные маржинальные риски для sales допустимы только как агрегированное предупреждение без закупочных цен и себестоимости.
