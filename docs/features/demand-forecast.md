# Feature: Demand Forecast

## Обзор
- **Назначение**: запускать прогноз спроса по продукту на горизонты `1`, `7` и `30` дней с доверительным интервалом, блоком качества модели и what-if сценарием по цене.
- **Пользователь**: `admin`, `sales`, `analyst`, `director`.
- **Точка входа**: `/forecast`.
- **Связанные фичи**: `sales-analytics`, `procurement-margin`, `news-digest-chat`.

## User Flow
1. Пользователь открывает страницу прогноза.
2. Выбирает продукт и горизонт прогноза.
3. По желанию включает сценарий `what-if` и задаёт изменение розничной цены в процентах.
4. Система вызывает прогнозный endpoint и отображает фактический ряд, прогноз, интервалы и драйверы.
5. Пользователь просматривает блок `Качество модели` по последнему backtest: статус, периоды, график тестового периода, метрики и сравнение с baseline.
6. Если модель недоступна, система показывает fallback baseline с предупреждением.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Default | Ещё не запускали прогноз | Фильтры и подсказки |
| Loading | Выполняется запрос | Spinner и disabled controls |
| ForecastReady | Базовый прогноз готов | График, таблица, драйверы |
| ScenarioReady | Рассчитан what-if | Сравнение base vs scenario |
| BaselineFallback | Нет активной модели | Warning и baseline result |
| ValidationUnknown | Нет validation evidence | Статус `UNKNOWN`, controlled fallback без графика и метрик |
| ValidationLimited | Evidence неполное или CatBoost не лучше baseline | Статус `LIMITED`, причина ограничения, доступные периоды/метрики/график |
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

### `ValidationEvidencePanel`
- **Расположение**: `src/features/forecast/components/ValidationEvidencePanel.tsx`
- **Поведение**: компактный блок `Качество модели` внутри области `Качество и надёжность`.
- **Источник данных**: `validation_summary` из последнего backtest; это опциональное поле существующего backtest payload, а не отдельный endpoint.
- **Содержимое**:
  - детерминированный статус `OK`, `LIMITED` или `UNKNOWN`;
  - короткая причина статуса на русском языке;
  - период обучения, тестовый период и число наблюдений, если доступны;
  - график тестового периода `факт vs CatBoost vs Seasonal Naive`;
  - таблица `MAE`, `RMSE`, `SMAPE` для CatBoost и Seasonal Naive;
  - улучшение CatBoost относительно Seasonal Naive, в первую очередь по `SMAPE`;
  - дисклеймер: прогноз является аналитической оценкой и не гарантирует точное значение будущего спроса или цены.

### `ForecastDriversPanel`
- **Расположение**: `src/features/forecast/components/ForecastDriversPanel.tsx`
- **Поведение**: простой текстовый блок с основными причинами прогноза.

## Качество модели для защиты
Качество прогноза в системе подтверждается не только значениями метрик, но и
отложенной временной проверкой. Исторический ряд разделяется по времени: модель
обучается на более раннем периоде, после чего её прогноз сравнивается с
фактическими значениями на тестовом периоде. Для интерпретации результата
CatBoost сопоставляется с простым сезонным ориентиром Seasonal Naive. В
интерфейсе это представлено через график `факт vs CatBoost vs Seasonal Naive`,
таблицу `MAE`/`RMSE`/`SMAPE` и показатель улучшения относительно baseline.
Такой подход не гарантирует абсолютную точность будущего прогноза, но
показывает, что модель проверялась на данных, не использованных для обучения,
и что её качество можно сопоставить с понятным базовым методом.

Статусы блока не являются строгим научным доказательством репрезентативности:
- `OK` означает, что CatBoost проверен на тестовом периоде и не хуже Seasonal Naive по `SMAPE`.
- `LIMITED` означает, что evidence есть, но оно неполное, тестовый период слишком короткий, отдельные метрики/ряд недоступны или CatBoost хуже Seasonal Naive по `SMAPE`.
- `UNKNOWN` означает, что validation evidence недоступно; экран показывает controlled fallback вместо недостоверного вывода.

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
    },
    "validation_summary": {
      "status": "LIMITED",
      "status_reason": "Backtest metrics are available, but dated test-period series is not persisted yet.",
      "train_period": {"start": "2025-01-01", "end": "2025-12-31"},
      "test_period": null,
      "observations": {"total": null, "train": null, "test": 40},
      "metrics": {
        "catboost": {"mae": 412.1, "rmse": 553.4, "smape": 4.8},
        "seasonal_naive": {"mae": 520.0, "rmse": 690.0, "smape": 6.2},
        "improvement": {"mae_pct": 20.75, "rmse_pct": 19.8, "smape_pct": 22.58}
      },
      "series": []
    }
  },
  "error": null,
  "meta": {}
}
```
- **`validation_summary`**: опциональное расширение payload последнего backtest. Старые или пустые backtest состояния остаются валидными без этого поля.
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
- В области `Качество и надёжность` отображается `Качество модели` с `validation_summary`.
- Для `admin` в `Качество модели` может быть доступен компактный accordion с техническими деталями backtest; остальные forecast-read роли видят core evidence.

## Backend-требования
- Сохранять вызов прогноза в `forecasts`.
- При отсутствии активной модели возвращать baseline с флагом `model_status=baseline_fallback`.
- What-if меняет только сценарную копию расчёта, а не перезаписывает базовый прогноз.
- Метрики backtest возвращать из последнего успешного `backtest_runs`.
- `validation_summary` хранится и возвращается как часть существующего backtest payload; отдельный endpoint не вводится.
- `POST /forecasts/run` и `GET /forecasts/latest` возвращают `external_context_quality`, `event_context`, `reference_overlays`.

## Edge Cases
- Пользователь запрашивает горизонт, для которого нет активной модели.
- Истории слишком мало для генерации признаков.
- Scenario задаёт экстремальное изменение цены.
- Данные обновились после последнего backtest, а модель ещё не переобучена.
- Последний backtest есть, но `validation_summary` отсутствует: UI показывает `UNKNOWN` или limited legacy summary без заявления о точности.
- `validation_summary.series` пустой: метрики могут отображаться, но график тестового периода заменяется controlled fallback сообщением.

## Тестирование
- API: active model, baseline fallback, scenario request, insufficient history.
- UI: переключение горизонтов, scenario mode, отображение backtest metrics и `Качество модели`.
- E2E: запуск прогноза на 7 дней и просмотр объяснений.
