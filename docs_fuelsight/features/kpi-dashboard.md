# Feature: KPI Dashboard

## Обзор
- **Назначение**: дать пользователю быстрый обзор текущих продаж, выручки, маржи и активных алертов после входа в систему.
- **Пользователь**: `admin`, `analyst`.
- **Точка входа**: `/dashboard`.
- **Связанные фичи**: `auth`, `data-import`, `sales-analytics`, `procurement-margin`, `demand-forecast`.

## User Flow
1. Пользователь входит в систему и попадает на `/dashboard`.
2. Видит карточки KPI за выбранный период.
3. Просматривает блок алертов по марже и аномалиям.
4. Из KPI или алерта переходит в детальный аналитический раздел.
5. При отсутствии данных получает предложение загрузить файлы или сгенерировать демо-набор.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Loading | Идёт запрос KPI | Skeleton cards и placeholder графика |
| Empty | Данных нет | CTA на `/import` |
| Ready | Данные доступны | KPI cards, мини-график, алерты |
| Warning | Есть проблемные зоны | Warning badge, список алертов |
| Error | API недоступен | Alert и кнопка retry |

## Ключевые компоненты

### `DashboardPage`
- **Расположение**: `src/pages/DashboardPage.tsx`
- **Поведение**: общая сборка карточек, мини-графиков и алертов.

### `KpiSummaryCards`
- **Расположение**: `src/features/kpi/components/KpiSummaryCards.tsx`
- **Пропсы**: `{ summary: KpiSummary }`
- **Поведение**: показывает `sales_volume_liters`, `revenue_rub`, `gross_margin_rub`, `gross_margin_pct`.

### `AlertFeed`
- **Расположение**: `src/features/kpi/components/AlertFeed.tsx`
- **Поведение**: компактный список низкой маржи и аномалий с переходом в детали.

### `DemandSnapshotChart`
- **Расположение**: `src/features/kpi/components/DemandSnapshotChart.tsx`
- **Поведение**: краткий график продаж за последние 14-30 дней.

## API-контракты

### `GET /api/v1/kpi/summary`
- **Авторизация**: `admin`, `analyst`
- **Query Params**:
  - `date_from`
  - `date_to`
  - `product_code` optional
- **Response 200**:
```json
{
  "data": {
    "sales_volume_liters": 152340.0,
    "revenue_rub": 8876500.45,
    "gross_margin_rub": 925340.11,
    "gross_margin_pct": 10.43,
    "low_margin_days": 3,
    "anomaly_count": 2
  },
  "error": null,
  "meta": {
    "explainability": {
      "summary": {
        "title": "Итог периода"
      },
      "chart": {
        "annotations": [],
        "overlays": [],
        "thresholds": [],
        "supporting_refs": []
      },
      "trust": {
        "data_freshness": "fresh",
        "mode": "cached"
      },
      "state": {
        "status": "ready"
      }
    },
    "margin_coverage_days": 24,
    "margin_missing_days": 6
  }
}
```

### `GET /api/v1/kpi/alerts`
- **Авторизация**: `admin`, `analyst`
- **Query params**: `severity`, `date_from`, `date_to`, `product_code` optional
- **Response 200**:
```json
{
  "data": [
    {
      "type": "low_margin",
      "severity": "high",
      "date": "2026-03-20",
      "product_code": "AI_92",
      "message": "Маржа опустилась ниже порога 3 руб/л"
    }
  ],
  "error": null,
  "meta": {}
}
```

### `GET /api/v1/kpi/snapshot`
- **Авторизация**: `admin`, `analyst`
- **Query params**:
  - `date_from`
  - `date_to`
  - `product_code` optional
- **Response 200**:
```json
{
  "data": [
    {
      "date": "2026-03-28",
      "volume_liters": 12450.0,
      "avg_retail_price_rub": 59.8
    }
  ],
  "error": null,
  "meta": {
    "explainability": {
      "summary": null,
      "chart": {
        "annotations": [],
        "overlays": [],
        "thresholds": [],
        "supporting_refs": []
      },
      "trust": {
        "data_freshness": "warning",
        "mode": "cached"
      },
      "state": {
        "status": "ready"
      }
    },
    "points": 30
  }
}
```

## Модель данных
- Новых таблиц не создаёт.
- Использует агрегаты из `sales_daily`, `purchases_daily` и производной витрины `vw_margin_daily`.

## Frontend-требования
- Период по умолчанию: последние 30 дней.
- Все суммы и проценты форматируются локализованно.
- Карточка KPI должна быть кликабельной только если для неё существует детальный сценарий перехода.
- При пустых данных CTA ведёт на `/import`.

## Backend-требования
- KPI должны считаться быстро и кешироваться на короткий TTL.
- Алерты строятся на базе правил:
  - маржа ниже порога;
  - аномальный скачок закупочной цены;
  - z-score аномалия спроса.
- При недостатке данных backend возвращает `data: null` и понятное описание empty-state в `meta`.

## Edge Cases
- Данные есть только по одному продукту.
- Есть продажи, но нет закупок за часть периода.
- Алертов нет вообще.
- Пользователь меняет период на диапазон вне доступной истории.

## Тестирование
- API: расчёт KPI на фиксированном наборе данных.
- UI: empty state, warning state, переход из алерта в аналитику.
- E2E: после импорта пользователь видит обновлённые KPI без ручного refresh страницы.
