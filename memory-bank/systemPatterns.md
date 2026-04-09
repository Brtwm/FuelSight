# System Patterns

## Architecture Shape
- `frontend` SPA + `backend` REST API + PostgreSQL + Airflow/ML pipeline contour.
- Airflow выполняет операционные задачи через backend task-layer (shared code), а не через API chaining.
- Документация теперь разделена на:
  - `docs_fuelsight/` для текущего `as-built` MVP;
  - `docs_fuelsight_2/` для target-spec улучшенной версии.

## Key Design Decisions
- Все серверные маршруты под `/api/v1`.
- Публичный контракт API фиксирован: envelope `{ data, error, meta }`.
- `request_id` используется для API tracing; pipeline использует structured log fields (`run_id`, `status`, `duration_ms`).
- Security guard: non-local/non-test backend startup требует `JWT_SECRET_KEY` длиной >= 32.
- Роли остаются `admin`/`analyst`.
- `v1` исключает multi-station.
- Bonus LLM/news/chat остаётся isolated contour.
- Для v2 analyst становится primary demo persona.
- Для v2 live integrations проектируются по схеме `provider -> cache -> degraded mode`.
- Для v2 CatBoost фиксируется как primary forecast path, а Seasonal Naive — как benchmark baseline.
- Для external indicators в коде принят adapter/registry pattern с режимами `live`, `cached`, `manual_snapshot`.

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
- `ingest_external_indicators_daily` перешёл от heartbeat-stub к manifest-oriented ingest (coverage/fallback/provider_mode summary).

## Data Patterns
- Fact grain: `day x product`.
- Feature store сохраняется файловым артефактом (`features_daily.csv`) в `FEATURE_STORE_DIR`.
- Model/backtest artifacts сохраняются в `MODEL_ARTIFACTS_DIR`.
- External indicators записываются в `external_indicators_daily` с `provider_mode`, `cache_key`, `metadata_json`.
- Для каждого индикатора используется fallback ladder: `live -> cache (TTL) -> last_good/manual_snapshot`.
- Manifest external ingest сохраняется в cache artifacts (`external/manifests/<run_date>/...json`) и используется в demo-валидации.

## UX Patterns
- Core user flow приоритетнее bonus-контуров.
- Data-heavy страницы поддерживают `loading/empty/error/ready`.
- Empty states должны предлагать import/demo-data путь.
- В v2 аналитические экраны должны использовать единый `chart design system`, freshness/status badges и короткие business summary блоки.

## Documentation Patterns
- После каждой фазы синхронизируются docs + memory-bank.
- Операционные контракты (DAG IDs, demo-run command, env variables) фиксируются в deployment/ml docs.
- Крупные target-решения сначала фиксируются в `docs_fuelsight_2/`, затем реализуются в коде и отражаются в `docs_fuelsight/` как новом `as-built`.

## Testing Patterns (Phase 9)
- Hybrid verification:
  - backend API smoke tests (`core flow`, `LLM off`);
  - browser E2E happy-path (Playwright).
- Demo runner (`scripts/run_full_demo.py`) теперь включает API smoke шаги и опциональный E2E шаг `--with-e2e` в общем JSON-отчёте.
- Для запуска E2E из demo-run используется cross-platform command resolution (`corepack` или fallback `pnpm`).
