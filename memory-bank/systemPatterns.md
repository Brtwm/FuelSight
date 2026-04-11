# System Patterns

## Architecture Shape
- Архитектура остаётся той же по форме: `frontend SPA + backend REST API + PostgreSQL + Airflow/pipeline contour`.
- Но фактический baseline уже сместился от чистого MVP к `v2 foundation`:
  - shared frontend design primitives;
  - shared backend `meta` builders;
  - integration scaffold для `external indicators`, `news`, `llm`;
  - operational fallback-oriented data sourcing.
- Документация намеренно двухслойная:
  - `docs_fuelsight/` — `as-built` линия;
  - `docs_fuelsight_2/` — target-spec и roadmap для следующих фаз;
  - `memory-bank/` — краткий operational контекст между сессиями.

## Stable Contracts
- Все серверные маршруты остаются под `/api/v1`.
- API envelope фиксирован: `{ data, error, meta }`.
- Роли остаются `admin` и `analyst`.
- `v1/v2` по-прежнему single-station: сущность `stations` не вводится.
- Chat/news/LLM не могут становиться hard dependency для core flow.

## Domain And Module Boundaries
- Backend домены:
  - `auth`
  - `imports`
  - `kpi`
  - `analytics`
  - `forecasts`
  - `backtests`
  - `news`
  - `chat`
  - `pipeline`
  - `integrations`
- Integration layer теперь устойчиво отделён от доменных сервисов:
  - `backend/app/integrations/external_indicators/*`
  - `backend/app/integrations/news/*`
  - `backend/app/integrations/llm/*`
  - shared contracts/resolution logic в `backend/app/integrations/contracts.py`, `mode_resolver.py`, `registry.py`
- External indicators дополнительно разделены на:
  - adapters;
  - registry;
  - cache manager;
  - repository/service слой;
  - pipeline ingest/manifest layer.

## Frontend Patterns
- V2 shared primitives считаются обязательным направлением, а не экспериментом:
  - `ChartCard`
  - `BusinessSummaryCard`
  - `DataStatePanel`
  - `FreshnessBadgeGroup`
  - `SourceModeBadge`
  - `DiagnosticsDrawer`
- `AppShell` использует slot-based status injection, чтобы глобальные badges не зависели от конкретной страницы.
- Analyst-first UX считается главным продуктовым путём:
  - analyst default login;
  - business-oriented copy;
  - admin diagnostics вынесены из основного narrative.

## API And Meta Patterns
- Shared enriched `meta` уже является частью устойчивой архитектуры.
- Нормализация `meta` вынесена в backend helper builders, чтобы избежать page-specific parsing на фронте.
- Общие `meta`-примитивы включают:
  - `business_summary`
  - `chart_annotations`
  - `reference_overlays`
  - `data_freshness`
  - `model_freshness`
  - `news_freshness`
  - `external_indicators_mode`
  - `provider_mode`
  - `llm_mode`
- Импортный контур тоже переведён на общий vocabulary contract:
  - `display_label`
  - `provenance_mode`
  - `quality_status`

## Data And Pipeline Patterns
- Fact grain остаётся `day x product`.
- External context теперь проектируется как штатная часть исторических данных и будущего feature engineering, а не как sidecar demo trick.
- Для external indicators принят единый runtime pattern:
  - `prefer live`
  - fallback на TTL `cache`
  - затем `last_good/manual_snapshot`
  - при полном провале — контролируемый degraded response вместо пустого результата
- Pipeline ingest фиксируется не heartbeat-файлом, а manifest-артефактом с coverage/fallback/provider statistics.
- Airflow остаётся thin orchestration layer над общим backend task-layer.

## Documentation And Delivery Pattern
- `docs_fuelsight_2/` сначала фиксирует решение как target contract.
- После закрытия очередного среза код должен подтягивать `docs_fuelsight/` как новое `as-built`.
- `memory-bank/` обязан фиксировать фазовый переход сразу после изменения архитектурного или продуктового baseline, чтобы следующая сессия не стартовала со stale assumptions.
