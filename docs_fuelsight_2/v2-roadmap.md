# FuelSight v2 Roadmap

## Принцип приоритизации
Сначала фиксируется честный `as-built` baseline, затем усиливается analyst-facing продуктовая часть, потом строится главный differentiating contour `real news + verified RAG chat`, и только после этого собирается финальный defense/exec слой.

## Phase A. Contracts Freeze + Docs Sync
- Цель: зафиксировать реальное `as-built` состояние и убрать расхождения между `memory-bank`, `docs_fuelsight`, `docs_fuelsight_2`, `README`.
- Выходы:
  - capability-based status matrix вместо спорных phase-label;
  - обновлённый roadmap с отдельными треками `visual/mobile`, `real news`, `RAG chat`, `defense`;
  - единый backlog `doc item -> code module -> tests -> demo scenario`.
- Зависимости:
  - текущая кодовая база;
  - `memory-bank/*`;
  - `docs_fuelsight/*`;
  - `docs_fuelsight_2/*`.
- Проверка:
  - можно однозначно ответить, что уже готово, что только в `worktree`, а что существует только как `target`;
  - `docs_fuelsight/` описывает текущее состояние, `docs_fuelsight_2/` — целевое.

## Phase B. Visual Polish + Mobile Readiness
- Цель: сделать analyst-facing UI убедительным на desktop и мобильных устройствах, так как проверка на защите likely будет идти и с телефона.
- Выходы:
  - responsive `AppShell` без desktop-only permanent drawer на малых экранах;
  - mobile-first layout для `/dashboard`, `/forecast`, `/news`;
  - компактные filters, карточечные таблицы, сокращённые legends/tooltips;
  - отдельный mobile Playwright profile и visual smoke.
- Зависимости:
  - текущие shared common components;
  - статусные badges и shell slots;
  - analyst-first content hierarchy.
- Проверка:
  - ключевые маршруты читабельны и управляемы на mobile width;
  - analyst flow проходит и на desktop, и на mobile without layout breakage.

## Phase C. Explainable Analytics Completion
- Цель: довести `dashboard`, `sales`, `margin` до единого explainable chart system уровня.
- Выходы:
  - единое использование `ChartCard`, `BusinessSummaryCard`, `DataStatePanel`, `FreshnessBadgeGroup`;
  - role-aware empty/degraded states;
  - согласованная подача `chart_annotations`, `reference_overlays`, `threshold_info`, `supporting_refs`;
  - business summaries на каждой analyst-facing странице.
- Зависимости:
  - enriched backend meta builders;
  - текущий AppShell/status layer;
  - URL-synced filters.
- Проверка:
  - analyst понимает не только что произошло, но и почему это важно;
  - все три аналитические страницы выглядят как единый продуктовый слой.

## Phase D. Data Realism + External Context Hardening
- Цель: закрепить realism story для исходных данных, overlays и forecasting features.
- Выходы:
  - правдоподобная initial history с межпродуктовым контекстом;
  - curated event catalog как часть explainability;
  - quality/fallback metrics для external indicators;
  - устойчивый pipeline для `external_indicators_daily`.
- Зависимости:
  - existing `external_indicators_daily` schema;
  - provider adapters;
  - cache/snapshot manager.
- Проверка:
  - generated dataset годится и для обучения, и для демонстрации контекста;
  - offline-safe режим не ломает data story.

## Phase E. CatBoost-First Forecast Finalization
- Цель: дотянуть forecasting-контур до fully polished analyst-facing capability.
- Выходы:
  - финальный `base vs scenario` UX;
  - model health panel with readable freshness/retrain/baseline signals;
  - deterministic manifests and health artifacts;
  - final docs sync for forecast contracts.
- Зависимости:
  - feature store v2;
  - model freshness manifests;
  - current forecast worktree slice.
- Проверка:
  - `/forecast` сам по себе уже выглядит как сильная демонстрационная feature;
  - analyst видит качество модели без admin-only действий.

