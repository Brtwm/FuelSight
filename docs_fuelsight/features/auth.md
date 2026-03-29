# Feature: Auth

## Обзор
- **Назначение**: обеспечить вход во внутреннюю систему FuelSight и корректное разграничение ролей `admin` и `analyst`.
- **Пользователь**: `admin`, `analyst`.
- **Точка входа**: `/login`.
- **Связанные фичи**: `data-import`, `kpi-dashboard`, `sales-analytics`, `procurement-margin`, `demand-forecast`, `news-digest-chat`.

## User Flow
1. Пользователь открывает `/login`.
2. Вводит email и пароль.
3. Система отправляет `POST /api/v1/auth/login`.
4. При успехе пользователь получает access token, refresh cookie и перенаправляется на `/dashboard`.
5. При последующих запросах frontend автоматически обновляет access token через `POST /api/v1/auth/refresh`.
6. При отсутствии прав на раздел пользователь видит экран `403 access denied`.
7. При logout сессия очищается и пользователь возвращается на `/login`.

## Состояния интерфейса
| Состояние | Описание | Что видит пользователь |
|---|---|---|
| Default | Страница только открылась | Форма входа, логотип, подсказка |
| Submitting | Отправка логина | Disabled кнопка, spinner |
| Success | Успешный вход | Redirect на `/dashboard` |
| InvalidCredentials | Неверный логин или пароль | Ошибка под формой |
| AccessDenied | Недостаточно прав | Сообщение о запрете доступа |
| SessionExpired | Refresh неуспешен | Сообщение о завершении сессии и возврат на `/login` |
| ServerError | Backend недоступен | Alert с retry |

## Ключевые компоненты

### `LoginPage`
- **Расположение**: `src/pages/LoginPage.tsx`
- **Поведение**: отображает карточку входа и короткое описание системы.

### `LoginForm`
- **Расположение**: `src/features/auth/components/LoginForm.tsx`
- **Пропсы**: `{ onSubmit: (credentials) => void, loading: boolean }`
- **Валидация**:
  - `email`: обязательный, валидный email;
  - `password`: обязательный, минимум 8 символов.

### `ProtectedRoute`
- **Расположение**: `src/features/auth/components/ProtectedRoute.tsx`
- **Пропсы**: `{ allowedRoles?: Array<'admin' | 'analyst'> }`
- **Поведение**: проверяет access token и роль, при необходимости запускает refresh flow.

## API-контракты

### `POST /api/v1/auth/login`
- **Авторизация**: `None`
- **Request Body**:
```json
{
  "email": "admin@fuelsight.local",
  "password": "string"
}
```
- **Response 200**:
```json
{
  "data": {
    "access_token": "jwt",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "role": "admin",
      "email": "admin@fuelsight.local"
    }
  },
  "error": null,
  "meta": {}
}
```
- **Response 401**:
```json
{
  "data": null,
  "error": {
    "code": "invalid_credentials",
    "message": "Неверный email или пароль"
  },
  "meta": {}
}
```

### `POST /api/v1/auth/refresh`
- **Авторизация**: refresh cookie
- **Response 200**: новый access token
- **Response 401**: refresh token недействителен

### `GET /api/v1/auth/me`
- **Авторизация**: `admin`, `analyst`
- **Response 200**: профиль пользователя и роль

### `POST /api/v1/auth/logout`
- **Авторизация**: `admin`, `analyst`
- **Response 200**: подтверждение выхода

## Модель данных
- Использует таблицы `users` и `roles`.
- Новых таблиц фича не создаёт.

## Frontend-требования
- Использовать `React Hook Form + Zod`.
- Access token хранить в памяти приложения; refresh token хранится в `HttpOnly` cookie.
- После логина редиректить по умолчанию на `/dashboard`, а не на последний открытый защищённый URL.
- Ошибки авторизации показывать на русском языке.

## Backend-требования
- Хранить `password_hash`, а не пароль.
- Выделить dependency для проверки роли.
- Реализовать refresh endpoint без требования повторного ввода пароля.
- Для демо-режима предусмотреть seeded пользователей `admin@fuelsight.local` и `analyst@fuelsight.local`.

## Edge Cases
- Пользователь уже авторизован и открывает `/login`.
- Access token истёк в момент перехода между страницами.
- Refresh cookie есть, но access token уже удалён из памяти.
- Backend недоступен при первичном логине.
- Пользователь `analyst` пытается открыть `/import`.

## Тестирование
- Unit: валидация формы, обработка статусов ошибок.
- Integration: login success, invalid credentials, auto-refresh, logout.
- E2E: вход под `admin` и под `analyst`, проверка доступа к роле-ограниченным разделам.
