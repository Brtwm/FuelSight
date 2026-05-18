# FuelSight: ролевая модель и права доступа

## 1. Purpose

Этот документ фиксирует целевую RBAC-модель FuelSight до изменения backend и frontend. Он нужен как архитектурная граница для следующих фаз: сначала согласовать роли, зоны ответственности, доступ к страницам и API, затем уже менять модели, seed-данные, guards, middleware и тесты.

Phase 0 не меняет код приложения. В этом документе отдельно зафиксированы:

- текущее состояние, обнаруженное в коде и документации;
- целевая модель ролей для реалистичного enterprise-сценария;
- planned/proposed элементы, которых пока нет в проекте;
- implementation gaps, которые должны быть закрыты в будущих фазах.

## 2. Current state

### Обнаруженные роли

Сейчас проект фактически использует две роли:

| Role key | Где обнаружено | Текущее назначение |
| --- | --- | --- |
| `admin` | `backend/app/scripts/seed_core.py`, `backend/app/dependencies/auth.py`, API guards, frontend navigation | Импорт продаж и закупок, генерация demo data, refresh новостей, запуск backtest, доступ к бизнес-аналитике |
| `analyst` | `backend/app/scripts/seed_core.py`, API guards, frontend navigation | Просмотр KPI, аналитики продаж, маржи, прогнозов, новостей и Chat/RAG |

Текущие локальные seeded users:

| Role | Email/Login | Password | Current purpose |
| --- | --- | --- | --- |
| `admin` | `admin@fuelsight.local` | `admin12345` | Импорт, demo data refresh, операционные действия |
| `analyst` | `analyst@fuelsight.local` | `analyst12345` | Dashboard, аналитика, прогноз, новости, Chat/RAG |

### Frontend routes

Обнаруженные frontend routes:

| Route | Current status | Current role behavior |
| --- | --- | --- |
| `/login` | existing | Public login page |
| `/dashboard` | existing | Доступен авторизованным пользователям; навигация показывает для `admin`, `analyst` |
| `/import` | existing | `ProtectedRoute allowedRoles={['admin']}` |
| `/analytics/sales` | existing | Доступен авторизованным пользователям; навигация показывает для `admin`, `analyst` |
| `/analytics/margin` | existing | Доступен авторизованным пользователям; навигация показывает для `admin`, `analyst` |
| `/forecast` | existing | Доступен авторизованным пользователям; навигация показывает для `admin`, `analyst` |
| `/news` | existing | Доступен авторизованным пользователям; навигация показывает для `admin`, `analyst` |

Frontend тип роли сейчас ограничен `UserRole = 'admin' | 'analyst'`. Навигация в `AppShell` также типизирована как `Array<'admin' | 'analyst'>`.

### Backend access model

Backend использует dependency `require_roles(...)`, где разрешенные роли передаются строками. Это простая role-list модель, а не permission-based RBAC.

Текущая логика:

- `admin` имеет доступ к импорту продаж, импорту закупок, генерации demo data, истории импортов, refresh новостей и запуску backtest;
- `admin` и `analyst` имеют доступ к KPI, аналитике, прогнозам, последним backtests, новостям и Chat/RAG;
- user management API отсутствует;
- отдельный management report API отсутствует;
- defense report существует как service/pipeline/CLI artifact, но не как HTTP endpoint и не как отдельный frontend-раздел.

### Почему модель `admin + analyst` недостаточно реалистична

Текущая модель удобна для раннего MVP, но плохо отражает работу предприятия:

- `admin` смешивает техническое администрирование и бизнес-операции. В реальной системе системный администратор управляет пользователями, настройками и техническими процессами, но не является владельцем продаж, закупок, маржинальности и управленческих решений.
- Нет разделения ответственности между продажами, бухгалтерией, аналитикой и руководством. Все бизнес-процессы фактически сведены к одному `analyst` и чрезмерно широкому `admin`.
- Невозможно убедительно показать enterprise/RBAC-сценарий на защите диплома: роли не соответствуют отделам предприятия и не демонстрируют безопасное разграничение данных.
- Сложно безопасно ограничить доступ к закупкам, продажам, маржинальности и управленческим отчетам. Например, отдел продаж не должен видеть всю закупочную себестоимость, а бухгалтерия не всегда должна видеть полный операционный sales drill-down.
- Директор в старой модели отсутствует. Чтобы показать управленческий сценарий, его пришлось бы вести под `admin` или `analyst`, что неверно с точки зрения бизнес-процесса: директор принимает решения по агрегированным KPI и отчетам, но не импортирует файлы и не администрирует пользователей.

