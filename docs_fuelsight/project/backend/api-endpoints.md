# FuelSight API Endpoints

## Общие соглашения
- Base URL: `/api/v1`
- Response envelope:
```json
{
  "data": {},
  "error": null,
  "meta": {
    "request_id": "uuid"
  }
}
```
- Все даты передаются в формате `YYYY-MM-DD`.
- Коды продуктов: `AI_92`, `AI_95`, `DT`.
- Для защищённых маршрутов используется bearer access token.

## Auth

### `POST /api/v1/auth/login`
- Назначение: аутентификация пользователя.
- Доступ: public.
- Request:
```json
{
  "email": "analyst@fuelsight.local",
  "password": "string"
}
```
- Response `200`:
```json
{
  "data": {
    "access_token": "jwt",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "email": "analyst@fuelsight.local",
      "role": "analyst",
      "display_name": "Price Analyst"
    }
  },
  "error": null,
  "meta": {}
}
```
- Дополнительно: refresh token выставляется в `HttpOnly` cookie.

### `POST /api/v1/auth/refresh`
- Назначение: выпуск нового access token.
- Доступ: public with refresh cookie.
- Response `200`: новый `access_token`.

### `GET /api/v1/auth/me`
- Назначение: профиль текущего пользователя.
- Доступ: `admin`, `analyst`.

### `POST /api/v1/auth/logout`
- Назначение: завершение сессии и очистка refresh cookie.
- Доступ: `admin`, `analyst`.

## Import

### `POST /api/v1/import/sales`
- Назначение: загрузка файла продаж.
- Доступ: `admin`.
- Content-Type: `multipart/form-data`.
- Поля:
  - `file`: CSV/XLSX.
  - `source_name`: строка, опционально.
- Response `202`:
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
- Назначение: загрузка файла закупок.
- Доступ: `admin`.
- Формат аналогичен загрузке продаж.

### `POST /api/v1/import/generate-demo`
- Назначение: генерация учебных продаж и закупок.
- Доступ: `admin`.
- Request:
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
- Назначение: история импортов.
- Доступ: `admin`.
- Query params: `entity_type`, `status`, `limit`.

### `GET /api/v1/import/jobs/{job_id}`
- Назначение: детальный статус импорта.
- Доступ: `admin`.

## KPI

### `GET /api/v1/kpi/summary`
- Назначение: главные KPI для dashboard.
- Доступ: `admin`, `analyst`.
- Query params:
  - `date_from`
  - `date_to`
  - `product_code` optional
