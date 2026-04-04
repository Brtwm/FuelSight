# Active Context

## Current State
- Фаза 6 реализована: backend `forecast/backtests` + базовый ML-контур и frontend `/forecast` больше не являются заглушками.
- Backend поддерживает `/api/v1/forecasts/run|latest` и `/api/v1/backtests/run|latest` с envelope-контрактом и role guards.
- Frontend страница прогноза использует URL-синхронизированные фильтры, сценарный `what-if`, график интервалов, панель метрик backtest и драйверы.

## Recently Completed
- Добавлены SQLAlchemy-модели и Alembic migration `20260404_0003` для `models`, `forecasts`, `backtest_runs`.
- Реализован ML contour:
  - `Seasonal Naive` baseline;
  - `CatBoostRegressor` с артефактами в `MODEL_ARTIFACTS_DIR`;
  - rolling/expanding backtest с метриками `MAE/RMSE/SMAPE`;
  - выбор winner по `SMAPE` (tie-break `RMSE`) и активация модели.
- Реализован `ForecastService`:
  - fallback `model_status=baseline_fallback`, если нет активной модели;
  - сценарий `retail_price_delta_pct` только на горизонте прогноза;
  - сохранение прогнозных точек и отчётов backtest.
- Реализован frontend vertical slice прогноза:
  - `ForecastPage`, `ForecastControlPanel`, `ForecastChart`, `BacktestMetricsPanel`, `ForecastDriversPanel`;
  - отдельный API client `frontend/src/lib/api/forecast.ts`;
  - URL helper `frontend/src/features/forecast/urlFilters.ts`.

## Current Focus
- Переход к Фазе 7: Airflow operationalization и reproducible local demo-run.

## Active Decisions
- `ENABLE_LLM=false` по умолчанию.
- MVP остаётся single-station (`v1` без `stations`).
- Порог low-margin фиксирован в backend config (`kpi_low_margin_threshold_rub_per_liter=3.0`) и read-only для UI.
- `POST /api/v1/backtests/run` выполняется синхронно в API (без job queue на фазе 6).
- `GET /api/v1/forecasts/latest` и `GET /api/v1/backtests/latest` возвращают `200 + data=null`, если данных ещё нет.
- Продуктовые коды в активной реализации: `AI_92`, `AI_95`, `DT_S`, `DT_W`.

## Risks To Remember
- Для production-like окружения нужен JWT secret длиной >= 32 символов (dev secret остаётся демонстрационным).
- KPI cache сейчас in-memory в процессе FastAPI; при горизонтальном масштабировании понадобится внешний cache слой.
- Импорт всё ещё работает через background tasks FastAPI-процесса; для heavy-job operationalization нужен вынос в очередь/DAG.
- Bundle size frontend остаётся выше warning-порога; для оптимизации нужен этап code-splitting.
