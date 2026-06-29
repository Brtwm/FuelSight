# FuelSight Deployment and Local Environment

## Цель развёртывания
Проект должен стабильно запускаться на чистой машине для защиты диплома: core MVP (`frontend + backend + db`) и операционный контур Airflow с воспроизводимым demo-run.

Production-развертывание на VPS, GHCR images, HTTPS, backup и ручной
GitHub Environment deploy описаны в `docs/vps-deployment.md`. Локальный
`.env` для этого не изменяется и не копируется в Git.

## Docker Compose сервисы
| Service | Назначение | Port |
|---|---|---|
| `frontend` | React SPA | `3000` |
| `backend` | FastAPI API | `8061` |
| `db` | PostgreSQL + pgvector (product DB) | `5432` |
| `db-airflow-init` | one-shot создание DB `airflow` | internal |
| `airflow-init` | миграция Airflow metadata + admin user | one-shot |
| `airflow-webserver` | UI и мониторинг DAG | `8080` |
| `airflow-scheduler` | планировщик DAG | internal |

## Compose/Volumes
- `compose/docker-compose.yml` использует profiles `core` и `airflow`.
- `db` использует image `pgvector/pgvector:pg16`; расширение `vector` включается Alembic-миграцией для RAG chunks.
- Обязательные named volumes:
  - `postgres_data`
  - `model_artifacts`
  - `news_index`
  - `airflow_logs`
- Shared bind mounts:
  - `backend/airflow/dags -> /opt/airflow/dags`
  - `backend/airflow/plugins -> /opt/airflow/plugins`
  - `backend/airflow/inbox -> /opt/fuelsight/inbox`

## Airflow image
Airflow работает на custom image `backend/airflow/Dockerfile`:
- базируется на `apache/airflow:2.10.3-python3.12`;
- включает backend+ml код;
- поднимает отдельную `uv`-виртуалку с `fuelsight-backend` зависимостями;
- DAG-и запускают pipeline через `uv run fuelsight-pipeline ...` без HTTP-обхода.

## Локальный запуск
### Core
```bash
docker compose -f compose/docker-compose.yml --profile core up -d
```

### Core + Airflow
```bash
docker compose -f compose/docker-compose.yml --profile core --profile airflow up -d
```

### Остановка
```bash
docker compose -f compose/docker-compose.yml --profile core --profile airflow down
```

## Full demo-run
Одна команда для воспроизводимой цепочки:
```bash
python scripts/run_full_demo.py
```

Опционально с browser E2E happy-path:
```bash
python scripts/run_full_demo.py --with-e2e
```
Опционально с mobile E2E artifacts:
```bash
python scripts/run_full_demo.py --with-mobile-e2e
```
Перед первым E2E-прогоном на fresh machine:
```bash
corepack pnpm --filter frontend exec playwright install chromium
```

PowerShell wrapper:
```powershell
./scripts/demo-run.ps1
```

Bash wrapper:
```bash
./scripts/demo-run.sh
```

Отчёт сохраняется в `scripts/last-smoke-result.json` в machine-readable формате (`PASS/FAIL`, шаги, длительность, подсказка по логам).
Отчёт включает:
- pipeline smoke шаги;
- rolling demo-data window до текущей даты;
- порядок подготовки `external indicators -> feature store -> train -> news -> rag index`;
- API core flow (`login -> generate-demo -> KPI -> analytics -> forecast -> backtests`);
- `LLM off` smoke (`news digest/search` + `chat retrieval_only` или честный blocked uncertainty);
  - опциональный Playwright desktop persona шаг при запуске с `--with-e2e`;
  - опциональный Playwright mobile device-class шаг при запуске с `--with-mobile-e2e`.

## Docs Discipline
- Documentation sync rule: любое изменение runtime capability, env/profile behavior, demo chain или verification story должно синхронно обновлять `README.md` при изменении quick-start/demo flow и релевантные документы в `docs/`.
- `README.md` остаётся кратким public snapshot; подробные runbook и контракты живут в `docs/`.

## Переменные окружения compose
### Backend (`compose/env/backend.env`)
```env
APP_PORT=8061
DATABASE_URL=postgresql+psycopg://fuelsight:fuelsight@db:5432/fuelsight
ENABLE_LLM=false
MODEL_ARTIFACTS_DIR=/opt/fuelsight/artifacts/models
NEWS_INDEX_DIR=/opt/fuelsight/artifacts/news
LLM_PROVIDER_MODE=retrieval_only
LLM_PROVIDER=none
PIPELINE_SALES_INBOX_DIR=/opt/fuelsight/inbox/sales
PIPELINE_PURCHASES_INBOX_DIR=/opt/fuelsight/inbox/purchases
PIPELINE_INBOX_ARCHIVE_DIR=/opt/fuelsight/inbox/archive
FEATURE_STORE_DIR=/opt/fuelsight/artifacts/models/features
```

### Frontend (`compose/env/frontend.env`)
```env
VITE_API_BASE_URL=http://localhost:8061/api/v1
VITE_APP_PORT=3000
VITE_ENABLE_LLM=false
```

### Airflow (`compose/env/airflow.env`)
```env
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://fuelsight:fuelsight@db:5432/airflow
AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8080
DATABASE_URL=postgresql+psycopg://fuelsight:fuelsight@db:5432/fuelsight
MODEL_ARTIFACTS_DIR=/opt/fuelsight/artifacts/models
NEWS_INDEX_DIR=/opt/fuelsight/artifacts/news
LLM_PROVIDER_MODE=retrieval_only
LLM_PROVIDER=none
```

## Наблюдаемость
- API и pipeline используют structured JSON logs (`timestamp`, `level`, `message`, `request_id`, `run_id`, `status`, `duration_ms`).
- Airflow логирует запуск DAG/task в `airflow_logs`.
- Health endpoints:
  - backend: `GET /api/v1/health`
  - airflow web: `http://localhost:8080/health`

## Проверка после запуска
1. `docker compose -f compose/docker-compose.yml ps`
2. `curl http://localhost:8061/api/v1/health`
3. `docker compose -f compose/docker-compose.yml --profile airflow exec -T airflow-webserver airflow dags list --output json`
4. `python scripts/run_full_demo.py --no-build`
