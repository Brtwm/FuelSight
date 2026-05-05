# FuelSight v2 Deployment And Local Environment

## Goal
Сохранить локальный Docker-first запуск, но добавить управляемые режимы интеграций и defense mode.

## Base Services
- `frontend`
- `backend`
- `db`
- `airflow-init`
- `airflow-webserver`
- `airflow-scheduler`

## Optional Capability Profiles
- `core`
- `airflow`
- `cloud-enhanced`
- `offline-safe`

## Environment Variables v2
### Required core
```env
APP_ENV=local
DATABASE_URL=postgresql+psycopg://fuelsight:fuelsight@db:5432/fuelsight
ENABLE_LLM=false
MODEL_ARTIFACTS_DIR=/opt/fuelsight/artifacts/models
NEWS_INDEX_DIR=/opt/fuelsight/artifacts/news
FEATURE_STORE_DIR=/opt/fuelsight/artifacts/models/features
```

### External indicators
```env
ENABLE_EXTERNAL_INDICATORS=true
EXTERNAL_INDICATORS_MODE=live
EXTERNAL_CACHE_DIR=/opt/fuelsight/artifacts/external
```

### LLM ladder
```env
ENABLE_LLM=true
LLM_PROVIDER_MODE=cloud_first
LLM_PROVIDER=neuraldeep
LLM_OPENAI_COMPAT_BASE_URL=https://api.neuraldeep.ru/v1
LLM_API_KEY=
LLM_CHAT_MODEL=gpt-oss-120b
LLM_EMBEDDING_MODEL=bge-m3
LLM_RERANKER_MODEL=bge-reranker
OLLAMA_BASE_URL=http://ollama:11434
```

### Alternative cloud providers
```env
# NeuralDeep cloud-enhanced profile
LLM_PROVIDER=neuraldeep
LLM_OPENAI_COMPAT_BASE_URL=https://api.neuraldeep.ru/v1
LLM_API_KEY=

# GigaChat alternative profile
LLM_PROVIDER=gigachat
GIGACHAT_AUTH_KEY=
GIGACHAT_SCOPE=
```

### Defense mode
```env
DEFENSE_MODE=true
DEFENSE_PROFILE=offline-safe
```

## Mode Resolution
- if `LLM_PROVIDER=neuraldeep` and `LLM_API_KEY` present: `cloud_llm`
- else if `LLM_PROVIDER=neuraldeep` and `GIGACHAT_AUTH_KEY` present: fallback to `GigaChat` as `cloud_llm`
- else if `LLM_PROVIDER=gigachat` and `GIGACHAT_AUTH_KEY` present: `cloud_llm`
- else if local provider configured: `local_llm`
- else: `retrieval_only`

## Provider Safety Rules
- `cloud-enhanced` mode may call NeuralDeep or GigaChat only after retrieval has produced an evidence pack.
- Raw `sales_daily`, `purchases_daily`, user records and import files are not sent to cloud providers.
- Cloud provider failures must be reflected in diagnostics and degrade to `local_llm` or `retrieval_only`, not block digest/search/chat.

## Local Run Expectations
- current core commands remain valid;
- defense mode extends existing demo-runner rather than replacing local workflow;
- fresh machine must be able to run in `offline-safe`.

## Acceptance Criteria
- `core` stack still starts fast enough for development;
- defense profile produces a complete, readable report;
- missing cloud dependencies degrade the system instead of blocking startup.