## Phase F. Real News Ingestion Baseline
- Цель: заменить fixture ingest на реальный ingest + cache + normalized storage.
- Выходы:
  - `news` provider adapters;
  - normalized ingest contract и cache policy;
  - digest builder поверх реально сохранённых `news_raw`;
  - refresh step как часть standard pipeline/demo chain.
- Зависимости:
  - `backend/app/integrations/news/*`;
  - `news_raw`, `news_digests`;
  - source normalization strategy.
- Проверка:
  - digest/search больше не зависят от fixture списка;
  - provider mode и freshness видны пользователю.

## Phase G. RAG-First Chat Core
- Цель: построить grounded chat поверх внутренних ref и реально сохранённых новостей без агентного веб-поиска.
- Выходы:
  - session-aware retrieval по `news_raw`, `news_digests`, `kpi`, `analytics`, `forecast`;
  - unified citations с `provider_mode`, `confidence`, `source_type`;
  - mode ladder `cloud_llm -> local_llm -> retrieval_only`;
  - `LLM off` больше не даёт hard failure по умолчанию.
- Зависимости:
  - real news ingest;
  - citation contracts;
  - LLM adapter interface.
- Проверка:
  - ни один chat answer не возвращается без citations;
  - even degraded mode still returns useful retrieval-grounded answer.

## Phase H. Advanced RAG Quality Layer
- Цель: сделать chat сильной feature диплома без перехода к нестабильному autonomous-agent паттерну.
- Выходы:
  - query normalization и optional rewrite;
  - hybrid retrieval + rerank;
  - session memory / short running summary;
  - final verification pass перед выдачей ответа;
  - confidence scoring по retrieval signals, а не только по генерации.
- Зависимости:
  - базовый RAG core;
  - persisted chat sessions/messages;
  - deterministic evidence pack pipeline.
- Проверка:
  - ответы стали точнее, короче и честнее в uncertainty cases;
  - verification умеет блокировать unsupported answer.

## Phase I. Cloud LLM Primary + Local Fallback
- Цель: использовать облачную русскоязычную модель как основной demo path, сохранив local fallback и retrieval-only safety.
- Выходы:
  - provider-agnostic `LLM adapter` abstraction;
  - first cloud provider integration;
  - local adapter for fallback;
  - clear mode surfacing in API/UI.
- Зависимости:
  - RAG core and verification layer;
  - config/env and provider mode contracts.
- Проверка:
  - смена провайдера не требует переписывания product contracts;
  - при отсутствии cloud key продукт деградирует мягко и явно.

## Phase J. Defense Mode + Executive Outputs
- Цель: превратить проект в управляемую и воспроизводимую защитную демонстрацию.
- Выходы:
  - profile-driven `run_full_demo.py` for `offline-safe` and `cloud-enhanced`;
  - defense report со статусами `ok/warning/degraded/failed`;
  - one-page export/PDF;
  - short decision journal;
  - shell/page badges for provider modes and freshness.
- Зависимости:
  - previous phases;
  - stable smoke/e2e chain.
- Проверка:
  - fresh-machine run выводит систему в показоспособное состояние;
  - отсутствие сети или ключей не блокирует демонстрацию.

## Phase K. Hardening, Tests, Docs Discipline
- Цель: закрепить продукт как устойчивый diploma-ready artifact.
- Выходы:
  - backend contract tests for enriched payloads;
  - frontend integration tests for degraded/mobile/badge states;
  - Playwright split by persona and device class;
  - mandatory sync rule for `memory-bank` and `docs_fuelsight`.
- Зависимости:
  - all previous slices;
  - stable documentation discipline.
- Проверка:
  - следующая сессия может продолжиться без новой разведки;
  - code, docs and demo story больше не расходятся.

## Scope Guardrails
- Не добавлять multi-tenant или публичный SaaS-контур.
- Не вводить `stations`.
- Не менять top-level API groups.
- Не делать LLM критическим dependency для core analytics, import и forecast.
- Не превращать chat в autonomous web agent; целевой паттерн — `stateful verified RAG`.
