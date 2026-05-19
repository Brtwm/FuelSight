# FuelSight: роли и backend permissions

## Назначение

Документ фиксирует фактическое поведение backend после Phase 2: разделение прав на импорты и связанные import endpoints по бизнес-ролям. Frontend в Phase 2 не менялся, поэтому этот документ описывает именно backend authorization.

FuelSight использует простую role-list модель через `require_roles(...)`. Новый RBAC framework в этой фазе не вводится.

## Роли

| Role slug | Бизнес-смысл |
| --- | --- |
| `admin` | Системный администратор. Техническое управление, demo generation, диагностика и полный backend-доступ к импортам. Slug остается `admin` и не переименовывается в `system_admin`. |
| `sales` | Отдел продаж. Загружает продажи и видит историю импортов продаж. |
| `accounting` | Бухгалтерия. Загружает закупки и видит историю импортов закупок. |
| `analyst` | Аналитический отдел. Читает аналитику и историю импортов, но не выполняет импорты и не запускает demo generation. |
| `director` | Генеральный директор. Должен работать с управленческими/сводными данными, но не выполняет импорты и не читает техническую историю импортов в текущем backend MVP. |

## Import permissions

| Backend action | Endpoint | `admin` | `sales` | `accounting` | `analyst` | `director` |
| --- | --- | --- | --- | --- | --- | --- |
| Sales import | `POST /api/v1/import/sales` | yes | yes | no | no | no |
| Purchase import | `POST /api/v1/import/purchases` | yes | no | yes | no | no |
| Demo generation | `POST /api/v1/import/generate-demo` | yes | no | no | no | no |
| Import history list | `GET /api/v1/import/jobs` | yes, all rows | yes, sales rows only | yes, purchase rows only | yes, all rows | no |
| Import job details | `GET /api/v1/import/jobs/{job_id}` | yes, all rows | yes, sales rows only | yes, purchase rows only | yes, all rows | no |

## Import history filtering

`ImportJob.entity_type` is treated as reliable backend metadata in Phase 2:

- `sales` can read only jobs with `entity_type == "sales"`;
- `accounting` can read only jobs with `entity_type == "purchases"`;
- `admin` and `analyst` can read all import jobs, including `historical_data`;
- `director` receives `403 Forbidden` for import history endpoints.

If `sales` explicitly requests `entity_type=purchases`, or `accounting` explicitly requests `entity_type=sales`, backend returns `403 Forbidden`.

For job details, backend preserves the distinction between missing and forbidden resources:

- missing job id returns `404 Not Found`;
- existing job outside the current role's allowed import type returns `403 Forbidden`.

## Notes

- Demo generation remains an `admin`-only technical operation for local demo and system preparation.
- Phase 2 does not change import file formats, import parsing, database models, migrations, or frontend guards.
- Existing seeded roles and demo users are kept: `admin`, `sales`, `accounting`, `analyst`, `director`.
