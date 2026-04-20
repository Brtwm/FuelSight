# Feature: Procurement And Margin Analytics v2

## Обзор
- Назначение: показывать маржу как управляемый бизнес-риск, а не просто как ещё одну серию на графике.
- Точка входа: `/analytics/margin`
- Пользователь: `admin`, `analyst`
- Owners:
  - frontend: risk bands, linked anomalies, reason panels
  - backend: margin aggregates, threshold metadata, event refs

## Ключевые изменения v2
- margin chart получает risk/reference bands;
- выделяются дни ниже порога и событие-пояснение;
- summary panel связывает внутренние данные и внешние сигналы;
- при наличии news refs UI может показать supporting context.

## API Requirements
- `GET /api/v1/analytics/margin` возвращает:
  - `series`
  - `threshold_rub_per_liter`
  - `low_margin_days`
  - `meta.explainability.summary`
  - `meta.explainability.chart.annotations`
  - `meta.explainability.chart.overlays`
  - `meta.explainability.chart.thresholds`
  - `meta.explainability.chart.supporting_refs`
  - `meta.explainability.trust` + `meta.explainability.state`

## UX Rules
- день ниже порога должен выделяться и на графике, и в таблице;
- reason panel не должен звучать как data science jargon;
- missing purchase coverage показывается явно.

## Tests
- risk band rendering;
- low-margin selection;
- explanation panel behavior;
- missing purchase state.
