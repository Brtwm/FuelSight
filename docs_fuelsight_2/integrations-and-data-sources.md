# Integrations And Data Sources

## Принцип
Все внешние интеграции в v2 работают по схеме `real provider + local cache/snapshots`.  
Сеть и ключи улучшают качество, но не должны ломать защиту диплома.

## Слои данных
| Слой | Что хранится | Primary mode | Fallback mode |
|---|---|---|---|
| Internal facts | `sales_daily`, `purchases_daily` | CSV/XLSX import или initial data generator | локальные файлы / last known state |
| External indicators | нефть, FX, wholesale signals, календарь, события | HTTP adapters + `external_indicators_daily` | cached snapshots |
| News | сохранённые новости и digest | public feeds + normalized cache | last successful ingest |
| LLM | генерация digest/chat | OpenAI-compatible cloud adapter | local LLM или retrieval-only |

## External Indicators v2
- Минимальный набор индикаторов:
  - `crude_brent_usd`;
  - `usd_rub`;
  - `wholesale_gasoline_index`;
  - `wholesale_diesel_index`;
  - `holiday_flag`;
  - `event_pressure_score`.
- Гранулярность: `day x indicator`.
- Назначение:
  - генерация начальной истории;
  - feature store;
  - графические benchmark/reference overlays;
  - объяснения прогноза и маржинальных скачков.

## Таблица `external_indicators_daily`
- Обязательные поля:
  - `indicator_date`;
  - `indicator_code`;
  - `value_numeric`;
  - `unit`;
  - `provider_name`;
  - `provider_mode`;
  - `cache_key`;
  - `ingested_at`;
  - `metadata_json`.
- Правила:
  - уникальность по `indicator_date + indicator_code + provider_name`;
  - last-good snapshot разрешён для defense mode;
  - provider mode фиксируется как `live`, `cached`, `manual_snapshot`.

## Regime-Aware Generator Inputs
- История продаж/закупок должна зависеть не только от случайных шоков, но и от:
  - сезонности по продукту;
  - межпродуктовой каннибализации/совместной динамики;
  - нефти и FX;
  - событийного каталога;
  - лагированного passthrough закупки в розницу.

## LLM Provider Strategy
- Cloud-first:
  - использовать OpenAI-compatible adapter при наличии ключа;
  - все ответы маркировать `provider_mode=cloud_llm`.
- Local fallback:
  - если cloud недоступен, пробовать local adapter;
  - mode маркируется `local_llm`.
- Safe fallback:
  - если генерация недоступна, отдавать `retrieval_only` summary с citations;
  - mode маркируется `retrieval_only`.

## Cache And Snapshot Rules
- Для каждого внешнего провайдера нужен локальный cache directory.
- Используется TTL + last-good snapshot.
- Network failure не должен приводить к пустому UI без понятного explanation.
- Admin может вручную refresh-ить источники, analyst только читает результат и видит freshness.
