# Feature: Demand Forecast

## Обзор
- **Назначение**: запускать прогноз спроса по продукту на горизонты `1`, `7` и `30` дней с доверительным интервалом, метриками качества и what-if сценарием по цене.
- **Пользователь**: `admin`, `sales`, `analyst`, `director`.
- **Точка входа**: `/forecast`.
- **Связанные фичи**: `sales-analytics`, `procurement-margin`, `news-digest-chat`.

## User Flow
1. Пользователь открывает страницу прогноза.
2. Выбирает продукт и горизонт прогноза.
3. По желанию включает сценарий `what-if` и задаёт изменение розничной цены в процентах.
4. Система вызывает прогнозный endpoint и отображает фактический ряд, прогноз, интервалы и драйверы.
5. Пользователь просматривает метрики последнего backtest.
6. Если модель недоступна, система показывает fallback baseline с предупреждением.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Default | Ещё не запускали прогноз | Фильтры и подсказки |
| Loading | Выполняется запрос | Spinner и disabled controls |
| ForecastReady | Базовый прогноз готов | График, таблица, драйверы |
| ScenarioReady | Рассчитан what-if | Сравнение base vs scenario |
| BaselineFallback | Нет активной модели | Warning и baseline result |
| InsufficientHistory | Истории не хватает | Сообщение и CTA на демо-данные |
| Error | Сервис недоступен | Alert и retry |

## Ключевые компоненты

### `ForecastPage`
- **Расположение**: `src/pages/ForecastPage.tsx`
- **Поведение**: layout страницы и координация запросов.

### `ForecastControlPanel`
- **Расположение**: `src/features/forecast/components/ForecastControlPanel.tsx`
- **Пропсы**: `{ productCode, horizonDays, scenarioEnabled }`
- **Поведение**: выбор продукта, горизонта и сценария.

### `ForecastChart`
- **Расположение**: `src/features/forecast/components/ForecastChart.tsx`
- **Поведение**: показывает `base vs scenario`, индикаторные overlays и event markers/bands на горизонте прогноза.

### `BacktestMetricsPanel`
- **Расположение**: `src/features/forecast/components/BacktestMetricsPanel.tsx`
- **Поведение**: отображает `MAE`, `RMSE`, `SMAPE`, тип окна и версию модели.

### `ForecastDriversPanel`
- **Расположение**: `src/features/forecast/components/ForecastDriversPanel.tsx`
- **Поведение**: простой текстовый блок с основными причинами прогноза.

## API-контракты

### `POST /api/v1/forecasts/run`
- **Авторизация**: `admin`, `sales`, `analyst`, `director`
- **Request Body**:
```json
{
  "product_code": "AI_95",
  "horizon_days": 7,
  "scenario": {
    "retail_price_delta_pct": 2.5
  }
}
```
- **Response 200**:
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
      "лаг спроса за 7 дней остаётся основным фактором",
      "рост цены снижает ожидаемый спрос умеренно"
    ],
    "external_context_quality": {
      "provider_mode": "cached",
      "coverage_ratio": 0.96,
      "fallback_ratio": 0.14,
      "quality_status": "warning",
      "reasons": ["fallback_ratio=0.140>0.10"],
      "manifest_run_date": "2026-04-09",
      "source_refs": []
    },
    "event_context": [
      {
        "event_code": "summer_logistics_tension",
        "title": "Летние логистические ограничения",
        "start_date": "2026-04-10",
        "end_date": "2026-04-12",
        "pressure_score": 0.35,
        "demand_delta_pct": -1.2,
        "purchase_delta_pct": 1.8,
        "source_mode": "db"
      }
    ],
    "reference_overlays": [
      {
        "code": "usd_rub",
        "label": "USD/RUB",
        "provider_mode": "cached",
        "points": [{"date": "2026-04-10", "value": 90.3}]
      }
    ]
  },
  "error": null,
  "meta": {}
}
```

### `GET /api/v1/forecasts/latest`
- **Авторизация**: `admin`, `sales`, `analyst`, `director`
- **Query Params**: `product_code`, `horizon_days`
- **Контракт latest (phase E)**:
  - `data.base_forecast_points` всегда содержит базовую серию;
  - `data.scenario_forecast_points` содержит сценарную серию, если она была рассчитана;
  - `data.forecast_points` остаётся совместимым полем (дублирует base в latest-контексте).
- **Поведение при пустой истории прогнозов**: `200`, `data=null`, `meta.empty_state`.

### `GET /api/v1/backtests/latest`
- **Авторизация**: `admin`, `sales`, `analyst`, `director`
- **Response 200**:
```json
{
  "data": {
    "product_code": "AI_95",
    "horizon_days": 7,
    "model_type": "catboost",
    "window_type": "rolling",
    "metrics": {
      "mae": 412.1,
      "rmse": 553.4,
      "smape": 4.8
    }
  },
  "error": null,
  "meta": {}
}
```
- **Поведение при отсутствии backtest**: `200`, `data=null`, `meta.empty_state`.

### `POST /api/v1/backtests/run`
- **Авторизация**: `admin`
- **Execution mode**: синхронный run (API ждёт завершения расчёта и сразу возвращает winner + metrics).

## Модель данных
- Использует `models`, `forecasts`, `backtest_runs`.
- Новых таблиц сверх ML-контура не создаёт.

## Frontend-требования
- Горизонты выбора жёстко ограничены `1`, `7`, `30`.
- Scenario mode активируется отдельным переключателем и должен визуально отличаться от базового прогноза.
- Интервалы прогноза и факт отображаются на одном графике.
- На графике присутствуют indicator lines + event markers/bands, legend/tooltips показывают режим источника и последнюю дату контекста.
- Драйверы выводятся человеческим языком, без названий сырого feature engineering.
- В отдельном блоке отображается `external_context_quality` (`quality_status`, `coverage`, `fallback`, `reasons`).

## Backend-требования
- Сохранять вызов прогноза в `forecasts`.
- При отсутствии активной модели возвращать baseline с флагом `model_status=baseline_fallback`.
- What-if меняет только сценарную копию расчёта, а не перезаписывает базовый прогноз.
- Метрики backtest возвращать из последнего успешного `backtest_runs`.
- `POST /forecasts/run` и `GET /forecasts/latest` возвращают `external_context_quality`, `event_context`, `reference_overlays`.

## Edge Cases
- Пользователь запрашивает горизонт, для которого нет активной модели.
- Истории слишком мало для генерации признаков.
- Scenario задаёт экстремальное изменение цены.
- Данные обновились после последнего backtest, а модель ещё не переобучена.

## Тестирование
- API: active model, baseline fallback, scenario request, insufficient history.
- UI: переключение горизонтов, scenario mode, отображение backtest metrics.
- E2E: запуск прогноза на 7 дней и просмотр объяснений.
