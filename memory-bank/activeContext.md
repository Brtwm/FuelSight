# Active Context

## Current State
- Фаза 7 реализована: Airflow operationalization + reproducible local demo-run.
- Core MVP API-контракты не менялись: `/api/v1/*` и envelope `{ data, error, meta }` сохранены.
- Airflow работает через backend task-layer (без HTTP-обхода), DAG-и создаются paused-by-default.

## Recently Completed
- Обновлён `compose/docker-compose.yml`:
  - profile-aware stack `core + airflow`;
  - отдельная metadata DB `airflow` внутри PostgreSQL;
  - one-shot `db-airflow-init` для гарантированного создания DB;
  - mounts для `dags/plugins/inbox` и shared volumes.
- Добавлен custom Airflow image: `backend/airflow/Dockerfile`.
- Реализован pipeline layer:
  - `backend/app/pipeline/tasks.py`
  - CLI: `uv run fuelsight-pipeline ...` (`backend/app/scripts/pipeline_runner.py`).
- Реализованы DAG-и:
  - `ingest_internal_sales_daily`
  - `ingest_internal_purchases_daily`
  - `build_feature_store_daily`
  - `train_models_weekly`
  - `ingest_external_indicators_daily` (stub).
- Реализован full demo chain:
  - `scripts/run_full_demo.py`
  - wrappers: `scripts/demo-run.ps1`, `scripts/demo-run.sh`
  - machine-readable output: `scripts/last-smoke-result.json`.
- Добавлено structured JSON logging:
  - `backend/app/core/logging.py`
  - API middleware пишет `duration_ms`, `request_id`, status.

## Active Decisions
- Airflow интегрируется через backend modules + CLI (`fuelsight-pipeline`), не через API.
- `ingest_external_indicators_daily` остаётся рабочим stub в v1.
- Airflow metadata хранится в DB `airflow`, product данные в DB `fuelsight`.
- DAG-режим: paused-by-default, ручной trigger для защиты.
- Full demo-run: одна команда, детерминированный отчёт шагов PASS/FAIL.

## Risks To Remember
- Dev JWT secret остаётся демонстрационным (`change-me`), для production-like демо нужен ключ >= 32 символов.
- Airflow image сборка тяжелая по времени на свежей машине.
- `ingest_external_indicators_daily` не даёт реальных внешних данных (stub by design).
- Bonus контур `news/chat` всё ещё не завершён (Phase 8).
