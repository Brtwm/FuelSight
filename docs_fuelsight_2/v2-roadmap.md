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
- Текущий статус (2026-05-05): `implemented` для `login/dashboard/forecast/news` и `AppShell`; desktop persona regression и dual mobile smoke проходят через split Playwright projects.
- Выходы:
  - responsive `AppShell` без desktop-only permanent drawer на малых экранах;
  - mobile-first layout для `/dashboard`, `/forecast`, `/news`;
  - компактные filters, карточечные таблицы, сокращённые legends/tooltips;
  - отдельный mobile Playwright profile (`iphone-13`, `pixel-7`) и visual smoke со screenshot artifacts.
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
  - согласованная подача `annotations`, `overlays`, `thresholds`, `supporting refs`;
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
- Текущий статус (2026-04-20): `implemented`.
- Выходы:
  - правдоподобная initial history с межпродуктовым контекстом;
  - curated event catalog как часть explainability;
  - quality/fallback metrics для external indicators;
  - устойчивый pipeline для `external_indicators_daily`.
- Реализовано в коде:
  - `event_catalog` как DB-managed curated asset (migration + seed + repository/service);
  - manifest-first quality/fallback semantics (`ok|warning|degraded|failed`) для external ingest/feature/train artifacts;
  - единый `external_context` контракт в KPI/analytics/forecast/news payloads;
  - full UI overlays для analytics/forecast (indicator lines + event markers/bands) и context-aware digest story;
  - offline-safe controlled degradation (`cached/last_good/manual_snapshot`) без пустых ответов.
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
- Текущий статус (2026-05-05): `implemented` для retrieval-first backend/API/UI baseline; provider-neutral cloud/local synthesis подключён поверх evidence pack в Phase I.
- Product decision: сначала строится не LLM-интеграция, а устойчивый retrieval-first контракт. Генерация подключается только поверх evidence pack и не имеет права добавлять факты без citations.
- Выходы:
  - session-aware retrieval по `news_raw`, `news_digests`, `kpi`, `analytics`, `forecast` реализован lexical/rule-based baseline;
  - unified citations с `provider_mode`, `confidence`, `source_type` возвращаются в chat API и UI;
  - mode ladder contract `cloud_llm -> local_llm -> retrieval_only` реализован как resolver, без реальных cloud вызовов;
  - `LLM off` больше не даёт hard failure по умолчанию: chat возвращает cited `retrieval_only` answer при наличии evidence.
  - добавлен Airflow DAG `refresh_news_daily`, закрывающий Phase F orchestration gap.
- Зависимости:
  - real news ingest;
  - citation contracts;
  - LLM adapter interface.
- Проверка:
  - ни один chat answer не возвращается без citations;
  - even degraded mode still returns useful retrieval-grounded answer.

## Phase H. Advanced RAG Quality Layer
- Цель: сделать chat сильной feature диплома без перехода к нестабильному autonomous-agent паттерну.
- Текущий статус (2026-05-05): `implemented` для offline-safe verified retrieval baseline; provider registry, deterministic fallback, cloud embeddings boundary and rerank fallback покрыты Phase I tests.
- Выходы:
  - query normalization и optional rewrite;
  - hybrid retrieval + rerank;
  - dense retrieval по chunks через cloud/local embeddings provider;
  - lexical/BM25-like retrieval по `title`, `snippet`, `full_text` и internal refs;
  - rule-based boost для свежих и domain-relevant материалов;
  - session memory / short running summary;
  - evidence pack как единственный источник для answer synthesis;
  - final verification pass перед выдачей ответа;
  - confidence scoring по retrieval signals, а не только по генерации.
- Реализовано в текущем worktree:
  - `pgvector` runtime baseline через compose image и migration `rag_chunks`;
  - deterministic local embedding fallback для chunks;
  - query normalization с product aliases и date hints;
  - lexical/dense/rule boosted candidate scoring;
  - session running summary;
  - final verification metadata and blocked uncertainty response.
- Зависимости:
  - базовый RAG core;
  - persisted chat sessions/messages;
  - deterministic evidence pack pipeline.
- Проверка:
  - ответы стали точнее, короче и честнее в uncertainty cases;
  - verification умеет блокировать unsupported answer.

## Phase I. Cloud LLM Primary + Provider-Neutral Fallback
- Цель: использовать облачную русскоязычную модель как основной demo path, но не завязывать продукт на одного поставщика.
- Provider decision:
  - primary adapter type: `OpenAI-compatible`;
  - first demo provider: `NeuralDeep`, если доступен API key;
  - alternative cloud provider: `GigaChat` через отдельный native adapter;
  - local adapter остаётся fallback-слоем;
  - крайний режим всегда `retrieval_only`.
- Почему `NeuralDeep` как первый demo provider:
  - один OpenAI-compatible endpoint для chat, embeddings и reranker;
  - удобнее для Phase H, где нужны dense retrieval и rerank;
  - RU-hosted cloud path хорошо подходит для защиты без VPN/geoblock narrative.
- Ограничение:
  - NeuralDeep используется как cloud-enhanced профиль, а не как фундамент продукта;
  - в cloud provider нельзя отправлять сырые таблицы продаж/закупок или персональные данные, только агрегированные snippets/evidence pack;
  - из-за beta/as-is характера провайдера `offline-safe` и `retrieval_only` остаются обязательными.
- Выходы:
  - provider-agnostic `LLM adapter` abstraction;
  - `OpenAI-compatible` adapter with configurable `base_url`, `api_key`, `chat_model`, `embedding_model`, `reranker_model`;
  - `NeuralDeep` cloud profile;
  - `GigaChat` alternative provider plan/adapter boundary;
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
  - `offline-safe` profile uses stored news/cache and `retrieval_only`;
  - `cloud-enhanced` profile can use `NeuralDeep` or `GigaChat` when the corresponding key is present;
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
