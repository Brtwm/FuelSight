# Operability And Defense Mode

## Цель
FuelSight должен выглядеть как управляемый внутренний продукт, а не как набор разрозненных страниц. Для этого нужен режим защиты, который воспроизводимо поднимает данные, модель, новости и проверки состояния.

## Operating Modes
### `offline-safe`
- без обязательного доступа к сети;
- использует local snapshots и last-good caches;
- chat деградирует до `retrieval_only` без hard failure, если сохранённый evidence доступен;
- подходит для нестабильной среды защиты.

### `cloud-enhanced`
- разрешает live ingest внешних индикаторов и news;
- включает cloud LLM при наличии ключа NeuralDeep или GigaChat;
- preferred demo provider: NeuralDeep OpenAI-compatible profile;
- показывает richer digest и более актуальные external signals.

## Defense/Demo Mode
- Основа: расширение существующего `scripts/run_full_demo.py`.
- Цепочка:
  1. health checks;
  2. seed users/products;
  3. initial data ingest or generation;
  4. external indicators refresh;
  5. feature store refresh;
  6. CatBoost retrain/backtest;
  7. news refresh;
  8. API smoke;
  9. optional browser E2E;
  10. legacy technical report artifact generation through `build-defense-report`.
- Итог: machine-readable JSON + human-readable summary для оператора. В UI
  бизнес-функция отчета называется `Управленческий отчет` и доступна на
  `/reports/executive`.

## What Defense/Demo Mode Must Produce
- статус по каждому шагу;
- data coverage summary;
- model freshness summary;
- active provider modes;
- выбранный LLM provider (`neuraldeep`, `gigachat`, `local`, `none`) и итоговый answer mode;
- список деградаций, если live integrations недоступны;
- ссылки на основные артефакты и last report.

## Visible Badges In UI
- `Data Freshness`
- `Model Freshness`
- `LLM Mode`
- `News Freshness`
- `External Indicators Mode`

## Data Quality Scorecard
- метрики:
  - покрытие периода по каждому продукту;
  - пропуски закупки/продаж;
  - доля fallback indicator points;
  - количество аномалий в initial data;
  - дата последнего retrain;
  - качество winner model против baseline.

## Executive Output
- One-page export/PDF должен включать:
  - KPI summary;
  - 1 chart по продажам;
  - 1 chart по марже;
  - forecast summary;
  - свежесть модели;
  - ключевые новости/источники;
  - короткий decision journal.

## Acceptance Criteria
- Один запуск defense/demo mode приводит систему в готовое к показу состояние.
- При отсутствии сети система продолжает работать, явно показывая fallback badges.
- Ни один критичный шаг не завершается "тихой" ошибкой: только `ok`, `warning`, `degraded`, `failed`.
- В `offline-safe` профиле `/news` и chat доступны через `retrieval_only`.
- LLM-off smoke ожидает `200` cited chat answer, а не `503 llm_disabled`.
- В `cloud-enhanced` профиле отказ NeuralDeep/GigaChat не ломает demo story, а фиксируется как controlled degradation.
