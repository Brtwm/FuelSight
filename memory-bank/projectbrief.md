# Project Brief

## Project
- Название: `FuelSight`
- Тип: внутренний локальный дипломный MVP
- Формат: web-система для анализа продаж, закупок, маржи и прогноза спроса на нефтепродукты

## Problem Statement
- Небольшие компании, работающие с топливом, часто ведут продажи, закупки и ценовой анализ в `Excel + 1C + ручных заметках`.
- Такой процесс плохо масштабируется, плохо объясняет причины изменений и затрудняет прогнозирование спроса.
- Для дипломного проекта нужен воспроизводимый, защищаемый и при этом practically useful стенд.

## Goal
- Собрать локальную систему, которая:
  - импортирует продажи и закупки;
  - строит KPI и аналитику;
  - рассчитывает маржу и аномалии;
  - строит прогноз спроса на `1/7/30` дней;
  - опционально показывает новостную сводку и RAG-чат с источниками.
- Параллельно держать две линии документации:
  - `docs_fuelsight/` как `as-built` описание текущего MVP;
  - `docs_fuelsight_2/` как целевую спецификацию улучшенной версии.

## Scope Of V1
- Одна точка продаж, без сущности `stations` в `v1`.
- Роли: `admin`, `analyst`.
- MVP-маршрут: `login -> import/demo-data -> dashboard -> sales analytics -> margin analytics -> forecast`.
- NLP/LLM-контур бонусный и non-blocking.

## Success Criteria
- Есть согласованный комплект документации для дальнейшей реализации.
- Архитектура выглядит production-like, но остаётся реалистичной для локального запуска.
- Система может работать как с импортом CSV/XLSX, так и с учебной синтетикой.
- Пользователь получает понятные объяснения, а не только сырые ML-выходы.
- Улучшенная версия описана decision-complete: UX, API, data, ML, Airflow и defense mode связаны между собой.

## Primary Documentation
- `docs_fuelsight/project-idea.md`
- `docs_fuelsight/as-built-baseline.md`
- `docs_fuelsight_2/project-idea.md`
- `docs_fuelsight_2/v2-roadmap.md`
- `docs_fuelsight_2/phase0-gap-matrix.md`
- `docs_fuelsight_2/integrations-and-data-sources.md`
- `docs_fuelsight_2/operability-and-defense-mode.md`
- `docs_fuelsight/marketing/go-to-market.md`
- `docs_fuelsight/project/frontend/frontend-docs.md`
- `docs_fuelsight/project/backend/backend-docs.md`
- `AGENTS.md`
