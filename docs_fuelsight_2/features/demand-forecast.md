# Feature: Demand Forecast v2

## Обзор
- Назначение: запускать base/scenario forecast с CatBoost-first логикой и прозрачным качеством модели.
- Точка входа: `/forecast`
- Пользователь: `admin`, `analyst`
- Owners:
  - frontend: control panel, dual forecast chart, model health panels
  - backend/ml: forecast, backtest, freshness, comparison, feature sources

## Ключевые изменения v2
- CatBoost описывается как primary path;
- Seasonal Naive показывается только как benchmark baseline;
- UI показывает base и scenario рядом;
- метрики включают freshness, training window, retrain status и baseline comparison.

## API Requirements
- `POST /api/v1/forecasts/run` и `GET /api/v1/forecasts/latest` возвращают:
  - `model_freshness`
  - `training_window`
  - `baseline_comparison`
  - `feature_sources`
  - `retrain_status`
- Для `GET /api/v1/forecasts/latest` используется единый pair-контракт:
  - `base_forecast_points` (обязательная базовая серия);
  - `scenario_forecast_points` (опциональная сценарная серия);
  - `forecast_points` сохраняется для backward compatibility и повторяет base-серию.
- `GET /api/v1/backtests/latest` возвращает те же health fields для последнего winner run.

## UX Rules
- fallback не должен выглядеть как "нормальный основной режим";
- scenario visually differs from base;
- business drivers формулируются человеческим языком;
- analyst видит качество модели без необходимости запускать admin backtest.

## Tests
- base/scenario rendering;
- baseline comparison panel;
- stale model badge;
- insufficient history state.
