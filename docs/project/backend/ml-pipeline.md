# FuelSight ML and Pipeline Design

## Цели ML-контура
- Прогноз спроса по каждому виду топлива на горизонтах `1`, `7`, `30` дней.
- Показ объяснимого результата: прогноз, интервалы, драйверы и evidence качества модели.
- Подтверждение качества через отложенную временную проверку, сравнение с `Seasonal Naive` и метрики `MAE/RMSE/SMAPE`.
- Полная воспроизводимость demo-сценария на локальной машине.

## Реализованный ML-контур
- Базовая модель: `Seasonal Naive`.
- Основная модель: `CatBoostRegressor`.
- Backtest: `rolling/expanding`, winner по `SMAPE` (tie-break `RMSE`).
- Validation evidence: CatBoost сравнивается с `Seasonal Naive` на тестовом периоде; `MAE`, `RMSE`, `SMAPE` переиспользуются без изменения формул.
- Артефакты и отчёты сохраняются в `MODEL_ARTIFACTS_DIR`.
- API-эндпоинты:
  - `POST /api/v1/forecasts/run`
  - `GET /api/v1/forecasts/latest`
  - `POST /api/v1/backtests/run`
  - `GET /api/v1/backtests/latest`

## Validation evidence
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

`validation_summary` является опциональным расширением существующего payload
backtest, а не отдельным endpoint. Новые backtest runs сохраняют summary в
существующем `metrics_json` записи `backtest_runs`; `GET /api/v1/backtests/latest`
возвращает stored summary, если оно есть. Для legacy metrics без сохранённого
summary сервис строит controlled fallback с `LIMITED`, потому что метрики есть,
но тестовый ряд или наблюдения могут быть неизвестны. При отсутствии comparison
metrics возвращается `UNKNOWN`.

Статусы интерпретируются как пользовательская оценка полноты evidence:
- `OK`: CatBoost проверен на тестовом периоде и не хуже `Seasonal Naive` по `SMAPE`.
- `LIMITED`: evidence есть, но оно неполное, короткое, без нужных метрик/ряда или CatBoost хуже baseline по `SMAPE`.
- `UNKNOWN`: validation evidence недоступно.

Это не MLOps monitoring platform и не drift-monitoring контур. Validation
artifacts используются для аналитического объяснения качества в дипломном MVP и
не гарантируют точное значение будущего спроса или цены.

## Pipeline task-layer
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

## Airflow DAG-и
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
  - report file остаётся существующим артефактом backtest; validation summary для API хранится в `metrics_json`, а не как отдельная подсистема мониторинга.
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
