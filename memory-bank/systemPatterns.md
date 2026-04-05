# System Patterns

## Architecture Shape
- `frontend` SPA + `backend` REST API + PostgreSQL + Airflow/ML pipeline contour.
- Airflow выполняет операционные задачи через backend task-layer (shared code), а не через API chaining.

## Key Design Decisions
- Все серверные маршруты под `/api/v1`.
- Публичный контракт API фиксирован: envelope `{ data, error, meta }`.
- `request_id` используется для API tracing; pipeline использует structured log fields (`run_id`, `status`, `duration_ms`).
- Роли остаются `admin`/`analyst`.
- `v1` исключает multi-station.
- Bonus LLM/news/chat остаётся isolated contour.

## Domain Breakdown
- `auth`
- `imports`
- `kpi`
- `analytics`
- `forecasts`
- `backtests`
- `news`
- `chat`
- `pipeline` (Phase 7 operational layer)

## Pipeline Patterns (Phase 7)
- Единый task-layer: `app/pipeline/tasks.py`.
- Унифицированный CLI: `fuelsight-pipeline`.
- Airflow DAG-и thin orchestration layer, task logic не дублируется в DAG коде.
- Airflow metadata DB отделена от product DB.
- DAG-и создаются paused-by-default для контролируемого демо режима.

## Data Patterns
- Fact grain: `day x product`.
- Feature store сохраняется файловым артефактом (`features_daily.csv`) в `FEATURE_STORE_DIR`.
- Model/backtest artifacts сохраняются в `MODEL_ARTIFACTS_DIR`.
- External indicators в Phase 7 реализован как stub heartbeat (не блокирует core MVP).

## UX Patterns
- Core user flow приоритетнее bonus-контуров.
- Data-heavy страницы поддерживают `loading/empty/error/ready`.
- Empty states должны предлагать import/demo-data путь.

## Documentation Patterns
- После каждой фазы синхронизируются docs + memory-bank.
- Операционные контракты (DAG IDs, demo-run command, env variables) фиксируются в deployment/ml docs.
