# Feature: Executive Report

## Обзор

- **Назначение**: сформировать `Управленческий отчет` по KPI, марже, прогнозу
  спроса, проблемным продуктам, рыночным факторам и рекомендациям.
- **Пользователь**: `admin`, `analyst`, `director`.
- **Точка входа**: `/reports/executive`.
- **Связанные фичи**: `kpi-dashboard`, `procurement-margin`, `demand-forecast`,
  `news-digest-chat`.

## User Flow

1. Пользователь открывает `/reports/executive`.
2. Нажимает `Сформировать управленческий отчет`.
3. Frontend вызывает `POST /api/v1/reports/executive`.
4. Backend собирает KPI, риски маржи, прогноз спроса и рыночный контекст.
5. Пользователь получает сводку для управленческого просмотра.

## API-контракт

### `POST /api/v1/reports/executive`

- **Авторизация**: `admin`, `analyst`, `director`.
- **Request Body**: опциональные `date_from`, `date_to`.
- **Response 200**: payload с `period`, `kpi`, `executive_summary`,
  `problem_products`, `demand_forecast`, `margin_risks`, `market_context`,
  `recommendations`, `data_quality`.

## Важное различие терминов

Пользовательская функция в UI называется `Управленческий отчет`.
Технический pipeline command `build-defense-report` и artifact
`scripts/last-defense-report.json` сохраняют legacy название для локального
demo runner и не должны использоваться как business-facing название функции.

## Проверки доступа

- `director` видит executive dashboard и может открыть `/reports/executive`.
- `analyst` может сформировать отчет как часть аналитического сценария.
- `admin` имеет доступ для локальной демонстрации и диагностики.
- `sales` и `accounting` не видят пункт меню и получают `403` при прямом переходе.
