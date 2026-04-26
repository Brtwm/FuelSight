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
- Коды продуктов: `AI_92`, `AI_95`, `DT_S`, `DT_W`.
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
- Response `200`:
```json
{
  "data": {
    "access_token": "jwt",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "error": null,
  "meta": {}
}
```
- Response `401`: refresh token недействителен или отсутствует (`error.code=invalid_refresh_token`).

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
- Для demo-chain используется rolling окно до текущей даты; пример ниже соответствует подтверждённому smoke-срезу `2026-04-25`.
- Request:
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
  "meta": {
    "margin_coverage_days": 24,
    "margin_missing_days": 6
  }
}
```

### `GET /api/v1/kpi/alerts`
- Назначение: список активных предупреждений.
- Доступ: `admin`, `analyst`.
- Query params: `severity`, `date_from`, `date_to`, `product_code`.
- Правила алертов:
  - `low_margin` (`gross_margin_rub_per_liter` ниже порога);
  - `purchase_spike` (резкий рост средневзвешенной закупочной цены day-over-day);
  - `demand_anomaly` (z-score аномалия спроса).

### `GET /api/v1/kpi/snapshot`
- Назначение: короткий ряд для мини-графика на dashboard (спрос + средняя розничная цена).
- Доступ: `admin`, `analyst`.
- Query params:
  - `date_from`
  - `date_to`
  - `product_code` optional
- Response `200`:
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
    "points": 30
  }
}
```
- Phase D contract:
  - `meta.explainability.trust.external_context` обязателен в explainability payload и включает:
    - `provider_mode`, `coverage_ratio`, `fallback_ratio`, `quality_status`, `reasons`, `manifest_run_date`, `source_refs`.
  - `meta.explainability.chart.overlays` может содержать event overlays (`code` вида `event:*`) для marker/band визуализации.

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
  - `series`: массив точек с `period_start`, `volume_liters`, `avg_retail_price_rub`;
  - `seasonality`: агрегаты по дням недели и месяцам;
  - `comparisons`: `mom_pct`, `yoy_pct` (или `null`, если истории недостаточно).
  - `meta.explainability.trust.external_context`: quality/fallback блок внешнего контекста.
  - `meta.explainability.chart.overlays`: indicator lines + event overlays (`event:*`) для explainable narrative.

### `GET /api/v1/analytics/margin`
- Назначение: динамика закупочной, розничной цены и валовой маржи.
- Доступ: `admin`, `analyst`.
- Query params:
  - `product_code` required
  - `date_from`
  - `date_to`
  - `granularity=day|week|month`
- Response содержит:
  - `series`: точки с `period_start`, ценами и маржой;
  - `threshold_rub_per_liter`;
  - `below_threshold_days`;
  - `low_margin_days`.
  - `meta.explainability.trust.external_context`: quality/fallback блок внешнего контекста.
  - `meta.explainability.chart.overlays`: indicator lines + event overlays (`event:*`) для explainable narrative.

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
      "product_code": "DT_W",
      "metric": "margin",
      "severity": "high",
      "actual_value": 1.34,
      "expected_range": [3.4, 5.1],
      "possible_reasons": [
        "рост закупочной цены",
        "запаздывание розничной цены"
      ],
      "target_path": "/analytics/margin"
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
    "scenario_name": "base",
    "scenario_params": null,
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
- Phase D additions (`data`):
  - `external_context_quality`: quality/fallback блок (`provider_mode`, `coverage_ratio`, `fallback_ratio`, `quality_status`, `reasons`, `manifest_run_date`, `source_refs`);
  - `event_context`: curated event windows для forecast horizon;
  - `reference_overlays`: indicator overlays для forecast chart.

### `GET /api/v1/forecasts/latest`
- Назначение: получить последнюю сохранённую серию прогноза.
- Доступ: `admin`, `analyst`.
- Query params: `product_code`, `horizon_days`.
- Pair-ready контракт:
  - `base_forecast_points` — базовая серия;
  - `scenario_forecast_points` — сценарная серия при наличии;
  - `forecast_points` — совместимый alias базовой серии.
- Если прогнозы ещё не запускались: `200` + `data=null` и `meta.empty_state`.
- Если прогноз найден, `data` также содержит `external_context_quality`, `event_context`, `reference_overlays`.

## Backtests

### `GET /api/v1/backtests/latest`
- Назначение: метрики последнего backtest по продукту и горизонту.
- Доступ: `admin`, `analyst`.
- Query params: `product_code`, `horizon_days`.
- Если backtest ещё не запускался: `200` + `data=null` и `meta.empty_state`.

### `POST /api/v1/backtests/run`
- Назначение: ручной запуск backtest/retraining.
- Доступ: `admin`.
- Request:
```json
{
  "product_code": "DT_S",
  "horizon_days": 30,
  "window_type": "rolling"
}
```
- Response `200`:
```json
{
  "data": {
    "product_code": "DT_S",
    "horizon_days": 30,
    "model_type": "catboost",
    "window_type": "rolling",
    "metrics": {
      "mae": 512.4,
      "rmse": 688.7,
      "smape": 5.3
    },
    "comparison": {
      "seasonal_naive": {
        "mae": 640.1,
        "rmse": 812.4,
        "smape": 6.9
      },
      "catboost": {
        "mae": 512.4,
        "rmse": 688.7,
        "smape": 5.3
      }
    },
    "trained_at": "2026-04-04T21:20:00+00:00",
    "model_version": "20260404212000"
  },
  "error": null,
  "meta": {
    "folds": 8
  }
}
```

## News

News runtime использует real-provider baseline: `GDELT` + curated RSS/API providers (`RBC`, `Kommersant`, `Prime`) с cache/manual snapshot fallback. Fixture ingest не является runtime-источником.

### `GET /api/v1/news/digests/latest`
- Назначение: последняя дневная или недельная сводка.
- Доступ: `admin`, `analyst`.
- Query params: `period_type=daily|weekly`.
- Phase D additions (`data`):
  - `provider_mode`, `news_freshness`;
  - `context_story` c полями:
    - `window`,
    - `external_context`,
    - `event_context`,
    - `indicator_refs`,
    - `event_refs`.

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
