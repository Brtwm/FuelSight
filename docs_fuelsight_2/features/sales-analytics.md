# Feature: Sales Analytics v2

## Обзор
- Назначение: объяснять динамику спроса через временной ряд, сезонность, аномалии и внешние benchmark overlays.
- Точка входа: `/analytics/sales`
- Пользователь: `admin`, `analyst`
- Owners:
  - frontend: filters, chart system, anomaly interactions
  - backend: sales series, annotations, summaries, overlays

## Ключевые изменения v2
- единый chart card вместо простого bar+line блока;
- business summary над или под графиком;
- аномалии и события помечаются аннотациями;
- если доступны external indicators, они показываются как muted overlays;
- UI явно показывает `live/cached/degraded` mode.

## API Requirements
- `GET /api/v1/analytics/sales` возвращает:
  - `series`
  - `seasonality`
  - `comparisons`
  - `meta.business_summary`
  - `meta.chart_annotations`
  - `meta.reference_overlays`
  - `meta.data_mode`

## UX Rules
- YoY, если недоступен, показывается как объяснимый `N/A`;
- anomaly click подсвечивает контекст и может вести в related view;
- period and granularity stay URL-synced.

## Tests
- chart overlays rendering;
- annotation rendering;
- degraded mode badge;
- short-history behavior.
