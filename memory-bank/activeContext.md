# Active Context

## Current State
- Фаза 4 реализована: backend KPI-контур и frontend dashboard больше не являются заглушками.
- Backend поддерживает `/api/v1/kpi/summary`, `/api/v1/kpi/alerts`, `/api/v1/kpi/snapshot` для ролей `admin` и `analyst`.
- Frontend `/dashboard` показывает карточки KPI, мини-график спроса/цены, ленту алертов, фильтры периода/продукта и empty/error/warning состояния.

## Recently Completed
- Добавлена Alembic-миграция `20260404_0002` с `vw_margin_daily`:
  - grain: `day x product`;
  - средневзвешенная закупочная цена за день;
  - поля маржи и `purchase_data_missing`.
- Реализован `KpiService`:
  - агрегаты summary/snapshot/alerts;
  - `rule + z-score` алерты (`low_margin`, `purchase_spike`, `demand_anomaly`);
  - короткий TTL cache для KPI-ответов;
  - расчёт `gross_margin_*` только по пересечению sales/purchases с мета-полями покрытия.
- Реализован `kpi` API router и dependency wiring.
- Реализован dashboard vertical slice:
  - `KpiSummaryCards`, `DemandSnapshotChart`, `AlertFeed`;
  - локализованное форматирование;
  - переходы в `/analytics/sales` и `/analytics/margin`;
  - фильтры по `AI_92`, `AI_95`, `DT_S`, `DT_W`.
- Синхронизированы docs:
  - добавлен `kpi/snapshot`;
  - зафиксированы коды `DT_S/DT_W`;
  - описаны `margin_coverage_days`/`margin_missing_days` и правило `rule + z-score`.

## Current Focus
- Переход к Фазе 5: `sales analytics` и `margin analytics` end-to-end поверх уже готового KPI слоя.

## Active Decisions
- `ENABLE_LLM=false` по умолчанию.
- MVP остаётся single-station (`v1` без `stations`).
- Порог low-margin фиксирован в backend config (`kpi_low_margin_threshold_rub_per_liter=3.0`) и read-only для UI.
- Для KPI-маржи используется только пересечение дней, где есть и продажи, и закупки; покрытие отдаётся в `meta`.
- Продуктовые коды в активной реализации: `AI_92`, `AI_95`, `DT_S`, `DT_W`.

## Risks To Remember
- Для production-like окружения нужен JWT secret длиной >= 32 символов (dev secret остаётся демонстрационным).
- KPI cache сейчас in-memory в процессе FastAPI; при горизонтальном масштабировании понадобится внешний cache слой.
- Импорт всё ещё работает через background tasks FastAPI-процесса; для heavy-job operationalization нужен вынос в очередь/DAG.