### Риски для дипломной демонстрации и архитектуры

- `admin` выглядит как универсальный бизнес-пользователь, а не как техническая роль.
- Ролевые границы трудно объяснить комиссии: система не показывает отдел продаж, бухгалтерию и руководство как разные аудитории.
- Будущие изменения frontend/backend могут начать добавлять проверки хаотично, если сначала не зафиксировать целевую permission model.
- При расширении проекта возрастает риск inconsistent guards: один раздел может проверять роль, другой - конкретный endpoint, третий - только видимость навигации.

## 3. Target role model

| Role key | Display name | Department / owner | Business responsibility | What this role must NOT do | Why this role exists |
| --- | --- | --- | --- | --- | --- |
| `admin` | Системный администратор | IT / technical operations | Управление пользователями, ролями, demo data generation, системными настройками, технической диагностикой и контролем доступности | Не должен быть основным бизнес-пользователем для анализа продаж, закупок, маржинальности и управленческих решений | Отделяет техническое администрирование от бизнес-процессов и делает RBAC реалистичным |
| `sales` | Отдел продаж | Коммерческий отдел / продажи | Загрузка и ведение продаж, просмотр динамики продаж, анализ спроса, работа с прогнозом спроса для коммерческих решений | Не должен управлять пользователями, импортировать закупки, видеть полную закупочную себестоимость и системные настройки | Показывает операционную бизнес-роль, отвечающую за revenue-side данные |
| `accounting` | Бухгалтерия | Финансы / бухгалтерия | Загрузка закупок, контроль себестоимости, маржинальности, сверка импортов закупок и учетных показателей | Не должна управлять пользователями, импортировать продажи без бизнес-основания, пользоваться полным RAG/новостным контекстом как основной ролью | Разделяет финансово-учетные данные и защищает закупочную себестоимость |
| `analyst` | Аналитический отдел | Аналитика / BI | Полная аналитика продаж, закупок, маржинальности, спроса, прогнозов, новостей, рыночного контекста и Chat/RAG | Не должен управлять пользователями и выполнять техническое demo generation как штатную обязанность | Является главным владельцем аналитических выводов и подготовки материалов для руководства |
| `director` | Генеральный директор | Executive management | Просмотр агрегированных KPI, прогнозов, summary-аналитики, рыночного контекста и управленческого отчета | Не должен импортировать raw data, управлять пользователями, запускать demo generation или заниматься технической настройкой | Показывает управленческий сценарий принятия решений без операционного drill-down |

## 4. Frontend access matrix

Легенда:

- `yes` - полный доступ;
- `no` - доступа нет;
- `limited` - ограниченный доступ, например только агрегаты или без чувствительных финансовых деталей;
- `optional` - доступ можно включить позднее, если это соответствует сценарию защиты;
- `own` - доступ только к собственным импортам/операциям;
- `read-only` - просмотр без изменения;
- `summary` - агрегированные управленческие выводы без drill-down до операционных данных.

| Frontend section | Current route / status | admin | sales | accounting | analyst | director |
| --- | --- | --- | --- | --- | --- | --- |
| Dashboard KPI | `/dashboard` existing | yes | limited | limited | yes | yes |
| Импорт продаж | `/import`, sales tab existing | yes | yes | no | optional | no |
| Импорт закупок | `/import`, purchases tab existing | yes | no | yes | optional | no |
| История импортов | `/import`, history existing | yes | own | own | yes | read-only |
| Аналитика продаж | `/analytics/sales` existing | yes | yes | limited | yes | summary |
| Маржинальная аналитика | `/analytics/margin` existing | yes | limited | yes | yes | summary |
| Прогноз спроса | `/forecast` existing | yes | yes | limited | yes | yes |
| Новости / рыночный контекст | `/news` existing | yes | optional | no/optional | yes | yes |
| Chat / RAG | `/news`, chat tab existing | yes | optional | no/optional | yes | optional |
| Управленческий отчет | planned/proposed frontend section | yes | no | no/optional | yes | yes |
| Demo data generation | `/import`, historical data tab existing | yes | no | no | no | no |
| User management | planned/proposed frontend section | yes | no | no | no | no |

