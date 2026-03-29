# FuelSight Database Design

## Принципы схемы
- `v1` работает с одной точкой продаж, поэтому таблица `stations` не создаётся.
- Гранулярность фактов: `день x продукт`.
- Все основные сущности используют `UUID` как primary key, кроме справочника ролей, где допустим `SMALLSERIAL`.
- Для аналитики допускаются SQL view и materialized view, но базовая предметная модель опирается только на основные таблицы.

## Основные сущности и связи
```text
roles 1---N users
products 1---N sales_daily
products 1---N purchases_daily
products 1---N models
products 1---N forecasts
products 1---N backtest_runs
users 1---N import_jobs
users 1---N chat_sessions
chat_sessions 1---N chat_messages
```

## Таблицы Core

### `roles`
```sql
CREATE TABLE roles (
  id SMALLSERIAL PRIMARY KEY,
  slug VARCHAR(32) UNIQUE NOT NULL,
  name VARCHAR(64) NOT NULL
);
```

### `users`
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  display_name VARCHAR(128) NOT NULL,
  role_id SMALLINT NOT NULL REFERENCES roles(id),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `products`
```sql
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(32) UNIQUE NOT NULL,
  name VARCHAR(128) NOT NULL,
  unit VARCHAR(16) NOT NULL DEFAULT 'liter',
  density_kg_m3 NUMERIC(8,3),
  vat_rate NUMERIC(5,2),
  excise_rate NUMERIC(10,2),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `sales_daily`
```sql
CREATE TABLE sales_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sale_date DATE NOT NULL,
  product_id UUID NOT NULL REFERENCES products(id),
  volume_liters NUMERIC(14,3) NOT NULL,
  revenue_rub NUMERIC(14,2) NOT NULL,
  avg_retail_price_rub NUMERIC(10,4) NOT NULL,
  data_source VARCHAR(32) NOT NULL,
  source_batch_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (sale_date, product_id, data_source, source_batch_id)
);
```

### `purchases_daily`
```sql
CREATE TABLE purchases_daily (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  purchase_date DATE NOT NULL,
  product_id UUID NOT NULL REFERENCES products(id),
  volume_liters NUMERIC(14,3) NOT NULL,
  purchase_price_rub NUMERIC(10,4) NOT NULL,
  logistics_cost_rub NUMERIC(12,2) NOT NULL DEFAULT 0,
  supplier_name VARCHAR(255),
  total_cost_rub NUMERIC(14,2) NOT NULL,
  data_source VARCHAR(32) NOT NULL,
  source_batch_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `import_jobs`
```sql
CREATE TABLE import_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type VARCHAR(32) NOT NULL,
  source_type VARCHAR(32) NOT NULL,
  file_name VARCHAR(255),
  status VARCHAR(32) NOT NULL,
  rows_total INTEGER NOT NULL DEFAULT 0,
  rows_success INTEGER NOT NULL DEFAULT 0,
  rows_failed INTEGER NOT NULL DEFAULT 0,
  error_report_path TEXT,
  started_by UUID NOT NULL REFERENCES users(id),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ
);
```

## Таблицы ML

### `models`
```sql
CREATE TABLE models (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id),
  horizon_days INTEGER NOT NULL CHECK (horizon_days IN (1, 7, 30)),
  model_type VARCHAR(32) NOT NULL,
  version VARCHAR(64) NOT NULL,
  trained_at TIMESTAMPTZ NOT NULL,
  train_window_start DATE NOT NULL,
  train_window_end DATE NOT NULL,
  metrics_json JSONB NOT NULL,
  artifact_path TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT FALSE
);
```

### `forecasts`
```sql
CREATE TABLE forecasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id UUID REFERENCES models(id),
  product_id UUID NOT NULL REFERENCES products(id),
  forecast_date DATE NOT NULL,
  target_date DATE NOT NULL,
  horizon_days INTEGER NOT NULL,
  scenario_name VARCHAR(64) NOT NULL DEFAULT 'base',
  scenario_params_json JSONB,
  y_hat NUMERIC(14,3) NOT NULL,
  y_lo NUMERIC(14,3),
  y_hi NUMERIC(14,3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `backtest_runs`
```sql
CREATE TABLE backtest_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id),
  model_type VARCHAR(32) NOT NULL,
  horizon_days INTEGER NOT NULL,
  window_type VARCHAR(32) NOT NULL,
  status VARCHAR(32) NOT NULL,
  metrics_json JSONB NOT NULL,
  report_path TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ
);
```

## Таблицы NLP

### `news_raw`
```sql
CREATE TABLE news_raw (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_ref VARCHAR(255),
  source_name VARCHAR(64) NOT NULL,
  published_at TIMESTAMPTZ NOT NULL,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  snippet TEXT,
  full_text TEXT,
  language VARCHAR(8),
  topic_tags JSONB,
  impact_hint VARCHAR(32),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `news_digests`
```sql
CREATE TABLE news_digests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  digest_date DATE NOT NULL,
  period_type VARCHAR(16) NOT NULL,
  summary_text TEXT NOT NULL,
  bullet_points_json JSONB NOT NULL,
  source_ids_json JSONB NOT NULL,
  llm_mode VARCHAR(16) NOT NULL DEFAULT 'off',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `chat_sessions`
```sql
CREATE TABLE chat_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### `chat_messages`
```sql
CREATE TABLE chat_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  sender_type VARCHAR(16) NOT NULL,
  message_text TEXT NOT NULL,
  citations_json JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Производные витрины
- `vw_margin_daily`: join продаж и закупок по `date + product`, расчёт `gross_margin_rub_per_liter` и `gross_margin_pct`.
- `vw_kpi_summary`: агрегаты по периоду для dashboard.
- `vw_anomalies_daily`: вычисляемые аномалии продаж, закупки и маржи; в `v1` может строиться на лету без отдельной persist-таблицы.

## Индексы
```sql
CREATE INDEX idx_sales_daily_date_product ON sales_daily (sale_date, product_id);
CREATE INDEX idx_purchases_daily_date_product ON purchases_daily (purchase_date, product_id);
CREATE INDEX idx_forecasts_product_target_date ON forecasts (product_id, target_date);
CREATE INDEX idx_models_product_horizon_active ON models (product_id, horizon_days, is_active);
CREATE INDEX idx_news_raw_published_at ON news_raw (published_at DESC);
CREATE INDEX idx_chat_messages_session_created_at ON chat_messages (session_id, created_at);
```

## Ограничения и правила качества
- Для `sales_daily` значения `volume_liters` и `revenue_rub` должны быть строго положительными.
- Для `purchases_daily` `purchase_price_rub` не может быть отрицательной.
- Загрузка дубликатов в рамках одного batch не должна приводить к silent overwrite.
- Для таблиц `models`, `forecasts`, `backtest_runs` обязательна трассировка по продукту и горизонту.
- Ссылки в `chat_messages.citations_json` должны указывать на существующие `news_raw` либо на внутренние аналитические ref id.

## Примечание по v2
- Поддержка нескольких точек продаж потребует введения `stations` и добавления `station_id` в `sales_daily`, `purchases_daily`, `models`, `forecasts` и аналитические витрины.
- `features_daily` может быть добавлена в `v2`, если потребуется хранить materialized feature store в PostgreSQL.
