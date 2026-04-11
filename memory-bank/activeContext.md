# Active Context

## Current State
- Репозиторий уже не находится в состоянии `Phase 9 + uncommitted experiments`: зафиксирован коммит `9097ad7` (`external indicators for data`), рабочее дерево чистое.
- Текущий фактический baseline: закрыты `v2` Фазы `0-3` поверх прежнего MVP/Phase 9 foundation.
- Core contracts сохранены:
  - маршруты UI остаются `login -> dashboard -> analytics/* -> forecast -> news`;
  - backend остаётся под `/api/v1/*`;
  - response envelope не меняется: `{ data, error, meta }`;
  - роли остаются `admin` и `analyst`;
  - продукт всё ещё single-station, без `stations`.
- `docs_fuelsight/` остаётся `as-built` линией для текущего MVP-бейзлайна, `docs_fuelsight_2/` — целевой и частично уже реализованный `v2` контур.

## Recently Confirmed In Code
- Фаза 0 закрыта как технический каркас:
  - backend `integrations/` уже выделен для `external indicators`, `news`, `llm`;
  - общие provider/freshness/degradation/quality типы заведены в backend schemas и frontend API types;
  - `.env.example` уже содержит `ENABLE_EXTERNAL_INDICATORS`, `EXTERNAL_INDICATORS_MODE`, `EXTERNAL_CACHE_DIR`, `LLM_PROVIDER_MODE`, `DEFENSE_MODE`, `DEFENSE_PROFILE`;
  - миграция `20260408_0005_phase0_external_indicators.py` и модель `external_indicators_daily` уже существуют.
- Фаза 1 закрыта как shared primitives слой:
  - на фронте есть `ChartCard`, `BusinessSummaryCard`, `DataStatePanel`, `FreshnessBadgeGroup`, `SourceModeBadge`, `DiagnosticsDrawer` и их тесты;
  - `AppShell` переведён на slot-based status badges (`data/model/news freshness`, `LLM mode`, `Indicators mode`);
  - frontend common API/meta types уже централизованы в `frontend/src/lib/api/common.types.ts`;
  - backend helper `backend/app/api/v1/meta_builders.py` нормализует enriched `meta` для `kpi`, `analytics`, `forecasts`, `news`.
- Фазы 2-3 тоже уже отражены в коде:
  - login default переключён на `analyst@fuelsight.local`;
  - `/auth/me` отдаёт `preferred_landing_route`;
  - `/import` переписан в нейтральный operational UI, а diagnostics вынесены в admin-only drawer;
  - import jobs получают `display_label`, `provenance_mode`, `quality_status`;
  - `ImportService.generate_demo_data` использует `ExternalIndicatorsService` и сохраняет offline-safe fallback;
  - external indicators получили service/repository слой, provider adapters, TTL cache, `last_good/manual_snapshot` fallback и manifest-oriented ingest.

## Current Focus
- Следующий крупный срез после фактически закрытой Фазы 3: `Фаза 4 — KPI и explainable analytics`.
- Главная задача следующего этапа: начать использовать уже подготовленные shared meta/primitives не как инфраструктуру "в стол", а как реальный UX-контракт для `/dashboard`, `/analytics/sales`, `/analytics/margin`.
- Параллельно важно не потерять docs sync:
  - `memory-bank/` теперь должен считаться более актуальным оперативным контекстом, чем верхнеуровневый `README`, который ещё описывает Phase 9 baseline;
  - после следующих срезов нужно подтягивать `docs_fuelsight/` до нового `as-built`.

## Active Decisions
- Analyst-first остаётся главным демонстрационным сценарием; `admin` — отдельная операционная роль для import/refresh/retrain/diagnostics.
- External indicators считаются штатной частью data realism и pipeline readiness, но обязаны деградировать предсказуемо через `cached` и `manual_snapshot`.
- LLM/news/chat по-прежнему не должны ломать основной контур KPI/analytics/forecast.
- Shared enriched `meta` и status badges считаются стабильным направлением v2 и должны переиспользоваться, а не дублироваться page-specific эвристиками.

## Risks To Remember
- В коде уже накопился фактический `v2` прогресс, который ещё не везде отражён в `docs_fuelsight/` и части обзорной документации.
- После Фазы 3 всё ещё остаются заметные продуктовые gaps:
  - KPI/dashboard и analytics pages ещё не полностью пересобраны под new chart system и explainable summaries;
  - forecasting, news/chat и defense mode ещё впереди по roadmap;
  - часть analyst-facing copy всё ещё может оставаться ближе к MVP, чем к финальному business UX.
- `EXTERNAL_INDICATORS_MODE=live` как дефолт сохраняет сетевую зависимость; при плохой сети нормой должен считаться рост fallback ratio, а не падение пайплайна.
