# Frontend: FuelSight

## Назначение
Frontend FuelSight — SPA-приложение для внутренней аналитики продаж, закупок, маржи и прогнозов по нефтепродуктам. Интерфейс должен быть понятным бизнес-пользователю, а не только разработчику или data scientist, поэтому визуально приоритетны панели KPI, графики, таблицы с фильтрами и короткие текстовые пояснения.

## Стек
- Framework: `React 19 + Vite`
- Language: `TypeScript`
- Routing: `React Router`
- UI Kit: `MUI`
- Charts: `Apache ECharts`
- Server State: `TanStack Query`
- Forms: `React Hook Form + Zod`
- Package Manager: `pnpm`
- Dev Port: `3000`

## Основные пользовательские маршруты
| Route | Назначение | Доступ |
|---|---|---|
| `/login` | Вход в систему | public |
| `/import` | Импорт продаж, закупок и демо-данных | admin |
| `/dashboard` | KPI и общие алерты | admin, analyst |
| `/analytics/sales` | Аналитика продаж и спроса | admin, analyst |
| `/analytics/margin` | Закупки, маржа, аномалии | admin, analyst |
| `/forecast` | Прогноз и what-if сценарии | admin, analyst |
| `/news` | Новостная сводка и чат | admin, analyst |

## Структура проекта
```text
frontend/
├── src/
│   ├── app/
│   │   ├── providers/
│   │   ├── router/
│   │   └── layout/
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── ImportPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── SalesAnalyticsPage.tsx
│   │   ├── MarginAnalyticsPage.tsx
│   │   ├── ForecastPage.tsx
│   │   └── NewsPage.tsx
│   ├── features/
│   │   ├── auth/
│   │   ├── import/
│   │   ├── kpi/
│   │   ├── sales/
│   │   ├── margin/
│   │   ├── forecast/
│   │   └── news/
│   ├── components/
│   │   ├── layout/
│   │   ├── charts/
│   │   ├── tables/
│   │   └── common/
│   ├── lib/
│   │   ├── api/
│   │   ├── auth/
│   │   └── utils/
│   ├── types/
│   └── theme/
└── public/
```

## UI-паттерны
- После логина используется responsive shell-layout:
  - desktop: `permanent drawer + top bar`;
  - mobile/tablet: `temporary drawer + bottom navigation` для analyst key routes.
- Все страницы с данными поддерживают состояния `loading`, `empty`, `error`, `ready`.
- Фильтры, влияющие на аналитические графики, синхронизируются с query-параметрами URL.
- Таблицы и графики должны быть согласованы по выбранному продукту и периоду, без скрытых локальных фильтров.
- Текстовые пояснения формулируются по-русски и избегают терминов уровня “feature importance” без интерпретации.

## Ключевые компоненты
- `AppShell`: responsive navigation shell с `permanent drawer` на desktop и `bottom navigation + temporary drawer` на mobile.
- `ProtectedRoute`: защита приватных маршрутов и проверка ролей.
- `FilterBar`: общий паттерн фильтров по продукту, периоду и горизонту.
- `KpiCardGrid`: карточки KPI на главном экране.
- `TimeseriesChartCard`: контейнер для ECharts с единым стилем и легендой.
- `AlertTable`: табличный список аномалий и низкой маржи.
- `ForecastDriversPanel`: карточки драйверов прогноза простым языком.
- `CitationList`: список ссылок на новости и внутренние источники для чата.

## Управление состоянием
- Серверные данные: только через `TanStack Query`.
- Формы и пользовательский ввод: `React Hook Form + Zod`.
- Состояние сессии: access token в памяти приложения, обновление сессии через refresh-cookie.
- Cross-page state: query-параметры URL и минимальный `auth` store.
- Не использовать глобальное состояние для аналитических данных, если достаточно query cache.

## Визуальные требования
- Основной стиль: нейтральный enterprise-интерфейс без маркетингового лендинга.
- MUI theme должен использовать спокойную палитру с акцентами для статусов:
  - `success` для устойчивой маржи;
  - `warning` для пограничных значений;
  - `error` для аномалий и критических алертов.
- ECharts используется для временных рядов, stacked bar, heatmap сезонности и доверительных интервалов прогноза.
- Для малой ширины применяется mobile chart rule-set:
  - сокращённые legend labels;
  - скрытие второстепенных серий (interval/overlays) по умолчанию через legend toggle;
  - краткий summary над графиком;
  - компактные grid/axis paddings.
- Для `/forecast` на mobile используется карточечное представление значений прогноза вместо широкой таблицы.

## Команды
- `pnpm install`
- `pnpm dev --host 0.0.0.0 --port 3000`
- `pnpm build`
- `pnpm lint`
- `pnpm test`
- `pnpm test:e2e`
- `pnpm exec playwright install chromium` (one-time on fresh machine before `test:e2e`)

## Environment Variables
```env
VITE_API_BASE_URL=http://localhost:8061/api/v1
VITE_APP_PORT=3000
VITE_ENABLE_LLM=false
VITE_ENABLE_DEMO_CREDENTIALS=true
VITE_DEFAULT_PRODUCT=AI_95
```
- `VITE_ENABLE_DEMO_CREDENTIALS=false` отключает автозаполнение демо-логина на `/login`;
  для локальной защиты значение по умолчанию остаётся `true`.

## Интеграция с backend
- Все ответы API используют единый envelope: `{ "data": ..., "error": null, "meta": {...} }`.
- Ошибки `401` переводят пользователя в refresh flow; при неуспехе — на `/login`.
- Ошибки `403` показываются как access denied state без бесконечных retries.
- Страницы импорта и администрирования недоступны роли `analyst`.

## Тестирование frontend
- Unit: UI-состояния, форматирование KPI, валидация форм.
- Integration: навигация по защищённым маршрутам, query-параметры фильтров, успешные и неуспешные загрузки файлов.
- Component visual checks: карточки KPI, графики временных рядов, forecast panel.
- E2E (Playwright):
  - `desktop-analyst`: analyst flow `login -> dashboard -> sales -> margin -> forecast -> news`;
  - `desktop-admin`: admin flow `login -> import -> initial-history refresh -> diagnostics`;
  - `mobile-iphone-13` и `mobile-pixel-7`: mobile smoke `login -> dashboard -> forecast -> news`.
- Mobile screenshots сохраняются в `frontend/output/playwright/` и используются как defense-артефакт.
- Mandatory sync rule: если UI state, status badge, degraded behavior или demo route меняется в коде, синхронно обновляются `memory-bank/*`, соответствующий документ в `docs_fuelsight/*` и `docs_fuelsight_2/phase0-gap-matrix.md`.

## Связанные документы
- Общее видение: `@docs_fuelsight/project-idea.md`
- Маркетинговый контекст: `@docs_fuelsight/marketing/go-to-market.md`
- Общая серверная архитектура: `@docs_fuelsight/project/backend/backend-docs.md`
- Спецификации экранов и поведения: `@docs_fuelsight/features/`
- ASCII-схемы UI: `@docs_fuelsight/screens/`
