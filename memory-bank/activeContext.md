# Active Context

## Current State
- Фаза 2 реализована: поверх core schema v1 добавлены auth endpoints и frontend auth-flow.
- Backend поддерживает `JWT access + refresh cookie` через `/api/v1/auth/login|refresh|me|logout`.
- Frontend переведён с mock auth на реальный API-auth c авто-refresh и role guard.

## Recently Completed
- Реализован backend auth-контур:
  - JWT helper-утилиты в `app/core/security.py`;
  - `AuthService`, `get_current_user`, `require_roles`;
  - auth router в `app/api/v1/auth.py`;
  - error handler поддерживает application-level `error.code` (например `invalid_credentials`).
- Реализован frontend auth rework:
  - новый auth API layer (`login`, `refresh`, `me`, `logout`);
  - `AuthProvider` хранит access token в памяти, refresh cookie в браузере;
  - `ProtectedRoute` учитывает loading/unauth/403 состояния;
  - логин без ручного выбора роли.
- Тесты и проверки:
  - backend: `uv run pytest` — 14 passed, `uv run ruff check .` — clean;
  - frontend: `pnpm lint`, `pnpm test`, `pnpm build` — clean.

## Current Focus
- Переход к Фазе 3: вертикальный slice импорта (`/api/v1/import/*`) и демо-генерации данных.

## Active Decisions
- `ENABLE_LLM=false` по умолчанию.
- MVP остаётся single-station (`v1` без `stations`).
- Airflow и bonus contour изолированы профилями/этапами и не блокируют core-flow.
- Seed выполняется отдельной командой после миграций (`uv run fuelsight-seed-core`), не в startup и не в migration.
- Refresh session остаётся stateless (без отдельной таблицы refresh-сессий в фазе 2).

## Risks To Remember
- Для production-like окружения нужен секрет JWT длиной >= 32 символов (текущий `change-me` только для локальной разработки).
- При реализации импорта не нарушить envelope-контракт и role boundaries.
- Следить за синхронизацией docs_fuelsight и реализации после каждой большой фазы.
