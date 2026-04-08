# Feature: Auth v2

## Обзор
- Назначение: analyst-first вход в систему с сохранением строгих ролей `admin` и `analyst`.
- Точка входа: `/login`.
- Owners:
  - frontend: auth/login flow
  - backend: auth tokens, profile, role checks

## Ключевые изменения v2
- форма логина по умолчанию предзаполнена analyst-учёткой;
- после входа пользователь попадает на `/dashboard`;
- analyst является основным persona для демонстрации продукта;
- admin остаётся operational role.

## User Flow
1. Пользователь открывает `/login`.
2. Видит business-oriented описание продукта.
3. По умолчанию форма готова для analyst login.
4. После успеха попадает на `/dashboard`.
5. При истечении сессии видит понятное сообщение и возвращается на `/login`.

## UI States
- default
- submitting
- invalid credentials
- session expired
- access denied
- server unavailable

## Frontend Requirements
- хранить analyst-default prefill;
- не использовать admin как default demo user;
- ошибки показывать по-русски и без backend jargon.

## Backend Requirements
- текущие auth endpoints сохраняются;
- role guards не меняются;
- при необходимости `GET /auth/me` может возвращать `preferred_landing_route`.

## Tests
- analyst-default form state;
- successful analyst login;
- admin login remains valid;
- expired session flow.
