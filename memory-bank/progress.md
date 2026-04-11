# Progress

## What Works
- Базовый MVP-поток по-прежнему рабочий: `login -> import -> dashboard -> sales -> margin -> forecast`, bonus contour `/news` сохранён.
- Поверх MVP в репозитории уже реализован foundation для `v2` Фаз `0-3`.

## Implemented V2 Baseline
- Фаза 0. Freeze contracts и backend integration scaffold:
  - backend `integrations/` выделен в отдельный слой (`external_indicators`, `news`, `llm`);
  - введены общие enum/status-типы для provider/freshness/degradation/quality на backend и frontend;
  - `.env.example` и config уже расширены под `external indicators`, `llm provider mode`, `defense mode`;
  - миграция и модель `external_indicators_daily` добавлены в основную схему.
- Фаза 1. Shared frontend/backend primitives:
  - созданы общие UI-компоненты `ChartCard`, `BusinessSummaryCard`, `DataStatePanel`, `FreshnessBadgeGroup`, `SourceModeBadge`, `DiagnosticsDrawer`;
  - `AppShell` поддерживает status slots и глобальные badges;
  - на фронте выделены общие API/meta types для enriched payloads;
  - на бэкенде есть `meta_builders.py` для унификации enriched `meta`.
- Фаза 2. Analyst-first UX и neutral import:
  - login по умолчанию analyst-first;
  - `/auth/me` содержит `preferred_landing_route`;
  - import flow переведён в operational panels + admin-only diagnostics;
  - import jobs отдают `display_label`, `provenance_mode`, `quality_status`.
- Фаза 3. Realistic initial data и external indicators:
  - реализованы repository/service для `external_indicators_daily`;
  - работают adapters для `crude_brent_usd`, `usd_rub`, `wholesale_*`, `holiday_flag`, `event_pressure_score`;
  - cache manager поддерживает `TTL`, `cache`, `last_good`, `manual_snapshot`;
  - synthetic data generator использует curated event catalog, cross-product dynamics и external context;
  - `ingest_external_indicators_daily` больше не stub: pipeline пишет manifest с `coverage_ratio`, `fallback_ratio`, `provider_mode_counts`.

## Still Working From Earlier Phases
- Bonus contour `news + chat` из прошлых фаз доступен, но остаётся MVP-level:
  - `/news` есть в UI и API;
  - citations обязательны;
  - при `LLM off` core product не ломается.
- Airflow/task-layer/CLI контур уже есть и служит foundation для следующих v2 фаз.
- Structured logging, demo runner и Phase 9 hardening остаются частью рабочего baseline.

## Validation Snapshot
- Memory-bank update основан на текущем состоянии репозитория, а не на старой записи про "uncommitted branch":
  - `git status --short` -> clean;
  - `git log -n 1` -> `9097ad7 external indicators for data`.
- По ранее зафиксированным результатам в проекте уже были успешные:
  - backend pytest/smoke срезы;
  - frontend unit/integration tests;
  - Playwright e2e happy-path;
  - demo-run smoke.
- В этой сессии дополнительные тесты не перезапускались; обновление банка сделано по фактической структуре кода, конфигов и документации.

## Remaining Work
- Фаза 4: расширить реальные payloads `kpi/analytics` и перевести `/dashboard`, `/analytics/sales`, `/analytics/margin` на explainable UX с shared components.
- Фаза 5: сделать CatBoost-first forecasting с richer model metadata, freshness и baseline comparison.
- Фаза 6: перевести `news/chat` с fixture/template baseline на real providers + retrieval-first fallback ladder.
- Фаза 7: собрать defense mode, defense report, executive outputs и export/PDF.
- Фаза 8: зафиксировать всё это тестами, e2e-сценариями и полным docs sync.

## Known Issues And Gaps
- Верхнеуровневый `README.md` и часть `docs_fuelsight/` всё ещё ближе к старому Phase 9 baseline, чем к фактическому состоянию после v2 Фазы 3.
- Shared primitives и enriched meta уже есть, но ещё не везде доведены до полного analyst-facing UX на ключевых аналитических страницах.
- `news/chat` и defense контур пока не соответствуют полной v2-спецификации.

## Maintenance Rule
- После каждого следующего архитектурного среза обновлять минимум:
  - `memory-bank/activeContext.md`
  - `memory-bank/progress.md`
- При изменении устойчивых решений по архитектуре/стеку дополнительно синхронизировать:
  - `memory-bank/systemPatterns.md`
  - `memory-bank/techContext.md`
