# Active Context

## Current Focus
- Главный живой срез на 2026-04-16: доведение forecasting-контура до более прозрачного analyst-facing состояния.
- Цель текущих локальных изменений: показать не только `y_hat`, но и качество/свежесть модели, источник признаков, сравнение с baseline и эффект ценового сценария.

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

## Next Likely Steps
- Довести текущий forecast slice до commit-ready состояния:
  - убедиться, что API/meta-contract и UI copy уже финальны;
  - решить, нужен ли ещё один проход по smoke/e2e.
- Синхронизировать `docs_fuelsight/` и при необходимости `README.md` с фактическими forecast contracts:
  - `model_freshness`
  - `baseline_comparison`
  - `provider_mode`
  - `base vs scenario` UX
- После стабилизации forecast worktree вернуться к следующему крупному направлению:
  - explainable dashboard/analytics;
  - real `news + chat`;
  - defense mode / executive outputs.

## Active Decisions
- Analyst-first демонстрационный сценарий остаётся главным; admin-функции — отдельно и не должны ломать narrative.
- Base forecast остаётся канонической серией, scenario — сравнительным overlay.
- Health/freshness должен вычисляться на backend и приходить готовым контрактом в API/UI.
- Core KPI/analytics/forecast обязаны сохранять работоспособность при деградации внешних источников и при `LLM off`.

## Risks To Remember
- Текущее состояние репозитория опережает последний коммит: часть важных forecast-изменений пока только в worktree.
- Верхнеуровневые docs ещё не полностью синхронизированы с этим срезом.
- Manifest-driven health полезен только при регулярном refresh артефактов; на stale локальных данных UI может честно показывать warning/degraded, даже если код исправен.
