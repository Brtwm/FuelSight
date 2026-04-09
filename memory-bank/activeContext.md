# Active Context

## Current State
- Фаза 8 реализована: bonus contour `news + chat` доступен на `/news`.
- Фаза 9 завершена: hardening + test expansion + docs sync.
- Core MVP API-контракты сохранены: `/api/v1/*` и envelope `{ data, error, meta }`.
- Airflow остаётся в режиме task-layer через backend (без HTTP-обхода), DAG-и paused-by-default.
- Создан новый комплект `docs_fuelsight_2/` как целевая спецификация улучшенной версии поверх текущего MVP.
- В рабочем дереве есть крупный незакоммиченный блок по external indicators и generator realism (backend + compose + demo runner + tests).

## Recently Completed
- Backend hardening:
  - runtime guard для `JWT_SECRET_KEY` (>=32 символов вне `local/test`);
  - env/examples обновлены на безопасный placeholder.
- Phase 9 backend tests:
  - `test_config_security.py` (env-aware JWT guard);
  - `test_phase9_core_flow_api.py` (core API smoke flow);
  - `test_phase9_llm_off_smoke_api.py` (`digest/search` + `chat 503 llm_disabled`).
- Frontend hardening:
  - route-level lazy loading в `AppRouter`;
  - Vite manual chunk split для снижения bundle warning.
- Добавлен browser E2E контур:
  - `frontend/playwright.config.ts`;
  - `frontend/e2e/happy-path.spec.ts`;
  - команда `pnpm test:e2e`.
- `scripts/run_full_demo.py` расширен:
  - `core_api_flow_smoke`;
  - `llm_off_smoke`;
  - опциональный `--with-e2e` шаг в общем machine-readable отчёте;
  - Windows-safe e2e command fallback (`corepack` -> `pnpm`) в demo-run.
- Выполнена документационная и контекстная развилка:
  - `docs_fuelsight/` оставлен как `as-built`;
  - `docs_fuelsight_2/` добавлен как target-spec.
- В `docs_fuelsight_2/` зафиксированы:
  - analyst-first demo mode;
  - нейтральный import UX;
  - chart design system;
  - CatBoost-first ML/pipeline;
  - real integrations + cache/fallback;
  - defense mode.
- Реализован production-like ingest контур external indicators (пока в незакоммиченных изменениях):
  - новые adapters: `EIA Brent`, `CBR USD/RUB`, curated wholesale indexes, `holiday_flag`, `event_pressure_score`;
  - `ExternalIndicatorsRegistry` + `ExternalIndicatorsCacheManager` (TTL cache + `last_good`);
  - новый `ExternalIndicatorsService` с live -> cache -> last_good/manual fallback;
  - `pipeline.tasks.ingest_external_indicators_daily` больше не stub heartbeat, а окно ingest + manifest (`coverage_ratio`, `fallback_ratio`, `provider_mode_counts`);
  - CLI `fuelsight-pipeline ingest-external-indicators-daily` расширен флагами `--provider`, `--run-date`, `--lookback-days`;
  - Airflow DAG `ingest_external_indicators_daily` переключён на `--provider auto`;
  - demo runner шаг `external_indicators_refresh` валидирует `manifest_path`, coverage/fallback метрики;
  - `ImportService.generate_demo_data` теперь подтягивает external context для генератора (с offline-safe fallback).
- Усилен synthetic generator:
  - добавлен curated event catalog;
  - внешние индикаторы влияют на retail/purchase цены и спрос;
  - добавлены межпродуктовые group factors.
- Добавлены/обновлены тесты для adapters/service/pipeline/data_generator; локальный срез: `22 passed` (`test_external_indicator_adapters`, `test_external_indicators_service`, `test_pipeline_tasks`, `test_data_generator`).

## Active Decisions
- LLM/news/chat остаётся bonus contour и не блокирует core MVP.
- При `LLM off` digest/search остаются доступными; chat generation возвращает `503`.
- Источники в чате обязательны: ответы без citations считаются невалидными.
- Источник новостей в базовом варианте: `GDELT` (fixture-driven для локального MVP).
- Для v2 cloud-first LLM и real providers описываются как целевой режим, но offline-safe fallback обязателен.
- Для v2 analyst становится primary user для демонстрационного сценария.
- Для external indicators принят runtime-паттерн `prefer live` при `ENABLE_EXTERNAL_INDICATORS=true` и `EXTERNAL_INDICATORS_MODE=live`, иначе fallback на cache/manual path.
- Для операционного контроля external ingestion фиксируется через manifest-артефакт, а не через stub heartbeat-файл.

## Risks To Remember
- Airflow image сборка остаётся тяжёлой по времени на свежей машине.
- Playwright E2E требует установленный Chromium (`playwright install chromium`) в средах без предустановленного браузера.
- Несмотря на новый ingest-контур, часть v2 всё ещё не закрыта: news остаётся fixture-driven, chat template-based, charts/import-copy всё ещё MVP-level.
- `EXTERNAL_INDICATORS_MODE=live` по умолчанию повышает зависимость от сети и внешних API; при нестабильной сети доля fallback (`cached`/`manual_snapshot`) может расти.