Примечание: сейчас `/import` является полностью admin-only. Целевая модель требует разделить доступ внутри страницы или вынести импорт продаж/закупок в permission-aware действия, чтобы `sales` мог загружать продажи, а `accounting` - закупки.

## 5. Backend permissions matrix

Таблица ниже разделяет существующие backend endpoints и proposed endpoints. Planned/proposed строки не должны считаться реализованными.

| Domain | Method | Endpoint / Route | Current status | admin | sales | accounting | analyst | director | Notes / rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auth/users | POST | `/api/v1/auth/login` | existing | yes | yes | yes | yes | yes | Public login endpoint; роль определяется после успешной аутентификации |
| auth/users | POST | `/api/v1/auth/refresh` | existing | yes | yes | yes | yes | yes | Доступ через refresh cookie для всех аутентифицированных ролей |
| auth/users | GET | `/api/v1/auth/me` | existing | yes | yes | yes | yes | yes | Сейчас разрешены только `admin`, `analyst`; target должен поддержать все роли |
| auth/users | POST | `/api/v1/auth/logout` | existing | yes | yes | yes | yes | yes | Сейчас разрешены только `admin`, `analyst`; target должен поддержать все роли |
| auth/users | GET | `/api/v1/users` | planned/proposed | yes | no | no | no | no | User management должен быть технической зоной `admin` |
| auth/users | POST | `/api/v1/users` | planned/proposed | yes | no | no | no | no | Создание пользователей и назначение ролей |
| auth/users | PATCH | `/api/v1/users/{user_id}` | planned/proposed | yes | no | no | no | no | Изменение display name, активности, роли, reset demo password |
| auth/users | DELETE | `/api/v1/users/{user_id}` | planned/proposed | yes | no | no | no | no | Удаление или деактивация пользователя; предпочтительна soft deactivate |
| demo/system | GET | `/api/v1/health` | existing | yes | limited | limited | yes | limited | Технический health endpoint сейчас public; для UI можно показывать детали только admin/analyst |
| imports | POST | `/api/v1/import/sales` | existing | yes | yes | no | optional | no | Сейчас admin-only; target owner - sales, admin может запускать для диагностики/demo |
| imports | POST | `/api/v1/import/purchases` | existing | yes | no | yes | optional | no | Сейчас admin-only; target owner - accounting |
| demo/system | POST | `/api/v1/import/generate-demo` | existing | yes | no | no | no | no | Техническая генерация demo data; не бизнес-операция |
| imports | GET | `/api/v1/import/jobs` | existing | yes | own | own | yes | read-only | Сейчас admin-only; target требует own/read_all фильтрацию |
| imports | GET | `/api/v1/import/jobs/{job_id}` | existing | yes | own | own | yes | read-only | Сейчас admin-only; target требует проверку владельца, entity type и summary visibility |
| sales | GET | `/api/v1/kpi/summary` | existing | yes | limited | limited | yes | yes | Сейчас admin/analyst; target должен ограничивать детализацию по роли |
| sales | GET | `/api/v1/kpi/alerts` | existing | yes | limited | limited | yes | yes | Для director нужны summary alerts без операционного drill-down |
| sales | GET | `/api/v1/kpi/snapshot` | existing | yes | limited | limited | yes | yes | Агрегированный ряд спроса подходит для director/sales/accounting с разной детализацией |
| sales | GET | `/api/v1/analytics/sales` | existing | yes | yes | limited | yes | summary | Сейчас admin/analyst; target требует sales full, accounting/director limited/summary |
| purchases | GET | `/api/v1/analytics/margin` | existing | yes | limited | yes | yes | summary | Содержит закупочную цену и маржу; sales/director не должны видеть полный drill-down |
| analytics | GET | `/api/v1/analytics/anomalies` | existing | yes | limited | limited | yes | summary | Нужно фильтровать metric-level доступ: sales, margin, purchase_price |
| forecasts | POST | `/api/v1/forecasts/run` | existing | yes | yes | limited | yes | no/read-only | Сейчас admin/analyst; director должен читать результаты, а не запускать операционные сценарии |
| forecasts | GET | `/api/v1/forecasts/latest` | existing | yes | yes | limited | yes | yes | Forecast read нужен sales, analyst и director; accounting ограниченно |
| forecasts | POST | `/api/v1/backtests/run` | existing | yes | no | no | optional | no | Сейчас admin-only; в target это technical/model operation, возможно analyst optional |
| forecasts | GET | `/api/v1/backtests/latest` | existing | yes | no | no | yes | no/read-only | Analyst видит качество модели; director может получать summary через report |
| news/market context | GET | `/api/v1/news/digests/latest` | existing | yes | optional | no/optional | yes | yes | Рыночный контекст важен analyst/director; sales optional |
| news/market context | GET | `/api/v1/news/search` | existing | yes | optional | no/optional | yes | yes | Поиск новостей может быть ограничен для accounting |
| news/market context | POST | `/api/v1/news/refresh` | existing | yes | no | no | no | no | Сейчас admin-only; техническое обновление источников |
| chat/rag | POST | `/api/v1/chat/sessions` | existing | yes | optional | no/optional | yes | optional | Сейчас admin/analyst; target делает Chat/RAG основным инструментом analyst |
| chat/rag | GET | `/api/v1/chat/sessions/{session_id}/messages` | existing | yes | optional | no/optional | yes | optional | Доступ должен учитывать владельца chat session и роль |
| chat/rag | POST | `/api/v1/chat/sessions/{session_id}/messages` | existing | yes | optional | no/optional | yes | optional | Нужно не раскрывать запрещенные данные через RAG context |
| reports | GET | `/api/v1/reports/management/latest` | planned/proposed | yes | no | no/optional | yes | yes | Отдельный управленческий отчет для director и analyst |
| reports | POST | `/api/v1/reports/management/generate` | planned/proposed | yes | no | no/optional | yes | no/read-only | Director читает итог, analyst/admin могут формировать |
| analytics | GET | `/api/v1/analytics/sales/summary` | planned/proposed | yes | yes | limited | yes | summary | Optional split endpoint, если summary visibility нельзя безопасно обеспечить на текущем `/analytics/sales` |
| analytics | GET | `/api/v1/analytics/margin/summary` | planned/proposed | yes | limited | yes | yes | summary | Optional split endpoint для director/sales без чувствительного drill-down |

