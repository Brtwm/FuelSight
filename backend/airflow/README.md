# Airflow (Phase 7)

Airflow контур реализован для operational/demo задач MVP.

## Реализованные DAG ID
- `ingest_internal_sales_daily`
- `ingest_internal_purchases_daily`
- `build_feature_store_daily`
- `train_models_weekly`
- `ingest_external_indicators_daily`
- `refresh_news_daily`
- `refresh_rag_index_daily`

## Правила
- `catchup=False`
- timezone: `Europe/Moscow`
- `is_paused_upon_creation=True`
- retries/timeout заданы для каждого DAG/task

## Как DAG исполняет бизнес-логику
DAG-и вызывают CLI task-layer через helper `_runner.py`:
- `uv run fuelsight-pipeline ...`
- без HTTP-call chain
- единый кодиспользуемый task-layer: `app/pipeline/tasks.py`

## Локальная проверка
```bash
docker compose -f compose/docker-compose.yml --profile airflow up -d
docker compose -f compose/docker-compose.yml --profile airflow exec -T airflow-webserver airflow dags list --output json
```

## Full demo run
Для полной цепочки используйте:
```bash
python scripts/run_full_demo.py
```
