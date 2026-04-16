# Progress

## Stable Baseline
- Базовый MVP flow реализован: `login -> import/demo-data -> dashboard -> sales analytics -> margin analytics -> forecast`, бонусный `/news` присутствует.
- В репозитории уже есть доменный backend под `auth/imports/kpi/analytics/forecasts/backtests/news/chat`.
- На фронте есть shared common-layer:
  - `ChartCard`
  - `BusinessSummaryCard`
  - `DataStatePanel`
  - `FreshnessBadgeGroup`
  - `SourceModeBadge`
  - `DiagnosticsDrawer`
- Integration scaffold для `external_indicators`, `news`, `llm` уже выделен в отдельный слой.
- Airflow DAG-ы и CLI pipeline существуют и используются как часть реального demo/ops-контура.

## Implemented / Confirmed Foundations
- Analyst-first направление уже закреплено:
  - analyst default login;
  - role-safe import/diagnostics separation;
  - русскоязычный business-oriented UX.
- External indicators перестали быть чистым stub-контуром:
  - есть provider adapters;
  - есть cache/fallback strategy;
  - есть repository/service слой;
  - данные уже входят в forecasting/pipeline baseline.
- Forecasting foundation уже вышел за рамки "baseline-only":
  - `CatBoost` закреплён как основной путь;
  - `Seasonal Naive` остался benchmark/fallback;
  - pipeline, API и UI уже несут richer meta, а не только raw forecast values.

## Current In-Progress Slice
- В worktree идёт forecast quality/health refinement:
  - feature store расширяется external/event/group признаками;
  - pipeline пишет manifest-артефакты для feature refresh и model freshness;
  - forecast/backtest contracts обогащаются `model_freshness`, `training_window`, `baseline_comparison`, `feature_sources`, `retrain_status`, `provider_mode`;
  - `/forecast` переводится на `base vs scenario` сравнение и отдельную `ModelHealthPanel`;
  - demo runner начинает валидировать manifest-выходы.

## Verified In This Session
- `backend` targeted forecast suite -> `11 passed`
- `frontend` vitest suite -> `35 files / 92 tests passed`

## Remaining Work
- Синхронизировать `docs_fuelsight/` и `README.md` с текущим forecasting-контрактом и реальным уровнем готовности.
- Довести `/dashboard`, `/analytics/sales`, `/analytics/margin` до того же explainable/shared-component уровня, что и forecast.
- Перевести `news/chat` с MVP/fixture-подхода на real providers + retrieval-first fallback.
- Собрать defense mode, executive outputs и export story.
- После стабилизации локального forecast-среза прогнать более широкий smoke/e2e.

## Known Gaps
- В репозитории есть расхождение между phase-label в разных документах:
  - `README` говорит о `Phase 9 complete`;
  - `docs_fuelsight_2/v2-roadmap.md` использует phases `1-7`;
  - для рабочих задач надёжнее ориентироваться на capability-based описание в `memory-bank`.
- Существенная часть текущего forecasting-среза пока не закоммичена.
- Generated/local артефакты (`frontend/output/`, `git_diff_output.txt`) могут мешать чистому publish/commit, если их не держать под контролем.

## Maintenance Rule
- После каждого значимого кодового среза обновлять как минимум:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При изменении устойчивых решений по архитектуре, pipeline или contracts дополнительно синхронизировать:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