- Response `200`:
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
  "meta": {}
}
```

### `GET /api/v1/kpi/alerts`
- Назначение: список активных предупреждений.
- Доступ: `admin`, `analyst`.
- Query params: `severity`, `date_from`, `date_to`.

## Analytics

### `GET /api/v1/analytics/sales`
- Назначение: временной ряд продаж и спроса.
- Доступ: `admin`, `analyst`.
- Query params:
  - `product_code` required
  - `date_from`
  - `date_to`
  - `granularity=day|week|month`
- Response содержит:
  - `series`: массив точек спроса;
  - `price_overlay`: средняя розничная цена;
  - `seasonality`: агрегаты по дням недели и месяцам;
  - `comparisons`: `mom`, `yoy` when available.

### `GET /api/v1/analytics/margin`
- Назначение: динамика закупочной, розничной цены и валовой маржи.
- Доступ: `admin`, `analyst`.
- Query params: `product_code`, `date_from`, `date_to`.

### `GET /api/v1/analytics/anomalies`
- Назначение: аномалии по продажам или марже.
- Доступ: `admin`, `analyst`.
- Query params:
  - `metric=sales|margin|purchase_price`
  - `product_code`
  - `date_from`
  - `date_to`
- Response:
```json
{
  "data": [
    {
      "date": "2025-11-05",
      "product_code": "DT",
      "metric": "margin",
      "severity": "high",
      "actual_value": 1.34,
      "expected_range": [3.4, 5.1],
      "possible_reasons": [
        "рост закупочной цены",
        "запаздывание розничной цены"
      ]
    }
  ],
  "error": null,
  "meta": {}
}
```

## Forecasts

### `POST /api/v1/forecasts/run`
- Назначение: on-demand прогноз по продукту.
- Доступ: `admin`, `analyst`.
- Request:
```json
{
  "product_code": "AI_95",
  "horizon_days": 7,
  "scenario": {
    "retail_price_delta_pct": 2.5
  }
}
```
- Response `200`:
```json
{
  "data": {
    "product_code": "AI_95",
    "horizon_days": 7,
    "model_type": "catboost",
    "model_status": "active",
    "forecast_points": [
      {
        "target_date": "2026-03-29",
        "y_hat": 12450.3,
        "y_lo": 11890.0,
        "y_hi": 13010.2
      }
    ],
    "drivers": [
      "спрос прошлой недели остаётся основным фактором",
      "ожидаемое повышение цены умеренно снижает объём"
    ]
  },
  "error": null,
  "meta": {}
}
```

### `GET /api/v1/forecasts/latest`
- Назначение: получить последнюю сохранённую серию прогноза.
- Доступ: `admin`, `analyst`.
- Query params: `product_code`, `horizon_days`.

## Backtests

### `GET /api/v1/backtests/latest`
- Назначение: метрики последнего backtest по продукту и горизонту.
- Доступ: `admin`, `analyst`.
- Query params: `product_code`, `horizon_days`.

### `POST /api/v1/backtests/run`
- Назначение: ручной запуск backtest/retraining.
- Доступ: `admin`.
- Request:
```json
{
  "product_code": "DT",
  "horizon_days": 30,
  "window_type": "rolling"
}
```

## News

### `GET /api/v1/news/digests/latest`
- Назначение: последняя дневная или недельная сводка.
- Доступ: `admin`, `analyst`.
- Query params: `period_type=daily|weekly`.

### `GET /api/v1/news/search`
- Назначение: поиск по новостным материалам.
- Доступ: `admin`, `analyst`.
- Query params: `q`, `date_from`, `date_to`, `topic`.

### `POST /api/v1/news/refresh`
- Назначение: принудительное обновление новостей и digest.
- Доступ: `admin`.

## Chat

### `POST /api/v1/chat/sessions`
- Назначение: создать новую диалоговую сессию.
- Доступ: `admin`, `analyst`.
- Request:
```json
{
  "title": "Рост закупочных цен за 14 дней"
}
```

### `GET /api/v1/chat/sessions/{session_id}/messages`
- Назначение: история сообщений.
- Доступ: `admin`, `analyst`.

### `POST /api/v1/chat/sessions/{session_id}/messages`
- Назначение: задать вопрос к данным и новостям.
- Доступ: `admin`, `analyst`.
- Request:
```json
{
  "question": "Почему в феврале упали продажи ДТ?",
  "context_scope": ["internal_analytics", "news_digest"]
}
```
- Response `200`:
```json
{
  "data": {
    "answer": "Снижение спроса по ДТ в феврале связано с сезонным спадом и ростом закупочной цены.",
    "citations": [
      {
        "type": "news",
        "ref_id": "news_2026_03_01_15",
        "title": "Новость о логистических ограничениях"
      },
      {
        "type": "chart",
        "ref_id": "analytics_margin_dt_2026_02",
        "title": "Динамика маржи ДТ"
      }
    ],
    "mode": "llm"
  },
  "error": null,
  "meta": {}
}
```

## Ошибки и коды
- Для framework-level ошибок backend возвращает:
  - `error.code=validation_error` для `422`;
  - `error.code=http_error` для `4xx`/`5xx` HTTP-исключений;
  - `error.code=internal_error` для непойманных исключений.
- `400`: бизнес-правило нарушено, например несовместимый сценарий.
- `401`: пользователь не аутентифицирован.
- `403`: недостаточно прав.
- `404`: сущность не найдена.
- `409`: конфликт импорта или попытка создать дублирующий job.
- `422`: ошибка схемы, формата файла или query-параметров.
- `503`: LLM-контур отключён либо недоступен, при этом news search и базовые digest могут продолжать работать.
