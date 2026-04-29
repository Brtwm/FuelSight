# Feature: News Digest And Chat v2

## Обзор
- Назначение: давать актуальную сводку внешнего контекста и отвечать на вопросы с обязательными citations и прозрачным provider mode.
- Точка входа: `/news`
- Пользователь: `admin`, `analyst`
- Owners:
  - frontend: digest/search/chat UI, provider badges, citations
  - backend: news ingest, digest build, retrieval, LLM fallback ladder

## Ключевые изменения v2
- fixture news заменяются реальным ingest + cache;
- digest строится по реально сохранённым `news_raw`;
- chat mode фиксируется как `cloud_llm`, `local_llm` или `retrieval_only`;
- citations содержат `provider_mode` и `confidence`.
- chat является `stateful verified RAG`, а не агентом с веб-поиском;
- cloud synthesis использует только backend evidence pack.
- Phase H хранит retrieval chunks в `rag_chunks` с `pgvector`, но default path остаётся offline-safe через stable deterministic local embeddings/fallback scoring.

## Provider Strategy
- Первый cloud-enhanced provider: `NeuralDeep` через OpenAI-compatible adapter.
- NeuralDeep удобен для первого demo path, потому что одним API закрывает chat, embeddings и reranker.
- `GigaChat` остаётся альтернативным cloud adapter для русского business tone и provider diversity.
- `local_llm` и `retrieval_only` обязательны для offline-safe защиты.
- В cloud provider отправляются только агрегированные snippets и citations, не сырые продажи/закупки и не ПДн.

## API Requirements
- `GET /api/v1/news/digests/latest`:
  - `provider_mode`
  - `news_freshness`
- `GET /api/v1/news/search`:
  - `provider_mode`
  - `confidence`
- `POST /api/v1/chat/.../messages`:
  - enriched citations with required `provider_mode`, `confidence`, `source_type`;
  - explicit `mode`: `cloud_llm`, `local_llm`, `retrieval_only`;
  - `meta.llm_provider` содержит выбранный provider (`neuraldeep`, `gigachat`, `local`, `none`) и причину деградации.
  - `meta.retrieval` содержит `candidate_count`, `selected_count`, `source_counts`, `reranker_used`, `degradation_reason`.
  - `data.confidence` и `data.verification` показывают retrieval-based confidence и итог final verification pass.

## Retrieval And Answer Flow
```text
question
-> session context resolver
-> lexical retrieval по news/internal refs
-> candidate merge + freshness/domain boost
-> evidence pack
-> final verification pass
-> retrieval-only formatter или future cloud/local synthesis
-> citation guard
-> answer + citations + confidence + mode
-> persist to chat_messages
```

## UX Rules
- digest/search доступны всегда;
- chat при недоступности генерации деградирует до retrieval-only, а не просто падает;
- пользователь всегда видит, в каком режиме получен ответ.
- при слабом evidence pack ответ должен честно говорить, что данных недостаточно.
- Phase G не выполняет agentic web search и не вызывает реальные cloud LLM providers; это остаётся Phase I.

## Tests
- live/cached digest states;
- chat with citations;
- retrieval-only fallback;
- admin refresh flow.
