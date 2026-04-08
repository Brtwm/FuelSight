# FuelSight v2 Roadmap

## Принцип приоритизации
Сначала усиливается основной analyst flow, затем реализм данных и модели, потом optional, но впечатляющий contour `news + chat + defense mode`.

## Phase 1. Documentation Baseline
- Цель: зафиксировать целевую архитектуру v2 без потери текущего `as-built` описания.
- Выходы:
  - полный `docs_fuelsight_2/`;
  - обновлённый `memory-bank/`;
  - согласованный gap list между текущим кодом и v2.
- Зависимости: текущие `docs_fuelsight/`, `memory-bank/`, кодовая база.
- Проверка: каждая v2-фича связана с API, экраном и backend/domain owner.

## Phase 2. Analyst-First UX And Chart System
- Цель: сделать интерфейс понятным для комиссии и бизнес-пользователя.
- Выходы:
  - analyst-default login;
  - нейтральный import copy;
  - shared chart components, annotations, business summaries, state panels;
  - единые статусные badges для данных, модели и режима LLM.
- Зависимости: frontend design tokens, общие response metadata для analytics/forecasts/news.
- Проверка: analyst проходит основной сценарий без захода в admin-only разделы.

## Phase 3. Initial Data And Data Realism
- Цель: заменить ощущение "учебной синтетики" на правдоподобный historical dataset.
- Выходы:
  - regime-aware generator;
  - длинная история и межпродуктовые зависимости;
  - curated event catalog;
  - cached external indicators для генератора и feature store.
- Зависимости: новая схема `external_indicators_daily`, provider adapters, cache strategy.
- Проверка: генератор выдерживает realism-инварианты и даёт пригодный обучающий набор для CatBoost.

## Phase 4. CatBoost-First Forecasting
- Цель: сделать CatBoost основным прогнозным путём и управляемо сравнивать его с benchmark baseline.
- Выходы:
  - расширенный feature engineering;
  - hyperparameter tuning и retrain cadence;
  - model freshness и baseline comparison в API;
  - раздельные active models по горизонтам `1/7/30`.
- Зависимости: feature store v2, external indicators, richer backtest metadata.
- Проверка: CatBoost выигрывает baseline на majority сценариев либо явно помечается как degraded case.

## Phase 5. External Indicators And Airflow Standardization
- Цель: убрать stub-операции из стандартного pipeline.
- Выходы:
  - daily `ingest_external_indicators`;
  - daily `build_feature_store`;
  - weekly `train_models`;
  - freshness/status артефакты для UI и defense mode.
- Зависимости: provider registry, cache directories, ops runbook.
- Проверка: pipeline проходит как в `cloud-enhanced`, так и в `offline-safe` режиме.

## Phase 6. Real News And Chat
- Цель: заменить fixtures и `template_rag` на реальный ingest + retrieval + fallback ladder.
- Выходы:
  - ingestion news from public sources with cache;
  - digest builder over stored `news_raw`;
  - chat with citations, provider mode and confidence;
  - fallback ladder: `cloud_llm -> local_llm -> retrieval_only`.
- Зависимости: news cache, source normalization, LLM adapter interface.
- Проверка: ни один ответ чата не возвращается без citations.

## Phase 7. Defense Mode And Executive Outputs
- Цель: сделать проект устойчивым и эффектным на защите.
- Выходы:
  - one-click defense profile;
  - data quality scorecard;
  - model freshness badge;
  - one-page export/PDF;
  - short decision journal.
- Зависимости: предыдущие фазы, стабильный smoke chain.
- Проверка: демонстрационный запуск выполняется на свежей машине с предсказуемым деградированием при отсутствии сети или ключей.

## Scope Guardrails
- Не добавлять multi-tenant или публичный SaaS-контур.
- Не вводить `stations`.
- Не менять top-level API groups.
- Не делать LLM критическим dependency для core analytics и forecast.
