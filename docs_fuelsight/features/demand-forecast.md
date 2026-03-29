# Feature: Demand Forecast

## Обзор
- **Назначение**: запускать прогноз спроса по продукту на горизонты `1`, `7` и `30` дней с доверительным интервалом, метриками качества и what-if сценарием по цене.
- **Пользователь**: `admin`, `analyst`.
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
- **Поведение**: показывает фактический ряд, прогноз и доверительный интервал.

### `BacktestMetricsPanel`
- **Расположение**: `src/features/forecast/components/BacktestMetricsPanel.tsx`
- **Поведение**: отображает `MAE`, `RMSE`, `SMAPE`, тип окна и версию модели.

### `ForecastDriversPanel`
- **Расположение**: `src/features/forecast/components/ForecastDriversPanel.tsx`
- **Поведение**: простой текстовый блок с основными причинами прогноза.

## API-контракты

### `POST /api/v1/forecasts/run`
- **Авторизация**: `admin`, `analyst`
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
    ]
  },
  "error": null,
  "meta": {}
}
```

### `GET /api/v1/forecasts/latest`
- **Авторизация**: `admin`, `analyst`
- **Query Params**: `product_code`, `horizon_days`

### `GET /api/v1/backtests/latest`
- **Авторизация**: `admin`, `analyst`
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

## Модель данных
- Использует `models`, `forecasts`, `backtest_runs`.
- Новых таблиц сверх ML-контура не создаёт.

## Frontend-требования
- Горизонты выбора жёстко ограничены `1`, `7`, `30`.
- Scenario mode активируется отдельным переключателем и должен визуально отличаться от базового прогноза.
- Интервалы прогноза и факт отображаются на одном графике.
- Драйверы выводятся человеческим языком, без названий сырого feature engineering.

## Backend-требования
- Сохранять вызов прогноза в `forecasts`.
- При отсутствии активной модели возвращать baseline с флагом `model_status=baseline_fallback`.
- What-if меняет только сценарную копию расчёта, а не перезаписывает базовый прогноз.
- Метрики backtest возвращать из последнего успешного `backtest_runs`.

## Edge Cases
- Пользователь запрашивает горизонт, для которого нет активной модели.
- Истории слишком мало для генерации признаков.
- Scenario задаёт экстремальное изменение цены.
- Данные обновились после последнего backtest, а модель ещё не переобучена.

## Тестирование
- API: active model, baseline fallback, scenario request, insufficient history.
- UI: переключение горизонтов, scenario mode, отображение backtest metrics.
- E2E: запуск прогноза на 7 дней и просмотр объяснений.
