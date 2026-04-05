# Frontend

FuelSight frontend на `React + Vite + TypeScript`.

## Текущий статус
- Реализованы маршруты core MVP:
  - `/login`
  - `/import`
  - `/dashboard`
  - `/analytics/sales`
  - `/analytics/margin`
  - `/forecast`
- Реализован bonus contour route `/news` (Phase 8): digest, поиск новостей, chat с citations и режим `LLM off`.

## Команды
```bash
corepack pnpm --filter frontend install
corepack pnpm --filter frontend dev --host 0.0.0.0 --port 3000
corepack pnpm --filter frontend build
corepack pnpm --filter frontend test
corepack pnpm --filter frontend lint
```

## Интеграция
- API base: `VITE_API_BASE_URL=http://localhost:8061/api/v1`
- Контракт ответов backend: `{ data, error, meta }`
- Auth: access token in-memory + refresh cookie flow

Используйте корневой `README.md` для полного локального запуска (`core`, `airflow`, `demo-run`).
