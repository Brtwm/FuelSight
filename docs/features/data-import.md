# Feature: Data Import

## Обзор
- **Назначение**: загрузка внутренних продаж и закупок из CSV/XLSX, а также генерация исторических данных для демонстрационного стенда.
- **Пользователь**: `admin`, `sales`, `accounting`.
- **Точка входа**: `/import/sales`, `/import/purchases`, `/import/history`.
- **Связанные фичи**: `auth`, `kpi-dashboard`, `sales-analytics`, `procurement-margin`, `demand-forecast`.

## User Flow
1. Пользователь открывает доступный route импорта: `sales` — `/import/sales`,
   `accounting` — `/import/purchases`, `admin` — любой import route.
2. Выбирает доступный режим: загрузка продаж, загрузка закупок или, только для
   `admin`, генерация исторических данных.
3. Система показывает шаблон обязательных полей и ограничения формата.
4. Пользователь перетаскивает файл в upload-зону или выбирает его через системный file picker, либо задаёт параметры генерации.
5. Backend создаёт `import_job`, валидирует данные и сохраняет результат.
6. Пользователь видит итог: успешно загруженные строки, ошибки и ссылку на историю импортов.
7. После успешного импорта система обновляет KPI и аналитические разделы.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Default | Страница открыта | Табы `Продажи`, `Закупки`, `Исторические данные`, история |
| UploadReady | Файл выбран | Название файла, кнопка запуска |
| Uploading | Отправка файла | Progress indicator |
| PartialSuccess | Часть строк отклонена | Счётчики успеха/ошибок, ссылка на отчёт |
| Success | Импорт завершён | Toast и обновлённая история |
| ValidationError | Ошибка схемы | Список проблем по колонкам |
| EmptyHistory | Импортов ещё не было | Placeholder |

## Ключевые компоненты

### `ImportPage`
- **Расположение**: `src/pages/ImportPage.tsx`
- **Поведение**: контейнер страницы, role-aware tabs и route guards для sales,
  purchases, history и генерации начальной истории, доступной только `admin`.

### `ImportUploadCard`
- **Расположение**: `src/features/import/components/ImportUploadCard.tsx`
- **Пропсы**: `{ entityType: 'sales' | 'purchases' }`
- **Поведение**: drag-and-drop upload и отображение шаблона колонок.

### `GenerateHistoryDataForm`
- **Расположение**: `src/features/import/components/GenerateHistoryDataForm.tsx`
- **Пропсы**: `{ onSubmit: (payload) => void }`
- **Валидация**:
  - `start_date < end_date`;
  - минимум один продукт;
  - `seed` целое число.

### `ImportJobsTable`
- **Расположение**: `src/features/import/components/ImportJobsTable.tsx`
- **Поведение**: история последних импортов и текущие статусы.

## API-контракты

### `POST /api/v1/import/sales`
- **Авторизация**: `admin`, `sales`
- **Request**: `multipart/form-data` с файлом CSV/XLSX.
- **Response 202**:
```json
{
  "data": {
    "job_id": "uuid",
    "entity_type": "sales",
    "status": "queued"
  },
  "error": null,
  "meta": {}
}
```

### `POST /api/v1/import/purchases`
- **Авторизация**: `admin`, `accounting`
- **Request**: `multipart/form-data` с файлом CSV/XLSX.

### `POST /api/v1/import/generate-demo`
- **Авторизация**: `admin`
- **Примечание**: технический path сохранён для совместимости, в UI режим называется `Исторические данные`.
- **Demo-run**: `scripts/run_full_demo.py` передаёт rolling окно до текущей даты, чтобы dashboard/analytics/forecast не открывались на пустом периоде.
- **Request Body**:
```json
{
  "start_date": "2025-04-26",
  "end_date": "2026-04-25",
  "products": ["AI_92", "AI_95", "DT_S", "DT_W"],
  "seed": 42,
  "replace_existing": false
}
```

### `GET /api/v1/import/jobs`
- **Авторизация**: `admin`, `sales`, `accounting`
- **Фильтрация**: `sales` видит только jobs продаж, `accounting` видит только
  jobs закупок, `admin` видит все jobs.
- **Response 200**: список импортов с полями `status`, `rows_success`, `rows_failed`, `started_at`, `finished_at`.

### `GET /api/v1/import/jobs/{job_id}`
- **Авторизация**: `admin`, `sales`, `accounting`
- **Response 200**: детали импорта и путь к error report при наличии.

## Модель данных
```sql
CREATE TABLE import_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(32) NOT NULL,
  source_type VARCHAR(32) NOT NULL,
  file_name VARCHAR(255),
  status VARCHAR(32) NOT NULL,
  rows_total INTEGER NOT NULL DEFAULT 0,
  rows_success INTEGER NOT NULL DEFAULT 0,
  rows_failed INTEGER NOT NULL DEFAULT 0,
  error_report_path TEXT,
  started_by UUID NOT NULL REFERENCES users(id),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ
);
```

## Frontend-требования
- Для файловой загрузки показывать шаблон обязательных колонок:
  - продажи: `date`, `product_code`, `volume_liters`, `revenue_rub`, `avg_retail_price_rub`;
  - закупки: `date`, `product_code`, `volume_liters`, `purchase_price_rub`, `supplier_name`, `logistics_cost_rub`.
- После успешного импорта инвалидировать query cache для `/dashboard`, `/analytics/*` и `/forecast`.
- Ошибки формата должны быть читаемыми, а не сырыми traceback.
- Upload UI поддерживает drag-and-drop и fallback через обычный file input.
- Пользователь видит ограничения до отправки: `CSV/XLSX`, до `10 MiB`, до `50 000` строк; backend остаётся source of truth для лимитов.

## Backend-требования
- Поддержать CSV и XLSX.
- Валидировать обязательные колонки, типы, дубликаты, отрицательные значения и неизвестные `product_code`.
- Реализовать частичный успех: валидные строки сохраняются, невалидные отражаются в error report.
- Генератор исторических данных должен создавать согласованные продажи и закупки, пригодные для прогноза и маржи.

## Edge Cases
- Пользователь загружает пустой файл.
- Повторная загрузка того же batch.
- В файле встречается неизвестный `product_code`.
- Дата в закупках позже текущего дня.
- Пользователь запускает генерацию исторических данных поверх существующих данных.

## Тестирование
- API: загрузка валидного CSV, невалидного XLSX, частичный успех, генерация исторических данных.
- UI: drag-and-drop, fallback file input, отображение истории импортов, сообщение об ошибке.
- E2E/API: `sales` загружает продажи, `accounting` загружает закупки, `admin`
  обновляет начальную историю и видит диагностику.
