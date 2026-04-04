# Feature: Sales Analytics

## Обзор
- **Назначение**: дать пользователю подробный анализ продаж и спроса по топливу с акцентом на временной ряд, сезонность и сравнение периодов.
- **Пользователь**: `admin`, `analyst`.
- **Точка входа**: `/analytics/sales`.
- **Связанные фичи**: `kpi-dashboard`, `procurement-margin`, `demand-forecast`, `news-digest-chat`.

## User Flow
1. Пользователь открывает страницу аналитики продаж.
2. Выбирает продукт, период и гранулярность `day/week/month`.
3. Система строит временной ряд объёма продаж и накладывает динамику розничной цены.
4. Пользователь переключается между общим графиком, сезонностью и сравнением периодов.
5. При наличии выбросов открывает список аномалий и переходит к соседним разделам для причинного анализа.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Default | Параметры по умолчанию | График и фильтры за 30 дней |
| Loading | Идёт запрос аналитики | Skeleton графиков и таблицы |
| Empty | Нет истории по фильтру | Placeholder и подсказка изменить период |
| Filled | Данные загружены | Графики, таблица сравнений, аномалии |
| Error | Ошибка API | Alert и retry |

## Ключевые компоненты

### `SalesAnalyticsPage`
- **Расположение**: `src/pages/SalesAnalyticsPage.tsx`
- **Поведение**: собирает фильтры, графики и боковой блок пояснений.

### `SalesFilterBar`
- **Расположение**: `src/features/sales/components/SalesFilterBar.tsx`
- **Пропсы**: `{ productCode, dateRange, granularity }`
- **Поведение**: синхронизирует фильтры с URL query params.

### `SalesTrendChart`
- **Расположение**: `src/features/sales/components/SalesTrendChart.tsx`
- **Поведение**: показывает продажи и розничную цену на двух осях.

### `SeasonalityPanel`
- **Расположение**: `src/features/sales/components/SeasonalityPanel.tsx`
- **Поведение**: агрегации по дням недели и месяцам.

### `SalesAnomalyTable`
- **Расположение**: `src/features/sales/components/SalesAnomalyTable.tsx`
- **Поведение**: список аномалий спроса и переход в смежные разделы.

## API-контракты

### `GET /api/v1/analytics/sales`
- **Авторизация**: `admin`, `analyst`
- **Query Params**:
  - `product_code`
  - `date_from`
  - `date_to`
  - `granularity=day|week|month`
- **Response 200**:
```json
{
  "data": {
    "product_code": "AI_95",
    "granularity": "day",
    "series": [
      {
        "period_start": "2026-03-01",
        "volume_liters": 12450.2,
        "avg_retail_price_rub": 59.8
      }
    ],
    "seasonality": {
      "by_weekday": [
        { "weekday": "Mon", "avg_volume_liters": 11800.0 }
      ],
      "by_month": [
        { "month": 3, "avg_volume_liters": 12150.0 }
      ]
    },
    "comparisons": {
      "mom_pct": 2.4,
      "yoy_pct": null
    }
  },
  "error": null,
  "meta": {}
}
```

### `GET /api/v1/analytics/anomalies`
- **Авторизация**: `admin`, `analyst`
- **Query Params**:
  - `metric=sales`
  - `product_code`
  - `date_from`
  - `date_to`

## Модель данных
- Новых таблиц не создаёт.
- Использует `sales_daily` и производные аналитические витрины.

## Frontend-требования
- Фильтр продукта обязателен.
- Фильтры (`product_code`, `date_from`, `date_to`, `granularity`) синхронизируются с URL query params.
- Сравнение периодов показывать только при достаточной истории.
- В интерфейсе отдельно отмечать, когда `YoY` недоступен.
- Empty-state содержит CTA на `/import`.

## Backend-требования
- Возвращать данные уже отсортированными по дате.
- При недельной и месячной гранулярности делать агрегацию на backend, а не в браузере.
- Для аномалий вернуть severity и краткое объяснение.
- Поддержать ситуацию с коротким рядом без падения endpoint.

## Edge Cases
- Данных недостаточно для `YoY`.
- Выбран период, где по продукту не было продаж.
- В истории есть разрыв из-за отсутствия загрузок.
- По продукту существует резкий выброс, вызванный синтетическим шоком.

## Тестирование
- API: day/week/month aggregation, empty ranges, anomalies response.
- UI: фильтрация, смена гранулярности, отображение `YoY` как `N/A`.
- E2E: переход из KPI на страницу продаж и анализ выбранного продукта.
