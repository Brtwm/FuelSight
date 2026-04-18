# Active Context

## Current Focus
- На 2026-04-16 выполнен `Phase A` документационный freeze:
  - `README.md` переведён на capability-based status snapshot;
  - `docs_fuelsight/as-built-baseline.md` добавлен как основной `as-built` baseline;
  - `docs_fuelsight_2/v2-roadmap.md` обновлён под новый roadmap с треками `visual/mobile`, `real news`, `RAG chat`, `defense`;
  - `docs_fuelsight_2/phase0-gap-matrix.md` расширен до execution backlog.
- Forecasting-контур остаётся главным живым worktree-срезом, который уже частично опережает зафиксированный commit baseline.

## Worktree Snapshot
- `backend/app/pipeline/tasks.py`
  - enrich feature store внешними индикаторами и межпродуктовым контекстом;
  - пишет `feature_refresh_manifest_*`, `train_backtest_manifest_*`, `model_freshness_manifest_*`;
  - возвращает coverage/fallback/provider summary в pipeline result.
- `backend/app/services/forecast_service.py`
  - добавляет в forecast/backtest payload health-поля;
  - вычисляет `model_freshness` и `retrain_status` из возраста модели и feature-refresh manifest;
  - подтягивает `provider_mode`, `feature_sources`, `baseline_comparison`.
- `backend/ml/features/dataset.py`
  - расширяет feature vector признаками external indicators, event pressure и group-level context.
- `frontend/src/pages/ForecastPage.tsx`
  - запускает `base`-прогноз отдельно от `scenario`;
  - сравнивает их в одном chart/table;
  - показывает `ModelHealthPanel`.
- `scripts/run_full_demo.py`
  - теперь дополнительно проверяет наличие manifest-файлов после refresh/train шагов.

## What Was Verified Today
- `uv run pytest tests/test_forecast_api.py tests/test_forecast_service.py tests/test_pipeline_tasks.py` -> `11 passed`
- `corepack pnpm --filter frontend test -- src/pages/ForecastPage.states.test.tsx` -> фактически прогнался весь frontend suite, `35 files / 92 tests passed`
- `uv run pytest tests/test_news_api.py tests/test_chat_api.py` -> `8 passed`

## Next Likely Steps
- Довести текущий forecast slice до commit-ready состояния:
  - закрепить финальный `base vs scenario` UX;
  - досинхронизировать docs по `model_freshness`, `baseline_comparison`, `provider_mode`, `training_window`.
- Открыть следующий cross-cutting track:
  - `Phase B. Visual Polish + Mobile Readiness`.
- После этого перейти к главной feature-ветке:
  - `Phase F. Real News Ingestion Baseline`;
  - `Phase G. RAG-First Chat Core`.

## Active Decisions
- Analyst-first демонстрационный сценарий остаётся главным; admin-функции — отдельно и не должны ломать narrative.
- Base forecast остаётся канонической серией, scenario — сравнительным overlay.
- Health/freshness должен вычисляться на backend и приходить готовым контрактом в API/UI.
- Core KPI/analytics/forecast обязаны сохранять работоспособность при деградации внешних источников и при `LLM off`.
- Chat target pattern зафиксирован как `stateful verified RAG`, а не autonomous web agent.
- Mobile readiness выделен в отдельный roadmap track и больше не считается optional visual cleanup.

## Risks To Remember
- Текущее состояние репозитория опережает последний коммит: часть важных forecast-изменений пока только в worktree.
- Верхнеуровневые docs после `Phase A` синхронизированы лучше, но feature-level docs ещё нужно обновлять по мере закрытия следующих capability slices.
- Manifest-driven health полезен только при регулярном refresh артефактов; на stale локальных данных UI может честно показывать warning/degraded, даже если код исправен.
- Текущий `news/chat` runtime ещё MVP-level и не соответствует будущему `real news + retrieval-first` contour, несмотря на наличие schemas/tests.
