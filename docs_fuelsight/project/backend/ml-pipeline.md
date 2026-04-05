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
- `ingest_external_indicators_daily` (stub heartbeat)
- `generate_demo_data`

## CLI контракт
Запуск через backend environment:
```bash
cd backend
uv run fuelsight-pipeline ingest-sales-daily
uv run fuelsight-pipeline ingest-purchases-daily
uv run fuelsight-pipeline build-feature-store-daily
uv run fuelsight-pipeline train-models-weekly --window-type rolling
uv run fuelsight-pipeline ingest-external-indicators-daily --provider stub
uv run fuelsight-pipeline generate-demo-data --replace-existing --start-date 2025-01-01 --end-date 2025-12-31
```

CLI возвращает JSON (`status`, `command`, `result`) и используется как внутренний эксплуатационный интерфейс.

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
- ingest external indicators остаётся stub, не блокирует core MVP.

## Feature store и артефакты
- Feature store экспортируется daily в `FEATURE_STORE_DIR/<run_date>/features_daily.csv`.
- Модельные артефакты:
  - `models/{product_code}/{horizon}/{version}/...`
- Backtest reports:
  - `backtests/{product_code}/{horizon}/{run_id}.json`
- External indicators stub heartbeat:
  - `news/external_indicators_stub/heartbeat_*.json`

## Full demo-chain
`scripts/run_full_demo.py` выполняет:
1. `docker compose up` (`core + airflow`);
2. `alembic upgrade head`;
3. `fuelsight-seed-core`;
4. `generate-demo-data`;
5. `build-feature-store-daily`;
6. `train-models-weekly`;
7. `ingest-external-indicators-daily`;
8. API health + DAG contract checks.

Результат записывается в `scripts/last-smoke-result.json`.

## Принципы v1
- MVP не зависит от LLM/чат-контура.
- Fact grain сохраняется `day x product`.
- What-if ограничен сценарием `retail_price_delta_pct`.
- `ingest_external_indicators_daily` intentionally stub до отдельной фазы интеграций.
