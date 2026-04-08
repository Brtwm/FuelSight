# Frontend: FuelSight v2

## Назначение
Frontend v2 сохраняет SPA-структуру MVP, но переводит интерфейс из "хорошего учебного макета" в объяснимую аналитическую систему для analyst-first сценария.

## Стек
- `React 19 + Vite + TypeScript`
- `MUI`
- `Apache ECharts`
- `React Router`
- `TanStack Query`
- `React Hook Form + Zod`

## Маршруты
| Route | Назначение | Доступ |
|---|---|---|
| `/login` | analyst-first вход | public |
| `/import` | загрузка начальных данных и diagnostics | admin |
| `/dashboard` | KPI, summaries, freshness badges | admin, analyst |
| `/analytics/sales` | спрос, сезонность, overlays, annotations | admin, analyst |
| `/analytics/margin` | маржа, price spread, risk bands | admin, analyst |
| `/forecast` | base/scenario forecast, model health, baseline comparison | admin, analyst |
| `/news` | digest, search, citations, chat | admin, analyst |

## Analyst-First UX Rules
- Логин по умолчанию предзаполнен analyst-учёткой.
- Analyst не видит технический жаргон про synthetic/demo data.
- Все analyst-facing страницы получают единый блок:
  - business summary;
  - freshness/status badges;
  - explainable empty state;
  - retry/degraded messaging.

## Chart Design System
### Общие правила
- каждый аналитический chart рендерится в едином `ChartCard`;
- обязательно есть:
  - заголовок;
  - короткий business summary;
  - legend с понятными названиями;
  - локализованные форматтеры осей;
  - tooltip с деловым текстом;
  - явные empty/loading/error states.

### Цветовая система
- `volume`: navy
- `retail_price`: amber
- `purchase_price`: brown/orange
- `margin`: green
- `baseline`: neutral gray
- `scenario`: teal
- `anomaly`: red
- `reference/benchmark`: dashed muted blue/gray

### Обязательные визуальные элементы
- `reference bands` для порогов маржи и нормальных диапазонов;
- `markLine`/`markArea` для ключевых событий;
- выделение аномалий точками и подписями;
- benchmark overlays для внешних индикаторов, если они доступны;
- badges рядом с chart title: `live`, `cached`, `degraded`.

## Shared Components v2
- `ChartCard`
- `BusinessSummaryCard`
- `DataStatePanel`
- `FreshnessBadgeGroup`
- `ModelFreshnessBadge`
- `CitationList`
- `SourceModeBadge`
- `DiagnosticsDrawer` для admin-only проблем данных/интеграций

## Import UX v2
- User-facing copy использует язык `начальные данные`, `история`, `обновление данных`.
- Технические значения `historical_data` и `generated` остаются только в backend/logging/admin diagnostics.
- Analyst не имеет доступа к `/import`, но empty states на аналитических страницах объясняют, что требуется initial data.

## Тестирование Frontend
- unit: formatters, chart config builders, badges, form defaults;
- integration: analyst-first login, URL filters, neutral import language, degraded states;
- e2e: analyst flow и отдельно admin operational flow.
