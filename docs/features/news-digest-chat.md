# Feature: News Digest and Chat

## Обзор
- **Назначение**: показывать краткую сводку новостей по факторам, влияющим на цены нефтепродуктов, и отвечать на вопросы пользователя через RAG-интерфейс с обязательными ссылками на источники.
- **Пользователь**: `admin`, `analyst`, `director` для frontend `/news`;
  backend также разрешает digest/search роли `sales`, но UI не показывает
  sales как news/RAG persona.
- **Точка входа**: `/news`.
- **Связанные фичи**: `sales-analytics`, `procurement-margin`, `demand-forecast`.
- **Статус в MVP**: бонусный модуль, non-blocking для первого релиза.

## User Flow
1. Пользователь открывает страницу `/news`.
2. Сначала видит последнюю дневную или недельную сводку новостей.
3. При желании раскрывает источники и переходит к отдельным новостям.
4. `admin` или `analyst` задаёт вопрос в чат-интерфейсе.
5. Система выполняет retrieval по внутренним данным и новостным материалам.
6. Пользователь получает ответ с citations на новости и внутренние аналитические ref id.
7. Для `director` демонстрационный сценарий ограничен digest/search и рыночным
   контекстом; backend chat actions этой роли не разрешены.
8. Если LLM отключён, страница остаётся доступной в режиме `digest + поиск`, а chat возвращает `retrieval_only` ответ с citations либо честный blocked uncertainty при нехватке источников.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Loading | Загружается digest | Skeleton карточек |
| DigestReady | Сводка доступна | Bullet points и блок источников |
| ChatReady | Сессия создана | История сообщений и input |
| LlmOff | Генеративный режим выключен | Badge `LLM off`, digest и поиск остаются |
| NoNews | Новостей нет | Placeholder и кнопка refresh для admin |
| Error | Ошибка запроса | Alert и retry |

## Ключевые компоненты

### `NewsPage`
- **Расположение**: `src/pages/NewsPage.tsx`
- **Поведение**: двухколоночный layout со сводкой и чатом.

### `NewsDigestPanel`
- **Расположение**: `src/features/news/components/NewsDigestPanel.tsx`
- **Поведение**: показывает summary, bullet points, `context_story` (indicator/event refs, quality/fallback) и ссылки на источники.

### `NewsSearchDrawer`
- **Расположение**: `src/features/news/components/NewsSearchDrawer.tsx`
- **Поведение**: поиск по новостям и просмотр выбранного материала.

### `ChatThread`
- **Расположение**: `src/features/news/components/ChatThread.tsx`
- **Поведение**: история сообщений с блоком citations; отправка сообщений
  поддерживается backend-ролями `admin` и `analyst`.

### `CitationList`
- **Расположение**: `src/features/news/components/CitationList.tsx`
- **Поведение**: список источников по каждому ответу.

## API-контракты

### `GET /api/v1/news/digests/latest`
- **Авторизация backend**: `admin`, `sales`, `analyst`, `director`
- **Frontend route**: `admin`, `analyst`, `director`
- **Query Params**: `period_type=daily|weekly`
- **Response 200**:
```json
{
  "data": {
    "digest_date": "2026-03-28",
    "period_type": "daily",
    "summary_text": "Рост оптовых индикаторов и логистические ограничения создают давление на закупочные цены.",
    "bullet_points": [
      "усилилось давление на поставки ДТ",
      "курс валюты остаётся фактором риска"
    ],
    "source_ids": ["news_1", "news_2"],
    "provider_mode": "cached",
    "news_freshness": "fresh",
    "context_story": {
      "window": { "start_date": "2026-03-28", "end_date": "2026-03-28" },
      "external_context": {
        "provider_mode": "cached",
        "coverage_ratio": 0.94,
        "fallback_ratio": 0.22,
        "quality_status": "warning",
        "reasons": ["coverage_ratio=0.940<0.95"],
        "manifest_run_date": "2026-03-28",
        "source_refs": []
      },
      "event_context": [],
      "indicator_refs": [],
      "event_refs": []
    }
  },
  "error": null,
  "meta": {}
}
```

### `GET /api/v1/news/search`
- **Авторизация backend**: `admin`, `sales`, `analyst`, `director`
- **Frontend route**: `admin`, `analyst`, `director`
- **Query Params**: `q`, `date_from`, `date_to`, `topic`

### `POST /api/v1/news/refresh`
- **Авторизация**: `admin`
- **Назначение**: принудительный запуск сбора новостей и digest.

### `POST /api/v1/chat/sessions`
- **Авторизация**: `admin`, `analyst`
- **Request Body**:
```json
{
  "title": "Почему в феврале упали продажи ДТ?"
}
```

### `GET /api/v1/chat/sessions/{session_id}/messages`
- **Авторизация**: `admin`, `analyst`

### `POST /api/v1/chat/sessions/{session_id}/messages`
- **Авторизация**: `admin`, `analyst`
- **Request Body**:
```json
{
  "question": "Покажи факторы по росту закупочных цен за 14 дней",
  "context_scope": ["internal_analytics", "news_digest"]
}
```
- **Response 200**:
```json
{
  "data": {
    "answer": "Рост закупочной цены за последние 14 дней связан с внешним новостным фоном и повышением индикативных значений.",
    "citations": [
      {
        "type": "news",
        "ref_id": "news_2026_03_24_02",
        "title": "Логистические ограничения на поставки"
      },
      {
        "type": "chart",
        "ref_id": "analytics_margin_ai95_2026_03",
        "title": "График закупочной цены AI-95"
      }
    ],
    "mode": "llm"
  },
  "error": null,
  "meta": {}
}
```

## Модель данных
- Основные таблицы: `news_raw`, `news_digests`, `chat_sessions`, `chat_messages`, `rag_chunks`.
- Дополнительный локальный артефакт: файловый индекс новостей для retrieval.

## Frontend-требования
- Всегда показывать citations рядом с ответом ассистента.
- При `LLM off` скрывать input чата только если retrieval-ответы полностью недоступны; digest и поиск должны остаться.
- Визуально отделять сгенерированный ответ от списка источников.
- Даже в fallback/offline режиме `context_story` должен оставаться непустым за счёт локальных artifacts.

## Backend-требования
- Retrieval обязан работать по внутренним ref id и по новостям.
- Ответ без citations не считается валидным.
- При выключенном LLM backend должен возвращать retrieval-grounded ответ при наличии evidence; `503 llm_disabled` сохраняется только как controlled degradation для будущих generation-only режимов.
- Источники новостей в текущем baseline: `GDELT` + curated RSS/API providers (`RBC`, `Kommersant`, `Prime`) через cache/manual snapshot fallback.
- `GET /news/digests/latest` возвращает `context_story` как bridge между news narrative и внешними индикаторами/events.

## Edge Cases
- Новостей за период нет.
- LLM отключён через конфиг.
- Retrieval нашёл релевантные документы, но генерация не запустилась.
- Пользователь задаёт слишком общий вопрос без привязки к продукту.
- Источник новости недоступен по внешней ссылке, но сниппет сохранён локально.

## Тестирование
- API: latest digest, search, refresh-news, create chat session, answer with citations, llm disabled behavior.
- UI: режим `LLM off`, раскрытие источников, отображение citations.
- E2E: пользователь открывает сводку и поиск; retrieval-first chat с ответом при
  `LLM off` проверяется для роли с backend-доступом к chat actions.
