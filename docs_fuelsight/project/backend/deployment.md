# FuelSight Deployment and Local Environment

## Цель развёртывания
Проект должен запускаться локально и демонстрироваться “вживую” на защите диплома. Основной профиль — ноутбук/ПК разработчика, где доступен Docker Compose, PostgreSQL и умеренный объём ресурсов.

## Docker Compose сервисы
| Service | Назначение | Port |
|---|---|---|
| `frontend` | React SPA | `3000` |
| `backend` | FastAPI API | `8061` |
| `db` | PostgreSQL | `5432` |
| `airflow-webserver` | UI и мониторинг DAG | `8080` |
| `airflow-scheduler` | Планировщик задач | internal |
| `airflow-init` | Инициализация Airflow БД и пользователя | one-shot |

## Рекомендуемая структура compose
```text
compose/
├── docker-compose.yml
├── env/
│   ├── backend.env
│   ├── frontend.env
│   └── airflow.env
└── volumes/
```

## Volumes
- `postgres_data`: постоянное хранение БД.
- `model_artifacts`: модели, backtest-репорты, parquet-витрины.
- `news_index`: локальный индекс для новостей и RAG.
- `airflow_logs`: логи выполнения DAG.

## Локальный запуск
```bash
docker compose up -d db
docker compose up -d backend frontend
docker compose up -d airflow-init airflow-webserver airflow-scheduler
```

## Начальная инициализация
1. Поднять PostgreSQL.
2. Применить Alembic миграции.
3. Создать роли `admin`, `analyst`.
4. Создать пользователей для демо.
5. Заполнить справочник продуктов `AI_92`, `AI_95`, `DT_S`, `DT_W`.
6. Либо загрузить CSV/XLSX, либо выполнить генерацию демо-данных.

## Порты и сетевые соглашения
- Frontend всегда обращается к backend по `http://localhost:8061/api/v1`.
- Airflow UI изолирован от основного пользовательского shell и используется только для демонстрации пайплайнов.
- Внешние API и новости должны читаться backend-контейнером, а не напрямую из браузера.

## Профиль ресурсов
- Базовый режим (`ENABLE_LLM=false`) должен уверенно работать на машине с ограниченной RAM.
- Для конфигурации уровня `RTX 3060 6GB + ~8GB RAM свободно` LLM-контур держать выключенным по умолчанию.
- При включении LLM использовать компактную квантованную модель `3B/7B 4-bit` и отделять её от обязательного MVP.

## Переменные окружения compose
### Backend
```env
APP_PORT=8061
DATABASE_URL=postgresql+psycopg://fuelsight:fuelsight@db:5432/fuelsight
ENABLE_LLM=false
NEWS_PROVIDER=gdelt
MODEL_ARTIFACTS_DIR=/opt/fuelsight/artifacts/models
NEWS_INDEX_DIR=/opt/fuelsight/artifacts/news
```

### Frontend
```env
VITE_API_BASE_URL=http://localhost:8061/api/v1
VITE_APP_PORT=3000
VITE_ENABLE_LLM=false
```

### Airflow
```env
AIRFLOW__CORE__LOAD_EXAMPLES=False
AIRFLOW__CORE__EXECUTOR=LocalExecutor
AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8080
```

## Наблюдаемость
- `backend`: структурированные логи запросов и фоновых задач.
- `airflow`: логи DAG и статус последних запусков.
- `db`: стандартные health checks.
- `frontend`: error boundary и уведомления об ошибках API.

## Риски и меры
- Если Airflow окажется слишком тяжёлым, основной бизнес-сценарий всё равно должен работать без ручного захода в его UI.
- Если LLM-контур недоступен, интерфейс показывает badge `LLM off` и оставляет доступной базовую digest-логику.
- Если данных мало для прогноза, система должна явно сообщать об ограничении и предлагать демо-датасет.