## 6. Data visibility and restrictions

### Ограничения видимости данных

- `sales` видит продажи, динамику спроса, агрегаты по forecast и ограниченную маржинальность. Эта роль не должна видеть полную закупочную себестоимость, поставщиков и детальные закупочные цены, если это не требуется бизнес-процессом.
- `accounting` видит закупки, себестоимость, закупочную цену, маржинальность и историю закупочных импортов. Полный операционный drill-down продаж для бухгалтерии не является обязательным и должен быть ограничен до агрегатов, если нет отдельного бизнес-требования.
- `analyst` видит широкий набор данных по продажам, закупкам, маржинальности, прогнозам, рыночному контексту и RAG, потому что отвечает за аналитические выводы и подготовку материалов для руководства.
- `director` видит агрегированные KPI, прогнозы, summary-аналитику, новости и управленческие выводы. Директор не должен работать с raw import jobs, row-level ошибками файлов и техническими настройками.
- `admin` управляет системой, demo data и пользователями. Бизнес-данные могут быть доступны для диагностики, но не являются основной зоной ответственности этой роли.

### Ограничения на действия

| Action | Allowed roles | Restriction |
| --- | --- | --- |
| Импорт продаж | `admin`, `sales`, optional `analyst` | `sales` является бизнес-владельцем; `admin` использует действие для диагностики/demo |
| Импорт закупок | `admin`, `accounting`, optional `analyst` | `accounting` является бизнес-владельцем закупочных данных |
| Просмотр истории импортов | `admin`, `analyst`, `sales` own, `accounting` own, `director` read-only/summary | Нужна фильтрация по владельцу и entity type |
| Demo data generation | `admin` | Только локальный demo/dev и техническая подготовка стенда |
| User management | `admin` | Planned/proposed; не должно быть доступно бизнес-ролям |
| Управленческий отчет | `analyst`, `director`, `admin`; optional `accounting` для финансовых частей | Director читает, analyst формирует, admin диагностирует |
| Chat/RAG | `analyst`; `admin` yes; `sales` optional; `accounting` no/optional; `director` optional | RAG должен учитывать permission boundary и не раскрывать запрещенные данные |
| News refresh | `admin` | Техническое обновление источников, не бизнес-операция |
| Forecast run | `analyst`, `sales`, `admin`; `accounting` limited; `director` read-only | Director должен читать результат, а не запускать операционные сценарии |
| Backtest/retraining | `admin`, optional `analyst` | Техническая/model operation, не sales/accounting/director процесс |

## 7. Demo accounts

Целевые demo accounts для будущей реализации:

