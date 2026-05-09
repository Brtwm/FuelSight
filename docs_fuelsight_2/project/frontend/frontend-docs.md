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
- Визуальный baseline: `Cinematic Dark` control-room UI с графитовым canvas, subtle grid/noise, cyan для аналитических сигналов, amber для риска/active states, green/red для маржи и аномалий.
- Шрифты: `Unbounded` только для бренда/крупных заголовков, `IBM Plex Sans` для интерфейса, `JetBrains Mono` для чисел и таблиц.
- Все analyst-facing страницы получают единый блок:
  - business summary;
  - freshness/status badges;
  - explainable empty state;
  - retry/degraded messaging.
- User-facing badges локализованы: `Данные: свежие`, `Модель: проверить`, `Индикаторы: кэш`; raw `n/a`, `provider_mode`, `source_type` не выводятся.
- `AppShell` не показывает global diagnostics/status row; freshness/provider/LLM badges живут в контексте конкретной страницы или chart/card.

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
- `volume/forecast`: signal cyan
- `retail_price/risk accent`: amber
- `purchase_price`: amber muted line
- `margin`: green
- `baseline`: neutral gray
- `scenario`: green/cyan contrast
- `anomaly`: red
- `reference/benchmark`: dashed muted violet/steel

### Обязательные визуальные элементы
- `reference bands` для порогов маржи и нормальных диапазонов;
- `markLine`/`markArea` для ключевых событий;
- выделение аномалий точками и подписями;
- benchmark overlays для внешних индикаторов, если они доступны;
- badges рядом с chart title показывают русские labels (`актуально`, `кэш`, `снимок`, `свежие`, `устарели`).

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
