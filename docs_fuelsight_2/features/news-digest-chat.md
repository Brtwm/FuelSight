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

## API Requirements
- `GET /api/v1/news/digests/latest`:
  - `provider_mode`
  - `news_freshness`
- `GET /api/v1/news/search`:
  - `provider_mode`
  - `confidence`
- `POST /api/v1/chat/.../messages`:
  - enriched citations;
  - explicit `mode`.

## UX Rules
- digest/search доступны всегда;
- chat при недоступности генерации деградирует до retrieval-only, а не просто падает;
- пользователь всегда видит, в каком режиме получен ответ.

## Tests
- live/cached digest states;
- chat with citations;
- retrieval-only fallback;
- admin refresh flow.