| Role | Email/Login | Password | Purpose |
| --- | --- | --- | --- |
| `admin` | `admin@fuelsight.local` | `admin_demo_2026` | Системное администрирование, пользователи, demo data |
| `sales` | `sales@fuelsight.local` | `sales_demo_2026` | Импорт продаж, аналитика продаж, forecast |
| `accounting` | `accounting@fuelsight.local` | `accounting_demo_2026` | Импорт закупок, маржинальность, учетные показатели |
| `analyst` | `analyst@fuelsight.local` | `analyst_demo_2026` | Полная аналитика, прогнозы, новости, RAG, отчеты |
| `director` | `director@fuelsight.local` | `director_demo_2026` | KPI, прогнозы, summary-аналитика, управленческий отчет |

Эти учетные записи предназначены только для локальной демонстрации и не должны использоваться в production.

Implementation gap: текущий seed создает только `admin@fuelsight.local / admin12345` и `analyst@fuelsight.local / analyst12345`. Новые demo passwords являются target design для будущей migration/seed phase.

## 8. Diploma defense demonstration scenario

### 1. Войти как `admin`

- Показать, что `admin` - техническая роль, а не главный бизнес-пользователь.
- Показать demo data generation через существующий `/import` tab `Исторические данные`.
- Показать user management как planned/proposed раздел, если он еще не реализован.
- Объяснить, что `admin` может диагностировать данные, но не является владельцем анализа продаж, закупок и управленческих решений.

### 2. Войти как `sales`

- Показать загрузку или просмотр продаж через целевой доступ к `/import` sales tab.
- Показать `/analytics/sales` как основной рабочий раздел отдела продаж.
- Показать `/forecast` для оценки спроса и коммерческих решений.
- Объяснить ограничения: нет доступа к импорту закупок, полной закупочной себестоимости, user management и demo generation.

### 3. Войти как `accounting`

- Показать загрузку или просмотр закупок через целевой доступ к `/import` purchases tab.
- Показать `/analytics/margin` для контроля себестоимости, закупочной цены и маржинальности.
- Показать историю собственных закупочных импортов и сверку ошибок.
- Объяснить, что бухгалтерия отвечает за финансово-учетные данные, но не является владельцем полного sales drill-down и RAG/новостного анализа.

### 4. Войти как `analyst`

- Показать `/dashboard`, `/analytics/sales`, `/analytics/margin` и `/forecast`.
- Показать `/news` как рыночный контекст.
- Показать Chat/RAG на `/news`, если он реализован и включен.
- Показать planned/proposed management report generation, если отдельный раздел еще не реализован.
- Объяснить, что аналитик готовит выводы для руководства на основе продаж, закупок, маржи, прогнозов и внешнего контекста.

### 5. Войти как `director`

- Показать Dashboard KPI.
- Показать forecast read-only или без операционного запуска.
- Показать summary-аналитику продаж и маржинальности.
- Показать управленческий отчет как planned/proposed, если отдельный route/API еще не реализован.
- Объяснить, что директор не импортирует raw data, не управляет пользователями и не занимается demo generation; он принимает решения по агрегированной информации.

## 9. Implementation notes for future phases

### Recommended backend permission representation

Следующим фазам лучше перейти от hard-coded role lists к permission-based RBAC:

```text
role -> permissions -> endpoint/action
```

Роль остается бизнес-идентификатором пользователя, а permission определяет конкретное действие. Это позволит не дублировать сложные role lists в каждом endpoint.

### Suggested permission constants

Рекомендуемый стиль именования:

- `users:read`
- `users:write`
- `demo:generate`
- `imports:sales:create`
- `imports:purchases:create`
- `imports:history:own`
- `imports:history:read_all`
- `analytics:sales:read`
- `analytics:sales:summary`
- `analytics:margin:read`
- `analytics:margin:summary`
- `forecast:read`
- `forecast:run`
- `market_context:read`
- `market_context:refresh`
- `rag:chat`
- `reports:management:read`
- `reports:management:generate`
- `system:health:read`
- `models:backtest:run`
- `models:backtest:read`

### Suggested role-to-permission mapping

