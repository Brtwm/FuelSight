# System Patterns

## Architecture Shape
- `FuelSight` остаётся локальным single-station приложением: `frontend SPA + backend REST API + PostgreSQL + Airflow + локальные ML/news artifacts`.
- Документация разделена на три слоя:
  - `docs_fuelsight/` — текущее `as-built` описание;
  - `docs_fuelsight_2/` — целевой roadmap/spec;
  - `memory-bank/` — краткий operational-контекст для продолжения работы между сессиями.
- Если код и обзорные документы расходятся, для старта новой задачи приоритет такой: `memory-bank -> код -> docs_fuelsight -> README`.

## Stable Contracts
- UI и бизнес-тексты — на русском языке; технические идентификаторы, API paths и file names — на английском.
- Основной пользовательский маршрут сохраняется: `login -> import/demo-data -> dashboard -> sales analytics -> margin analytics -> forecast`, бонусный вход в `/news` остаётся отдельно.
- Все серверные маршруты живут под `/api/v1`.
- Response envelope не меняется: `{ data, error, meta }`.
- Ролевые границы стабильны:
  - `admin` управляет импортом, refresh/retrain и diagnostics;
  - `analyst` читает аналитику и запускает прогноз.
- LLM/news/chat не могут становиться hard dependency для `import`, `kpi`, `analytics`, `forecast`.

## Domain Boundaries
- Backend организован по доменам: `auth`, `imports`, `kpi`, `analytics`, `forecasts`, `backtests`, `news`, `chat`.
- Отдельный integration-layer считается устойчивым паттерном, а не экспериментом:
  - `backend/app/integrations/external_indicators/*`
  - `backend/app/integrations/news/*`
  - `backend/app/integrations/llm/*`
  - shared contracts и resolution logic в `contracts.py`, `mode_resolver.py`, `registry.py`
- Pipeline task-layer вынесен в `backend/app/pipeline/tasks.py` и переиспользуется из:
  - Airflow DAG-ов;
  - CLI `fuelsight-pipeline`;
  - demo/smoke runner.

## Frontend Patterns
- Analyst-first UX остаётся главным product path: нейтральный operational copy, минимум ML-жаргона, акцент на бизнес-объяснениях.
- Shared common-компоненты считаются базовым UI-каркасом:
  - `ChartCard`
  - `BusinessSummaryCard`
  - `DataStatePanel`
  - `FreshnessBadgeGroup`
  - `SourceModeBadge`
  - `DiagnosticsDrawer`
- `AppShell` остаётся чистым navigation shell: drawer/bottom navigation, role chip и logout. Provider/freshness/LLM/defense indicators показываются только на страницах, которым они нужны.
- Фильтры страниц должны синхронизироваться с URL query params.

## Forecasting Patterns
- Winner policy фиксирован: `CatBoost` — primary model, `Seasonal Naive` — benchmark и controlled fallback.
- Forecast/backtest payloads должны не только отдавать прогноз и метрики, но и нести operational health-контекст:
  - `model_freshness`
  - `training_window`
  - `baseline_comparison`
  - `feature_sources`
  - `retrain_status`
  - `provider_mode`
- Scenario-flow на фронте трактуется как отдельный `base`-run плюс отдельный `what-if` run, которые потом сравниваются в одном chart/table, а не как замена базового прогноза.
- Model health считается на бэкенде на основе возраста модели и свежести feature-refresh manifest, а не выводится эвристикой на фронте.

## Data And Pipeline Patterns
- Fact grain не меняется: `day x product`.
- External indicators входят в основной forecasting-контур и используют fallback ladder:
  - `live`
  - `cache`
  - `last_good/manual_snapshot`
- Feature engineering уже выходит за базовые лаги и включает:
  - `lag/rolling`
  - `calendar`
  - `price/margin`
  - `external indicators`
  - `event pressure`
  - `cross-product context`
- Для operational-прозрачности важны manifest-артефакты:
  - ingest manifest по external indicators;
  - `feature_refresh_manifest_*`;
  - `train_backtest_manifest_*`;
  - `model_freshness_manifest_*`.

## Documentation Discipline
- Mandatory sync rule: любое изменение code capability, API payload, demo story, Phase status или supported degraded mode должно синхронно обновлять `memory-bank/*`, релевантные документы в `docs_fuelsight/*` и `docs_fuelsight_2/phase0-gap-matrix.md`.
- Не полагаться на phase-label как единственный источник истины: в репозитории уже есть разъезд между `README` и `docs_fuelsight_2/v2-roadmap.md`.
- В `memory-bank` лучше фиксировать capability-based статус:
  - что реально реализовано;
  - что сейчас в worktree;
  - что ещё не подтверждено тестами или коммитом.
- Для нового входа в проект использовать doc stack:
  - `docs_fuelsight/as-built-baseline.md` как честный `as-built`;
  - `docs_fuelsight_2/v2-roadmap.md` как target roadmap;
  - `docs_fuelsight_2/phase0-gap-matrix.md` как execution backlog.
- `README.md` больше не считается phase-tracker; его задача — кратко отражать capability snapshot и указывать на source-of-truth docs.
