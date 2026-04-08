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
OPENAI_API_KEY=
OLLAMA_BASE_URL=http://ollama:11434
```

### Defense mode
```env
DEFENSE_MODE=true
DEFENSE_PROFILE=offline-safe
```

## Mode Resolution
- if `OPENAI_API_KEY` present: `cloud_llm`
- else if local provider configured: `local_llm`
- else: `retrieval_only`

## Local Run Expectations
- current core commands remain valid;
- defense mode extends existing demo-runner rather than replacing local workflow;
- fresh machine must be able to run in `offline-safe`.

## Acceptance Criteria
- `core` stack still starts fast enough for development;
- defense profile produces a complete, readable report;
- missing cloud dependencies degrade the system instead of blocking startup.
