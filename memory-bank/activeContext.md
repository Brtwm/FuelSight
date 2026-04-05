# Active Context

## Current State
- Фаза 8 реализована: bonus contour `news + chat` доступен на `/news`.
- Core MVP API-контракты сохранены: `/api/v1/*` и envelope `{ data, error, meta }`.
- Airflow остаётся в режиме task-layer через backend (без HTTP-обхода), DAG-и paused-by-default.

## Recently Completed
- Реализованы backend роуты и домены:
  - `GET /api/v1/news/digests/latest`
  - `GET /api/v1/news/search`
  - `POST /api/v1/news/refresh`
  - `POST /api/v1/chat/sessions`
  - `GET /api/v1/chat/sessions/{session_id}/messages`
  - `POST /api/v1/chat/sessions/{session_id}/messages`
- Добавлена миграция NLP/chat таблиц:
  - `news_raw`, `news_digests`, `chat_sessions`, `chat_messages`.
- Обновлён frontend `/news`:
  - digest panel с раскрытием источников;
  - поиск новостей с переходом к материалу;
  - чат с обязательным блоком citations;
  - `LLM off` поведение синхронизировано с backend status.
- Расширено тестовое покрытие:
  - API/service тесты по `news/chat`;
  - сквозной Phase 8 API flow test;
  - frontend component/API/urlFilter tests для news/chat.

## Active Decisions
- LLM/news/chat остаётся bonus contour и не блокирует core MVP.
- При `LLM off` digest/search остаются доступными; chat generation возвращает `503`.
- Источники в чате обязательны: ответы без citations считаются невалидными.
- Источник новостей в базовом варианте: `GDELT` (fixture-driven для локального MVP).

## Risks To Remember
- Dev JWT secret остаётся демонстрационным (`change-me`), для production-like демо нужен ключ >= 32 символов.
- Airflow image сборка остаётся тяжёлой по времени на свежей машине.
- Frontend bundle size warning остаётся и будет закрываться на hardening-фазе.
