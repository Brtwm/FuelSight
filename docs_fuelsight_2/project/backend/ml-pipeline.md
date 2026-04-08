# FuelSight v2 ML And Pipeline Design

## Цель
Сделать CatBoost основным и управляемым прогнозным контуром, а не "дополнительной моделью рядом с baseline".

## Model Hierarchy
- Primary:
  - `CatBoostRegressor` per `product x horizon`
- Benchmark:
  - `Seasonal Naive`
- Decision rule:
  - CatBoost preferred by default;
  - если CatBoost quality/regime gate провален, UI и API обязаны явно показать degraded status и benchmark comparison.

## Feature Groups v2
- lag features
- rolling statistics
- calendar flags
- price dynamics
- margin features
- external indicators
- event pressure features
- cross-product context features

## Training Strategy
### Daily
- refresh external indicators;
- refresh feature store;
- recompute freshness/status artifacts.

### Weekly
- run rolling backtests for `1/7/30`;
- retrain active CatBoost models;
- persist winner metrics and baseline comparison.

### Less frequent
- hyperparameter retuning on wider history window;
- refresh event catalog and calibration constants for generator.

## Backtesting
- modes:
  - `rolling`
  - `expanding`
- outputs:
  - `MAE`
  - `RMSE`
  - `SMAPE`
  - winner vs baseline
  - residual statistics
  - training window
  - feature sources used

## Freshness
- Fresh:
  - retrained within expected cadence and data coverage complete.
- Warning:
  - model older than target cadence or indicators partly cached.
- Degraded:
  - external context stale, model missing, or fallback path used.

## Airflow Tasks v2
- `ingest_internal_sales_daily`
- `ingest_internal_purchases_daily`
- `ingest_external_indicators_daily`
- `build_feature_store_daily`
- `train_models_weekly`
- `refresh_news_daily`
- `build_defense_report`

## Artifacts
- feature store snapshots
- active model artifacts
- backtest reports
- freshness/status manifests
- defense report JSON
