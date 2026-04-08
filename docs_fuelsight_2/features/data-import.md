# Feature: Data Import v2

## Обзор
- Назначение: загрузка продаж, закупок и обновление начальной истории без технического user-facing языка.
- Точка входа: `/import`
- Пользователь: `admin`
- Owners:
  - frontend: import workflow and diagnostics
  - backend: parsing, validation, provenance, quality status

## Ключевые изменения v2
- для пользователя используются термины `начальные данные`, `история`, `обновление`;
- analyst-facing страницы не говорят `demo`, `generated`, `historical_data`;
- provenance остаётся в БД, логах и admin diagnostics;
- import jobs получают нейтральный `display_label`.

## User Flow
1. Admin открывает `/import`.
2. Выбирает загрузку продаж, закупок или обновление начальной истории.
3. Запускает операцию и видит статус/quality summary.
4. При необходимости открывает diagnostics и provenance details.

## UI Sections
- `Продажи`
- `Закупки`
- `Начальная история`
- `Диагностика`

## Frontend Requirements
- заменить тексты про `demo`/`historical_data` на нейтральные;
- job table показывает `display_label`, а не raw `entity_type` там, где это analyst-visible;
- diagnostics drawer доступен только admin.

## Backend Requirements
- path `/api/v1/import/generate-demo` сохраняется;
- response для jobs может содержать `display_label`, `provenance_mode`, `quality_status`;
- importer продолжает поддерживать CSV/XLSX и partial success.

## Tests
- neutral copy in UI;
- admin-only access;
- compatibility with existing endpoint names;
- diagnostics visibility rules.
