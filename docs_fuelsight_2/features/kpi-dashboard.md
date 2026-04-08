# Feature: KPI Dashboard v2

## Обзор
- Назначение: давать быстрый overview по продажам, марже и рискам с понятным бизнес-резюме.
- Точка входа: `/dashboard`
- Пользователь: `admin`, `analyst`
- Owners:
  - frontend: summary cards, badges, chart card
  - backend: KPI aggregates, freshness, summary metadata

## Ключевые изменения v2
- chart design system применяется к snapshot chart;
- рядом с KPI отображаются freshness/status badges;
- backend возвращает `business_summary` и chart annotations;
- analyst empty state объясняет, что нужны начальные данные, без технических подробностей.

## Main Blocks
- KPI cards
- demand snapshot chart
- alert feed
- business summary card
- freshness badge group

## Backend Contract
- `GET /api/v1/kpi/summary`:
  - KPI values;
  - `meta.business_summary`;
  - `meta.data_freshness`.
- `GET /api/v1/kpi/snapshot`:
  - series;
  - `meta.chart_annotations`;
  - `meta.reference_overlays`.

## Tests
- ready/warning/empty states;
- business summary rendering;
- freshness badge rendering;
- navigation from alerts to analytics pages.
