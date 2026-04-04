# Feature: Data Import

## Обзор
- **Назначение**: загрузка внутренних продаж и закупок из CSV/XLSX, а также генерация исторических данных для демонстрационного стенда.
- **Пользователь**: `admin`.
- **Точка входа**: `/import`.
- **Связанные фичи**: `auth`, `kpi-dashboard`, `sales-analytics`, `procurement-margin`, `demand-forecast`.

## User Flow
1. Администратор открывает страницу `/import`.
2. Выбирает режим: загрузка продаж, загрузка закупок или генерация исторических данных.
3. Система показывает шаблон обязательных полей и ограничения формата.
4. Пользователь загружает файл либо задаёт параметры генерации.
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
- **Поведение**: контейнер страницы, role guard `admin`.

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
- **Авторизация**: `admin`
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
- **Авторизация**: `admin`
- **Request**: `multipart/form-data` с файлом CSV/XLSX.

### `POST /api/v1/import/generate-demo`
- **Авторизация**: `admin`
- **Примечание**: технический path сохранён для совместимости, в UI режим называется `Исторические данные`.
- **Request Body**:
```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "products": ["AI_92", "AI_95", "DT"],
  "seed": 42,
  "replace_existing": false
}
```

### `GET /api/v1/import/jobs`
- **Авторизация**: `admin`
- **Response 200**: список импортов с полями `status`, `rows_success`, `rows_failed`, `started_at`, `finished_at`.

### `GET /api/v1/import/jobs/{job_id}`
- **Авторизация**: `admin`
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
- UI: drag-and-drop, отображение истории импортов, сообщение об ошибке.
- E2E: `admin` загружает продажи и закупки, затем видит обновлённые KPI.
