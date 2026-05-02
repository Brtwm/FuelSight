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
| LLM | synthesis для digest/chat по evidence pack | OpenAI-compatible cloud adapter (`NeuralDeep` first demo profile) | `GigaChat` alternative, local LLM или retrieval-only |

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
- Архитектурный принцип:
  - retrieval и citations первичны;
  - LLM получает только `evidence pack`, собранный backend;
  - runtime web search и autonomous agent loop запрещены;
  - ответ без citations считается невалидным независимо от provider.
- Cloud-first:
  - использовать provider-neutral adapter interface;
  - первым cloud profile считать `NeuralDeep` как OpenAI-compatible endpoint для chat, embeddings и reranker;
  - `GigaChat` оставить альтернативным cloud provider через отдельный adapter;
  - все cloud-ответы маркировать `provider_mode=cloud_llm`.
- NeuralDeep profile:
  - `base_url=https://api.neuraldeep.ru/v1`;
  - chat model по умолчанию: `gpt-oss-120b`;
  - embedding model по умолчанию: `bge-m3` или `e5-large`;
  - reranker model по умолчанию: `bge-reranker`;
  - использовать только для агрегированных snippets/evidence pack, без сырых fact tables и ПДн.
  - профиль активируется только при `ENABLE_LLM=true`, `LLM_PROVIDER_MODE=cloud_first`, `LLM_PROVIDER=neuraldeep` и наличии `LLM_API_KEY`;
  - `LLM_OPENAI_COMPAT_BASE_URL`, `LLM_CHAT_MODEL`, `LLM_EMBEDDING_MODEL`, `LLM_RERANKER_MODEL` всегда могут переопределить defaults.
- GigaChat profile:
  - использовать как второй cloud adapter, если выбран в конфиге;
  - сохранить тот же product contract: `answer + citations + confidence + mode`;
  - provider-specific auth и request shape изолировать внутри adapter.
  - в Phase I adapter получает OAuth token по `GIGACHAT_AUTH_KEY`, кеширует token до expiry, вызывает `/chat/completions` и `/embeddings`;
  - reranker endpoint для GigaChat не считается доступным контрактом, поэтому rerank мягко деградирует к local scoring.
- Local fallback:
  - если cloud недоступен, пробовать local adapter;
  - mode маркируется `local_llm`.
- Safe fallback:
  - если генерация недоступна, отдавать `retrieval_only` summary с citations;
  - mode маркируется `retrieval_only`.
- Quality layer:
  - embeddings/reranker являются optional accelerators качества, а не hard dependency;
  - cloud embeddings нормализуются к текущему `rag_chunks.embedding = vector(64)`, чтобы Phase I не требовала migration под размерность конкретного provider;
  - при их недоступности retrieval обязан деградировать до lexical/rule-based search;
  - confidence рассчитывается из retrieval/rerank signals, freshness и source coverage, а не из свободной оценки LLM.

## Cache And Snapshot Rules
- Для каждого внешнего провайдера нужен локальный cache directory.
- Используется TTL + last-good snapshot.
- Network failure не должен приводить к пустому UI без понятного explanation.
- Admin может вручную refresh-ить источники, analyst только читает результат и видит freshness.
