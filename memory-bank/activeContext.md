# Active Context

## Current State
- Фаза 3 реализована: добавлен вертикальный slice импорта и генерации исторических данных.
- Backend поддерживает `/api/v1/import/sales|purchases|generate-demo|jobs|jobs/{job_id}` с role guard `admin`.
- Frontend `/import` больше не stub: рабочие табы загрузки продаж/закупок и генерации исторических данных, плюс история job-ов.

## Recently Completed
- Реализован backend import-контур:
  - роутер `app/api/v1/imports.py` и wiring в `api_router`;
  - `ImportService` с CSV/XLSX парсингом, row-level валидацией и partial success;
  - единый lifecycle статусов `queued | processing | completed | completed_with_errors | failed`;
  - error report в JSON с сохранением пути в `import_jobs.error_report_path`;
  - продвинутый генератор исторических данных (выделен модуль `DataGenerator` без ORM);
  - сложная симуляция (AR(1) спрос, Ornstein-Uhlenbeck цены, праздники РФ, долгосрочный тренд);
  - поддержка 4 ГОСТ-продуктов (АИ-92, АИ-95, ДТ летнее, ДТ зимнее) со специфичной сезонностью;
  - политики дубликатов: skip + логирование в report.
- Реализован frontend import-flow:
  - `ImportPage` с табами `Продажи`, `Закупки`, `Исторические данные`;
  - `ImportUploadCard`, `GenerateHistoryDataForm`, `ImportJobsTable`;
  - polling истории импортов до terminal статусов;
  - invalidation query cache для KPI/analytics/forecast контуров после успешных операций.
- Тесты и проверки:
  - backend: `uv run ruff check .` — clean, `uv run pytest` — 29 passed (вкл. статистические тесты генератора);
  - frontend: `pnpm lint`, `pnpm test`, `pnpm build` — clean (12 passed).

## Current Focus
- Переход к Фазе 4: KPI dashboard поверх данных, загруженных/сгенерированных в фазе 3.

## Active Decisions
- `ENABLE_LLM=false` по умолчанию.
- MVP остаётся single-station (`v1` без `stations`).
- Airflow и bonus contour изолированы профилями/этапами и не блокируют core-flow.
- Seed выполняется отдельной командой после миграций (`uv run fuelsight-seed-core`), не в startup и не в migration.
- Refresh session остаётся stateless (без отдельной таблицы refresh-сессий в фазе 2).
- Пользовательский термин в UI: `исторические данные`; технический endpoint сохранён как `generate-demo`.

## Risks To Remember
- Для production-like окружения нужен секрет JWT длиной >= 32 символов (текущий `change-me` только для локальной разработки).
- Импорт сейчас выполняется через background task процесса FastAPI; при будущей операционализации стоит вынести тяжёлые задания в очередь/оркестратор.
- Следить за синхронизацией docs_fuelsight и реализации после каждой большой фазы.