```text
admin:
  users:read, users:write, demo:generate,
  imports:sales:create, imports:purchases:create,
  imports:history:read_all,
  system:health:read, market_context:refresh,
  models:backtest:run, models:backtest:read

sales:
  imports:sales:create, imports:history:own,
  analytics:sales:read, analytics:margin:summary,
  forecast:read, forecast:run

accounting:
  imports:purchases:create, imports:history:own,
  analytics:sales:summary, analytics:margin:read,
  forecast:read

analyst:
  imports:history:read_all,
  analytics:sales:read, analytics:margin:read,
  forecast:read, forecast:run,
  market_context:read, rag:chat,
  reports:management:read, reports:management:generate,
  models:backtest:read

director:
  analytics:sales:summary, analytics:margin:summary,
  forecast:read, market_context:read,
  reports:management:read
```

Это mapping является проектным ориентиром, а не реализованным кодом.

### Frontend route guard strategy

- Расширить `UserRole` до `admin | sales | accounting | analyst | director`.
- Ввести frontend permission map или получать permissions из `/auth/me`.
- Навигацию строить по permissions, а не по двум hard-coded ролям.
- Для `/import` проверять permissions на уровне tab/action: sales import, purchases import, history, demo generation.
- Для `/news` отдельно контролировать digest/search и Chat/RAG, чтобы accounting или director не получали лишний доступ через один общий экран.
- Для director использовать summary/read-only states вместо скрытого доступа к операционным controls.

### Backend dependency/middleware strategy

- Сохранить `get_current_user`, но добавить dependency уровня `require_permissions(...)`.
- Не удалять `require_roles(...)` сразу, если это увеличивает риск; можно временно держать совместимость и мигрировать endpoints постепенно.
- Для endpoints с `own` доступом добавить object-level checks: `started_by`, `entity_type`, ownership of chat session.
- Для summary access не отдавать чувствительные поля из service layer или schema layer, а не только скрывать их на frontend.
- Для RAG использовать context filtering по permissions, чтобы запрещенные закупочные или финансовые данные не попадали в retrieval context.

### Migration/seed strategy for demo accounts

- Добавить роли `sales`, `accounting`, `director` в seed/migration.
- Обновить local demo users до `_demo_2026` credentials или явно поддержать переходный период для старых паролей только в dev/test.
- Не использовать demo credentials в production.
- Обновить тестовые fixtures и e2e personas по новым ролям.

### Testing strategy

- Backend: добавить role boundary tests для каждого endpoint group.
- Backend: проверить `403` для запрещенных действий и `200/202` для разрешенных ролей.
- Backend: отдельно проверить `own` import history и chat session ownership.
- Frontend: проверить видимость навигации для всех пяти ролей.
- Frontend: проверить, что director видит summary/read-only controls, а sales/accounting не видят чужие import actions.
- Docs/contracts: обновить API documentation после реализации, но не смешивать planned endpoints с existing.

## 10. Implementation gaps

Обнаруженные расхождения между текущей реализацией и целевой RBAC-моделью:

- `docs/roles_and_permissions.md` сейчас отсутствовал до Phase 0.
- `UserRole` во frontend поддерживает только `admin | analyst`.
- Backend `require_roles` основан на списках ролей, а не на permissions.
- Нет user management API.
- Нет user management frontend page.
- Нет dedicated management report API.
- Нет dedicated management report frontend route.
- Demo accounts для `sales`, `accounting`, `director` не seeded.
- Текущие demo passwords отличаются от целевых `_demo_2026` credentials.
- Existing import API полностью admin-only; target model требует разделить sales import и purchases import между `sales` и `accounting`.
- Existing import history полностью admin-only; target model требует `own` и `read_all`.
- Existing analytics endpoints возвращают широкие данные для `admin` и `analyst`; target model требует limited/summary visibility для `sales`, `accounting`, `director`.
- Existing `/news` объединяет digest, search и Chat/RAG; target model может требовать tab-level или permission-level restrictions.
- Existing `admin` остается overpowered для бизнес-страниц до будущего refactor permissions.
- Director currently cannot be represented without adding role, seed user, frontend guards and backend permissions.

## 11. Acceptance checklist

- [ ] docs/roles_and_permissions.md exists
- [ ] Old admin + analyst model is explicitly criticized and explained
- [ ] admin is defined as a technical role, not a universal business role
- [ ] Business operations are split between sales/accounting/analyst/director
- [ ] Frontend access matrix is present
- [ ] Backend endpoint/permission matrix is present
- [ ] Existing endpoints are separated from planned/proposed endpoints
- [ ] Demo accounts are listed for all roles
- [ ] Diploma defense scenario is included
- [ ] Future implementation notes are included
- [ ] No application code was changed in this phase
