# Feature: Procurement and Margin Analytics

## Обзор
- **Назначение**: анализировать закупочную цену, розничную цену, валовую маржу и аномальные отклонения по каждому виду топлива.
- **Пользователь**: `admin`, `analyst`.
- **Точка входа**: `/analytics/margin`.
- **Связанные фичи**: `kpi-dashboard`, `sales-analytics`, `demand-forecast`, `news-digest-chat`.

## User Flow
1. Пользователь открывает раздел закупок и маржи.
2. Выбирает продукт и период.
3. Система показывает совместный график закупочной и розничной цены, а также динамику маржи.
4. Пользователь просматривает список дней с низкой маржой и аномальными скачками закупки.
5. При необходимости использует данные раздела как контекст для прогноза и чата.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Loading | Данные загружаются | Skeleton chart и таблицы |
| Empty | Нет закупок или продаж в периоде | Placeholder с подсказкой |
| Ready | Всё рассчитано | Графики цен, маржа, журнал аномалий |
| Warning | Есть дни ниже порога | Highlight и warning badge |
| Error | Ошибка расчёта | Alert с retry |

## Ключевые компоненты

### `MarginAnalyticsPage`
- **Расположение**: `src/pages/MarginAnalyticsPage.tsx`
- **Поведение**: общий layout раздела и навигация между графиком и журналом аномалий.

### `PriceVsMarginChart`
- **Расположение**: `src/features/margin/components/PriceVsMarginChart.tsx`
- **Поведение**: совместная визуализация закупочной, розничной цены и маржи + indicator overlays и event bands.

### `LowMarginTable`
- **Расположение**: `src/features/margin/components/LowMarginTable.tsx`
- **Поведение**: список дней, где маржа ушла ниже бизнес-порога.

### `AnomalyJournal`
- **Расположение**: `src/features/margin/components/AnomalyJournal.tsx`
- **Поведение**: журнал “что случилось” с возможными причинами из внутренних метрик.

## API-контракты

### `GET /api/v1/analytics/margin`
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
    "product_code": "DT_S",
    "granularity": "day",
    "series": [
      {
        "period_start": "2026-03-01",
        "avg_purchase_price_rub": 52.1,
        "avg_retail_price_rub": 58.7,
        "gross_margin_rub": 4300.0,
        "gross_margin_rub_per_liter": 4.3,
        "gross_margin_pct": 7.3,
        "purchase_data_missing": false
      }
    ],
    "threshold_rub_per_liter": 3.0,
    "below_threshold_days": 4,
    "low_margin_days": [
      {
        "date": "2026-03-03",
        "gross_margin_rub_per_liter": 2.1,
        "purchase_data_missing": false
      }
    ]
  },
  "error": null,
  "meta": {
    "explainability": {
      "summary": {
        "title": "Маржинальный риск"
      },
      "chart": {
        "annotations": [],
        "overlays": [],
        "thresholds": [
          {
            "id": "margin-threshold-rub-per-liter",
            "label": "Порог маржи",
            "value": 3.0
          }
        ],
        "supporting_refs": []
      },
      "trust": {
        "data_freshness": "warning",
        "mode": "cached",
        "external_context": {
          "provider_mode": "manual_snapshot",
          "coverage_ratio": 0.82,
          "fallback_ratio": 0.64,
          "quality_status": "degraded",
          "reasons": ["coverage_ratio=0.820<0.85"],
          "manifest_run_date": "2026-03-05",
          "source_refs": []
        }
      },
      "state": {
        "status": "ready"
      }
    }
  }
}
```

### `GET /api/v1/analytics/anomalies`
- **Авторизация**: `admin`, `analyst`
- **Query Params**:
  - `metric=margin|purchase_price`
  - `product_code`
  - `date_from`
  - `date_to`

## Модель данных
- Новых таблиц не создаёт.
- Основные источники: `purchases_daily`, `sales_daily`.
- Расчёт опирается на производную витрину `vw_margin_daily`.

## Frontend-требования
- Порог маржи отображать в UI как справочное значение, а не редактируемую настройку `v1`.
- Дни ниже порога должны быть кликабельны и подсвечивать соответствующую точку на графике.
- Для аномальных событий предусмотреть колонку “возможные причины”.
- В отдельном блоке показывать quality/fallback состояние внешнего контекста.

## Backend-требования
- Корректно рассчитывать маржу даже при наличии нескольких закупок в один день через средневзвешенную закупочную цену.
- Возвращать дни без закупки с явным флагом `purchase_data_missing`, а не silently drop.
- Формировать `possible_reasons` из внутренних данных; news-интеграция остаётся контуром Phase 8.

## Edge Cases
- Есть продажи, но в этот день нет закупки.
- Закупочная цена выше розничной.
- Импорт закупок содержит выброс из-за ошибки в файле.
- История короткая и не позволяет устойчиво выделить тренд.

## Тестирование
- API: корректность расчёта маржи, negative margin, missing purchase data, anomalies.
- UI: подсветка дней ниже порога, переход из журнала к графику.
- E2E: пользователь находит аномально низкую маржу и видит возможные причины.
