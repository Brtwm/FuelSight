# Progress

## What Works
- Фазы 0–7 реализованы end-to-end.
- Core product flow стабилен: `login -> import/demo-data -> dashboard -> sales -> margin -> forecast`.
- Airflow operationalization (Phase 7):
  - custom Airflow image с backend runtime;
  - DAG runtime через `fuelsight-pipeline` task-layer;
  - 5 стандартизированных DAG ID присутствуют и загружаются в Airflow;
  - separate Airflow metadata DB (`airflow`);
  - shared volumes/inbox wiring для pipeline операций.
- Full demo-run automation добавлена (`scripts/run_full_demo.py`) с machine-readable отчётом.
- Structured logging добавлен для API/pipeline.

## Completed Artifacts (Phase 7)
- Infra/compose:
  - `compose/docker-compose.yml`
  - `compose/env/airflow.env`
  - `compose/env/backend.env`
  - `compose/env/db.env`
  - `compose/init/01-create-airflow-db.sql`
  - `backend/airflow/Dockerfile`
- Pipeline backend:
  - `backend/app/core/logging.py`
  - `backend/app/pipeline/__init__.py`
  - `backend/app/pipeline/tasks.py`
  - `backend/app/scripts/pipeline_runner.py`
  - `backend/tests/test_pipeline_tasks.py`
  - `backend/pyproject.toml` (`fuelsight-pipeline` entrypoint)
- Airflow DAGs:
  - `backend/airflow/dags/_runner.py`
  - `backend/airflow/dags/ingest_internal_sales_daily.py`
  - `backend/airflow/dags/ingest_internal_purchases_daily.py`
  - `backend/airflow/dags/build_feature_store_daily.py`
  - `backend/airflow/dags/train_models_weekly.py`
  - `backend/airflow/dags/ingest_external_indicators_daily.py`
- Demo scripts:
  - `scripts/run_full_demo.py`
  - `scripts/demo-run.ps1`
  - `scripts/demo-run.sh`
- Docs sync:
  - `docs_fuelsight/project/backend/deployment.md`
  - `docs_fuelsight/project/backend/ml-pipeline.md`
  - `README.md`
  - `backend/airflow/README.md`
  - `backend/ml/README.md`
  - `frontend/README.md`

## Validation Snapshot
- Backend tests: `uv run pytest` -> `60 passed`.
- Frontend tests: `corepack pnpm --filter frontend test -- --run` -> `28 passed`.
- Compose config check (`core + airflow`) passed.
- Airflow stack boot check passed; `airflow dags list --output json` содержит все 5 DAG ID.

## Remaining Work
- Phase 8: bonus contour `news + chat` (изолированно от core MVP).
- Phase 9: hardening, e2e critical path, documentation polish.

## Known Issues
- Frontend bundle size warning остаётся.
- LLM/news/chat контур не является частью завершённого core MVP.

## Maintenance Rule
- После каждой следующей фазы обновлять:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При архитектурных изменениях поддерживать синхронизацию:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
