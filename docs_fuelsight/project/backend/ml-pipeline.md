# FuelSight ML and Pipeline Design

## Цели ML-контура
- Прогноз спроса по каждому виду топлива на горизонтах `1`, `7`, `30` дней.
- Показ объяснимого результата: прогноз, интервалы, метрики `MAE/RMSE/SMAPE`, драйверы.
- Полная воспроизводимость demo-сценария на локальной машине.

## Реализованный ML-контур
- Базовая модель: `Seasonal Naive`.
- Основная модель: `CatBoostRegressor`.
- Backtest: `rolling/expanding`, winner по `SMAPE` (tie-break `RMSE`).
- Артефакты и отчёты сохраняются в `MODEL_ARTIFACTS_DIR`.
- API-эндпоинты:
  - `POST /api/v1/forecasts/run`
  - `GET /api/v1/forecasts/latest`
  - `POST /api/v1/backtests/run`
  - `GET /api/v1/backtests/latest`

## Pipeline task-layer (Phase 7)
Общий task-layer вынесен в `backend/app/pipeline/tasks.py` и вызывается:
- из Airflow DAG-ов;
- из CLI `fuelsight-pipeline`;
- из smoke/demo scripts.

Доступные операции:
- `ingest_internal_sales_daily`
- `ingest_internal_purchases_daily`
- `build_feature_store_daily`
- `train_models_weekly`
- `ingest_external_indicators_daily`
- `generate_demo_data`
- `refresh_news_daily`

## CLI контракт
Запуск через backend environment:
```bash
cd backend
uv run fuelsight-pipeline ingest-sales-daily
uv run fuelsight-pipeline ingest-purchases-daily
uv run fuelsight-pipeline build-feature-store-daily
uv run fuelsight-pipeline train-models-weekly --window-type rolling
uv run fuelsight-pipeline ingest-external-indicators-daily --provider auto
uv run fuelsight-pipeline generate-demo-data --replace-existing
uv run fuelsight-pipeline refresh-news-daily --provider auto --lookback-days 14
```

CLI возвращает JSON (`status`, `command`, `result`) и используется как внутренний эксплуатационный интерфейс. Если `start-date/end-date` для demo-data не заданы, CLI строит rolling окно: `end_date = today`, `start_date = today - 365 дней`.

## Airflow DAG-и (Phase 7)
Реализованы в `backend/airflow/dags`:
- `ingest_internal_sales_daily`
- `ingest_internal_purchases_daily`
- `build_feature_store_daily`
- `train_models_weekly`
- `ingest_external_indicators_daily`

Общие правила:
- `catchup=False`;
- timezone `Europe/Moscow`;
- retries/timeout заданы на уровне DAG/task;
- `is_paused_upon_creation=True` (ручной trigger для защиты);
- ingest external indicators использует live/cached/manual_snapshot ladder и не ломает core MVP при offline режиме.

## Feature store и артефакты
- Feature store экспортируется daily в `FEATURE_STORE_DIR/<run_date>/features_daily.csv`.
- Модельные артефакты:
  - `models/{product_code}/{horizon}/{version}/...`
- Backtest reports:
  - `backtests/{product_code}/{horizon}/{run_id}.json`
- External indicators manifests:
  - `EXTERNAL_CACHE_DIR/manifests/<run_date>/external_indicators_manifest_<run_id>.json`
  - статус: `ok | warning | degraded | failed`
  - обязательные quality/fallback поля: `coverage_ratio`, `fallback_ratio`, `quality_status`, `reasons`, `provider_mode_counts`.
- Feature refresh manifests:
  - `FEATURE_STORE_DIR/<run_date>/feature_refresh_manifest_<run_id>.json`
  - include `external_context` блок с quality/fallback метриками.
- Model freshness / train manifests:
  - `MODEL_ARTIFACTS_DIR/manifests/*`
  - include `external_context_quality` для retrain/readiness narrative.

## Full demo-chain
`scripts/run_full_demo.py` выполняет:
1. `docker compose up` (`core + airflow`);
2. `alembic upgrade head`;
3. `fuelsight-seed-core`;
4. `generate-demo-data` на rolling окне до текущей даты;
5. `ingest-external-indicators-daily` (manifest-first, quality/fallback artifacts);
6. `build-feature-store-daily`;
7. `train-models-weekly`;
8. `refresh-news-daily` с повторным запуском, если новости записались, но digest ещё не создан;
9. API health + DAG contract checks.

Результат записывается в `scripts/last-smoke-result.json`.

## Принципы v1
- MVP не зависит от LLM/чат-контура.
- Fact grain сохраняется `day x product`.
- What-if ограничен сценарием `retail_price_delta_pct`.
- `ingest_external_indicators_daily` работает в offline-safe режиме: controlled degradation (`cached/last_good/manual_snapshot`) без пустых рядов.
