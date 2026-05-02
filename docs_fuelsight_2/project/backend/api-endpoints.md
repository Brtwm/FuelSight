# FuelSight v2 API Endpoints

## Общие соглашения
- Base URL: `/api/v1`
- Envelope:
```json
{
  "data": {},
  "error": null,
  "meta": {}
}
```
- Совместимость с текущими route groups сохраняется.
- Новые возможности добавляются через расширение payload, а не через новый top-level API group.

## Import

### `POST /api/v1/import/generate-demo`
- Path сохраняется для совместимости.
- User-facing термин: `initial history refresh`.
- Внутри backend допустимы технические `entity_type=historical_data` и `source_type=generated`.

### `GET /api/v1/import/jobs`
- Для admin diagnostics.
- Дополнительно может включать:
  - `display_label` для нейтрального UI;
  - `provenance_mode`;
  - `quality_status`.

## KPI

### `GET /api/v1/kpi/summary`
- Возвращает:
  - стандартные KPI;
  - `meta.explainability.summary`;
  - `meta.explainability.trust`;
  - `meta.explainability.state`;
  - `meta.margin_coverage_days`.

### `GET /api/v1/kpi/snapshot`
- `meta.explainability.chart`:
  - `annotations`;
  - `overlays`;
  - `supporting_refs`;
- `meta.explainability.summary` и `meta.explainability.trust`.

## Analytics

### `GET /api/v1/analytics/sales`
- `data`:
  - `series`
  - `seasonality`
  - `comparisons`
- `meta.explainability`:
  - `summary`
  - `chart.annotations`
  - `chart.overlays`
  - `chart.supporting_refs`
  - `trust` (`data_mode`, freshness, mode)
  - `state`

### `GET /api/v1/analytics/margin`
- `meta.explainability`:
  - `summary`
  - `chart.annotations`
  - `chart.overlays`
  - `chart.thresholds`
  - `chart.supporting_refs`
  - `trust`
  - `state`

### `GET /api/v1/analytics/anomalies`
- Сохраняет текущий shape.
- Может дополняться полями:
  - `supporting_refs`;
  - `confidence`;
  - `source_mode`.

## Forecasts

### `POST /api/v1/forecasts/run`
- Сохраняет текущий request shape.
- `data` расширяется:
  - `model_freshness`
  - `training_window`
  - `baseline_comparison`
  - `feature_sources`
  - `retrain_status`
  - `provider_mode`

### `GET /api/v1/forecasts/latest`
- Возвращает те же enriched fields, что и `run`.
- Дополнительно фиксируется pair-shape для UI:
  - `base_forecast_points`
  - `scenario_forecast_points`
  - `forecast_points` как совместимый alias для base-серии.

## Backtests

### `GET /api/v1/backtests/latest`
- Дополнительно возвращает:
  - `baseline_comparison`
  - `model_freshness`
  - `training_window`
  - `feature_sources`
  - `retrain_status`

## News

### `GET /api/v1/news/digests/latest`
- `data`:
  - `summary_text`
  - `bullet_points`
  - `source_ids`
  - `provider_mode`
  - `news_freshness`

### `GET /api/v1/news/search`
- Каждый результат дополняется:
  - `provider_mode`
  - `confidence`
  - `cached_at` when applicable

## Chat

### `POST /api/v1/chat/sessions/{session_id}/messages`
- `data.citations[*]` дополняется полями:
  - `provider_mode`
  - `confidence`
  - `source_type`
- `data.mode` фиксируется как `cloud_llm`, `local_llm` или `retrieval_only`.
- `data.confidence` вычисляется по retrieval signals.
- `data.verification` фиксирует `verified|repaired|fallback_verified|blocked`, reason, severity, unsupported terms, repair flag и claim counters.
- `meta.llm_provider` фиксирует выбранный provider: `neuraldeep`, `gigachat`, `local` или `none`.
- `meta.llm_provider.model` фиксирует активную модель, если ответ был синтезирован LLM adapter.
- `meta.llm_provider.degradation_reason` всегда заполняется при переходе с cloud/local generation на `retrieval_only`.
- `meta.retrieval` может включать:
  - `candidate_count`;
  - `selected_count`;
  - `source_counts`;
  - `reranker_used`;
  - `degradation_reason`.
- `meta.verification` и `meta.confidence` дублируют ключевые quality signals для UI diagnostics.
- При `ENABLE_LLM=false` endpoint возвращает `200` и `data.mode=retrieval_only`, если retrieval нашёл evidence.
- При `cloud_first` без ключа или при ошибке cloud adapter endpoint возвращает `200` и cited `retrieval_only` answer.
- Старые scopes `news_digest` и `internal_analytics` сохраняются как aliases для совместимости.

## Error Rules
- `503` допустим только для недоступного specific contour с явной деградацией.
- Если chat generation недоступен, предпочтителен `retrieval_only`, а не hard failure.
- Ошибки provider adapters обязаны отражаться в `meta` или diagnostics, а не теряться внутри UI.
- Cloud provider failure не должен ломать digest/search и не должен блокировать cited retrieval-only answer.
