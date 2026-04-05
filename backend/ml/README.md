# ML Module

ML контур используется в core MVP и pipeline Phase 7.

## Реализовано
- `features/`: подготовка признаков (лаги, rolling stats, календарь, ценовые признаки)
- `models/`: `Seasonal Naive` + `CatBoost`
- `backtesting/`: rolling/expanding backtest, метрики `MAE/RMSE/SMAPE`
- `inference/`: on-demand forecast path и интервалы

## Интеграция с backend
- `app/services/forecast_service.py` использует `ml/*` для `forecasts/backtests` API.
- Артефакты/метрики пишутся в `MODEL_ARTIFACTS_DIR`.

## Интеграция с Airflow
- `train_models_weekly` и `build_feature_store_daily` вызывают этот модуль через `app/pipeline/tasks.py`.

## Локальные команды
```bash
cd backend
uv run pytest
uv run fuelsight-pipeline train-models-weekly --window-type rolling
uv run fuelsight-pipeline build-feature-store-daily
```
