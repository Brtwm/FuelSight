from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import Select, select, text, update
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import BacktestRun, ForecastRecord, ModelRecord, Product
from app.repositories.external_indicators_repository import ExternalIndicatorsRepository
from app.services.event_catalog_service import EventCatalogService
from app.services.external_context_service import ExternalContextService
from ml.backtesting import BacktestOutcome, run_rolling_backtest
from ml.features import FEATURE_NAMES, MAX_LAG, build_training_matrix, normalize_history_rows
from ml.inference import forecast_with_baseline, forecast_with_catboost
from ml.models import CatBoostDemandModel, is_catboost_available

ModelType = Literal["catboost", "seasonal_naive"]
WindowType = Literal["rolling", "expanding"]

MODEL_FRESH_DAYS = 8
MODEL_WARNING_DAYS = 14
FEATURE_FRESH_DAYS = 1
FEATURE_WARNING_DAYS = 2
FEATURE_COVERAGE_FRESH = 0.95
FEATURE_COVERAGE_WARNING = 0.85

DRIVER_LABELS = {
    "lag_1": "Спрос предыдущего дня остаётся ключевым ориентиром.",
    "lag_7": "Недельная сезонность заметно влияет на объём продаж.",
    "lag_14": "Двухнедельный паттерн поддерживает текущую динамику.",
    "lag_28": "Месячный цикл спроса учитывается в прогнозе.",
    "rolling_mean_7": "Средний спрос за 7 дней задаёт базовый уровень прогноза.",
    "rolling_mean_14": "Средний спрос за 14 дней стабилизирует прогноз.",
    "rolling_mean_28": "Средний спрос за 28 дней задаёт долгий тренд.",
    "avg_retail_price_rub": "Текущая розничная цена влияет на ожидаемый спрос.",
    "retail_price_change_pct": "Темп изменения розничной цены учитывается моделью.",
    "gross_margin_rub_per_liter": "Маржинальность учитывается как фактор ценовой устойчивости.",
    "event_pressure_score": "Событийное давление учитывается при оценке краткосрочного спроса.",
    "product_share_in_group": "Доля продукта в группе помогает учесть каннибализацию и сдвиги спроса.",
    "group_volume_lag_7": "Групповая динамика за неделю добавляет контекст межпродуктового спроса.",
}

DEFAULT_FEATURE_SOURCES = [
    "lag_rolling",
    "calendar",
    "price_margin",
    "external_indicators",
    "event_pressure",
    "cross_product_context",
]

FORECAST_OVERLAY_LABELS: dict[str, str] = {
    "crude_brent_usd": "Brent, $/баррель",
    "usd_rub": "USD/RUB",
    "wholesale_gasoline_index": "Оптовый индекс бензина",
    "wholesale_diesel_index": "Оптовый индекс дизеля",
}


@dataclass(frozen=True)
class ForecastResult:
    data: dict[str, Any]
    meta: dict[str, Any]


@dataclass(frozen=True)
class LatestForecastResult:
    data: dict[str, Any] | None
    meta: dict[str, Any]


@dataclass(frozen=True)
class BacktestResult:
    data: dict[str, Any]
    meta: dict[str, Any]


@dataclass(frozen=True)
class LatestBacktestResult:
    data: dict[str, Any] | None
    meta: dict[str, Any]


class ForecastService:
    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._event_catalog_service = EventCatalogService(session)
        self._external_context_service = ExternalContextService(self._settings)
        self._external_repository = ExternalIndicatorsRepository(session)

    def run_forecast(
        self,
        *,
        product_code: str,
        horizon_days: int,
        scenario: dict[str, Any] | None,
    ) -> ForecastResult:
        normalized_code = self._normalize_product_code(product_code)
        normalized_horizon = self._normalize_horizon_days(horizon_days)
        scenario_delta = self._scenario_delta_pct(scenario)

        product = self._get_product(normalized_code)
        history = self._load_history(product.id)
        if len(history) < MAX_LAG + 1:
            raise ValueError("Insufficient history for forecast generation")

        model = self._get_active_model(product.id, normalized_horizon)
        model_type: ModelType = "seasonal_naive"
        model_status = "baseline_fallback"
        residual_std: float | None = None
        drivers: list[str] = []

        if model is not None:
            model_type = model.model_type  # type: ignore[assignment]
            model_status = "active"
            residual_std = self._metric_float(model.metrics_json, "residual_std")

        if model is not None and model.model_type == "catboost":
            try:
                catboost_model = CatBoostDemandModel.load(Path(model.artifact_path))
                forecast_path = forecast_with_catboost(
                    history,
                    normalized_horizon,
                    catboost_model,
                    scenario_delta_pct=scenario_delta,
                    residual_std=residual_std,
                )
                drivers = self._build_catboost_drivers(model, scenario_delta)
            except Exception:
                forecast_path = forecast_with_baseline(
                    history,
                    normalized_horizon,
                    scenario_delta_pct=scenario_delta,
                    residual_std=residual_std,
                )
                model_type = "seasonal_naive"
                model_status = "baseline_fallback"
                drivers = self._build_baseline_drivers(scenario_delta, fallback=True)
        else:
            forecast_path = forecast_with_baseline(
                history,
                normalized_horizon,
                scenario_delta_pct=scenario_delta,
                residual_std=residual_std,
            )
            drivers = self._build_baseline_drivers(
                scenario_delta,
                fallback=(model is None),
            )
            if model is not None and model.model_type == "seasonal_naive":
                model_status = "baseline_fallback"

        target_dates = self._target_dates(history[-1].day, normalized_horizon)
        forecast_points = [
            {
                "target_date": day.isoformat(),
                "y_hat": round(point.y_hat, 3),
                "y_lo": None if point.y_lo is None else round(point.y_lo, 3),
                "y_hi": None if point.y_hi is None else round(point.y_hi, 3),
            }
            for day, point in zip(target_dates, forecast_path, strict=True)
        ]

        scenario_name = "base" if scenario_delta == 0 else "what_if_price"
        scenario_params = (
            None if scenario_delta == 0 else {"retail_price_delta_pct": scenario_delta}
        )
        self._store_forecast_rows(
            product_id=product.id,
            model_id=model.id if model_status == "active" and model is not None else None,
            horizon_days=normalized_horizon,
            scenario_name=scenario_name,
            scenario_params=scenario_params,
            forecast_points=forecast_points,
        )

        health_payload = self._resolve_health_payload(
            model=model,
            model_status=model_status,
        )
        external_context_quality = self._external_context_service.build_external_context_quality()
        event_context = self._event_catalog_service.build_event_context(
            start_date=target_dates[0],
            end_date=target_dates[-1],
        )
        reference_overlays, overlays_provider_mode = self._build_reference_overlays(
            product_code=normalized_code,
            start_date=target_dates[0],
            end_date=target_dates[-1],
        )
        resolved_provider_mode = (
            external_context_quality.get("provider_mode")
            or overlays_provider_mode
            or health_payload.get("provider_mode")
        )

        return ForecastResult(
            data={
                "product_code": normalized_code,
                "horizon_days": normalized_horizon,
                "model_type": model_type,
                "model_status": model_status,
                "scenario_name": scenario_name,
                "scenario_params": scenario_params,
                "forecast_points": forecast_points,
                "drivers": drivers,
                **health_payload,
                "external_context_quality": external_context_quality,
                "event_context": event_context,
                "reference_overlays": reference_overlays,
            },
            meta={
                "points": len(forecast_points),
                "scenario_delta_pct": scenario_delta,
                "model_freshness": health_payload.get("model_freshness"),
                "provider_mode": resolved_provider_mode,
                "external_indicators_mode": resolved_provider_mode,
                "external_context": external_context_quality,
            },
        )

    def get_latest_forecast(
        self,
        *,
        product_code: str,
        horizon_days: int,
    ) -> LatestForecastResult:
        normalized_code = self._normalize_product_code(product_code)
        normalized_horizon = self._normalize_horizon_days(horizon_days)
        product = self._get_product(normalized_code)

        latest = (
            self._session.execute(
                text(
                    """
                SELECT forecast_date, scenario_name
                FROM forecasts
                WHERE product_id = :product_id
                  AND horizon_days = :horizon_days
                ORDER BY created_at DESC
                LIMIT 1
                """
                ),
                {"product_id": product.id, "horizon_days": normalized_horizon},
            )
            .mappings()
            .first()
        )

        if latest is None:
            return LatestForecastResult(
                data=None,
                meta={"empty_state": "Прогнозы пока не рассчитаны."},
            )

        rows = (
            self._session.execute(
                text(
                    """
                SELECT DISTINCT ON (target_date)
                  target_date,
                  y_hat,
                  y_lo,
                  y_hi,
                  model_id,
                  scenario_params_json
                FROM forecasts
                WHERE product_id = :product_id
                  AND horizon_days = :horizon_days
                  AND forecast_date = :forecast_date
                  AND scenario_name = :scenario_name
                ORDER BY target_date, created_at DESC
                """
                ),
                {
                    "product_id": product.id,
                    "horizon_days": normalized_horizon,
                    "forecast_date": latest["forecast_date"],
                    "scenario_name": latest["scenario_name"],
                },
            )
            .mappings()
            .all()
        )

        if not rows:
            return LatestForecastResult(
                data=None,
                meta={"empty_state": "Прогнозы пока не рассчитаны."},
            )

        model_type: ModelType = "seasonal_naive"
        model_status = "baseline_fallback"
        drivers = self._build_baseline_drivers(0.0, fallback=True)
        model: ModelRecord | None = None
        model_id = rows[0]["model_id"]
        if model_id is not None:
            model = self._session.get(ModelRecord, model_id)
            if model is not None:
                model_type = model.model_type  # type: ignore[assignment]
                model_status = "active" if model.model_type == "catboost" else "baseline_fallback"
                if model_type == "catboost":
                    drivers = self._build_catboost_drivers(model, 0.0)
                else:
                    drivers = self._build_baseline_drivers(0.0, fallback=False)

        forecast_points = [
            {
                "target_date": row["target_date"].isoformat(),
                "y_hat": round(float(row["y_hat"]), 3),
                "y_lo": None if row["y_lo"] is None else round(float(row["y_lo"]), 3),
                "y_hi": None if row["y_hi"] is None else round(float(row["y_hi"]), 3),
            }
            for row in rows
        ]
        health_payload = self._resolve_health_payload(
            model=model,
            model_status=model_status,
        )
        target_dates = [date.fromisoformat(item["target_date"]) for item in forecast_points]
        external_context_quality = self._external_context_service.build_external_context_quality()
        event_context = []
        reference_overlays: list[dict[str, Any]] = []
        overlays_provider_mode: str | None = None
        if target_dates:
            event_context = self._event_catalog_service.build_event_context(
                start_date=min(target_dates),
                end_date=max(target_dates),
            )
            reference_overlays, overlays_provider_mode = self._build_reference_overlays(
                product_code=normalized_code,
                start_date=min(target_dates),
                end_date=max(target_dates),
            )
        resolved_provider_mode = (
            external_context_quality.get("provider_mode")
            or overlays_provider_mode
            or health_payload.get("provider_mode")
        )

        return LatestForecastResult(
            data={
                "product_code": normalized_code,
                "horizon_days": normalized_horizon,
                "model_type": model_type,
                "model_status": model_status,
                "scenario_name": latest["scenario_name"],
                "scenario_params": rows[0]["scenario_params_json"],
                "forecast_points": forecast_points,
                "drivers": drivers,
                **health_payload,
                "external_context_quality": external_context_quality,
                "event_context": event_context,
                "reference_overlays": reference_overlays,
            },
            meta={
                "forecast_date": latest["forecast_date"].isoformat(),
                "points": len(forecast_points),
                "model_freshness": health_payload.get("model_freshness"),
                "provider_mode": resolved_provider_mode,
                "external_indicators_mode": resolved_provider_mode,
                "external_context": external_context_quality,
            },
        )

    def run_backtest(
        self,
        *,
        product_code: str,
        horizon_days: int,
        window_type: WindowType,
    ) -> BacktestResult:
        normalized_code = self._normalize_product_code(product_code)
        normalized_horizon = self._normalize_horizon_days(horizon_days)
        normalized_window = self._normalize_window_type(window_type)
        product = self._get_product(normalized_code)
        history = self._load_history(product.id)
        if len(history) < MAX_LAG + normalized_horizon + 20:
            raise ValueError("Insufficient history for backtest")

        baseline_outcome = run_rolling_backtest(
            history,
            model_type="seasonal_naive",
            horizon_days=normalized_horizon,
            window_type=normalized_window,
        )
        outcomes: list[BacktestOutcome] = [baseline_outcome]
        catboost_outcome: BacktestOutcome | None = None
        catboost_failure_reason: str | None = None
        if is_catboost_available():
            try:
                catboost_outcome = run_rolling_backtest(
                    history,
                    model_type="catboost",
                    horizon_days=normalized_horizon,
                    window_type=normalized_window,
                )
                outcomes.append(catboost_outcome)
            except Exception as exc:  # noqa: BLE001
                catboost_failure_reason = str(exc)
        else:
            catboost_failure_reason = "catboost_unavailable"

        winner = catboost_outcome or baseline_outcome
        winner_reason = "catboost_primary" if catboost_outcome is not None else "catboost_fallback"
        try:
            trained_model = self._register_active_model(
                product_id=product.id,
                product_code=normalized_code,
                horizon_days=normalized_horizon,
                winner=winner,
                history=history,
            )
        except Exception as exc:  # noqa: BLE001
            if winner.model_type != "catboost":
                raise
            catboost_failure_reason = str(exc)
            winner = baseline_outcome
            winner_reason = "catboost_artifact_failure"
            trained_model = self._register_active_model(
                product_id=product.id,
                product_code=normalized_code,
                horizon_days=normalized_horizon,
                winner=winner,
                history=history,
            )

        comparison = {
            outcome.model_type: {
                "mae": round(outcome.mae, 4),
                "rmse": round(outcome.rmse, 4),
                "smape": round(outcome.smape, 4),
            }
            for outcome in outcomes
        }
        winner_metrics = comparison[winner.model_type]
        baseline_metrics = comparison["seasonal_naive"]
        baseline_comparison = self._build_baseline_comparison(
            winner_metrics=winner_metrics,
            baseline_metrics=baseline_metrics,
            winner_model_type=winner.model_type,
        )
        feature_manifest = self._load_latest_feature_refresh_manifest()
        model_status = "active" if winner.model_type == "catboost" else "baseline_fallback"
        health_payload = self._resolve_health_payload(
            model=trained_model,
            model_status=model_status,
            feature_manifest=feature_manifest,
        )
        training_window = {
            "start_date": history[0].day.isoformat(),
            "end_date": history[-1].day.isoformat(),
        }
        provider_mode = health_payload.get("provider_mode")
        trained_model_metrics = getattr(trained_model, "metrics_json", {})
        if not isinstance(trained_model_metrics, dict):
            trained_model_metrics = {}
        feature_sources = self._resolve_feature_sources(metrics_json=trained_model_metrics)
        residual_stats = {
            "winner_residual_std": round(winner.residual_std, 6),
            "baseline_residual_std": round(baseline_outcome.residual_std, 6),
            "residual_std_delta": round(winner.residual_std - baseline_outcome.residual_std, 6),
        }
        enriched_metrics_json = {
            "winner": winner.model_type,
            "winner_reason": winner_reason,
            "winner_metrics": winner_metrics,
            "baseline_metrics": baseline_metrics,
            "comparison": comparison,
            "baseline_comparison": baseline_comparison,
            "folds": winner.folds,
            "residual_std": round(winner.residual_std, 6),
            "residual_stats": residual_stats,
            "training_window": training_window,
            "feature_sources": feature_sources,
            "provider_mode": provider_mode,
            "model_freshness": health_payload.get("model_freshness"),
            "retrain_status": health_payload.get("retrain_status"),
            "cadence": {
                "model_fresh_days": MODEL_FRESH_DAYS,
                "model_warning_days": MODEL_WARNING_DAYS,
                "feature_fresh_days": FEATURE_FRESH_DAYS,
                "feature_warning_days": FEATURE_WARNING_DAYS,
            },
            "feature_refresh_manifest_path": (
                feature_manifest.get("manifest_path") if feature_manifest is not None else None
            ),
            "model_version": trained_model.version,
            "catboost_failure_reason": catboost_failure_reason,
        }
        trained_model.metrics_json = enriched_metrics_json

        report_path = self._write_backtest_report(
            product_code=normalized_code,
            horizon_days=normalized_horizon,
            window_type=normalized_window,
            winner=winner.model_type,
            comparison=comparison,
        )

        run = BacktestRun(
            product_id=product.id,
            model_type=winner.model_type,
            horizon_days=normalized_horizon,
            window_type=normalized_window,
            status="success",
            metrics_json=enriched_metrics_json,
            report_path=str(report_path),
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
        )
        self._session.add(run)
        self._session.commit()

        return BacktestResult(
            data={
                "product_code": normalized_code,
                "horizon_days": normalized_horizon,
                "model_type": winner.model_type,
                "window_type": normalized_window,
                "metrics": winner_metrics,
                "comparison": comparison,
                "trained_at": trained_model.trained_at.isoformat(),
                "model_version": trained_model.version,
                **health_payload,
            },
            meta={
                "folds": winner.folds,
                "model_freshness": health_payload.get("model_freshness"),
                "provider_mode": health_payload.get("provider_mode"),
                "external_indicators_mode": health_payload.get("provider_mode"),
                "external_context": self._external_context_service.build_external_context_quality(),
            },
        )

    def get_latest_backtest(
        self,
        *,
        product_code: str,
        horizon_days: int,
    ) -> LatestBacktestResult:
        normalized_code = self._normalize_product_code(product_code)
        normalized_horizon = self._normalize_horizon_days(horizon_days)
        product = self._get_product(normalized_code)

        statement: Select[tuple[BacktestRun]] = (
            select(BacktestRun)
            .where(
                BacktestRun.product_id == product.id,
                BacktestRun.horizon_days == normalized_horizon,
                BacktestRun.status == "success",
            )
            .order_by(BacktestRun.finished_at.desc(), BacktestRun.started_at.desc())
            .limit(1)
        )
        latest = self._session.scalar(statement)
        if latest is None:
            return LatestBacktestResult(
                data=None,
                meta={"empty_state": "Backtest пока не запускался."},
            )

        metrics_json = latest.metrics_json or {}
        winner_metrics = metrics_json.get("winner_metrics", {})
        comparison = metrics_json.get("comparison", {})
        fallback_health = self._resolve_health_payload(
            model=None,
            model_status="active" if latest.model_type == "catboost" else "baseline_fallback",
        )
        health_payload = {
            "model_freshness": metrics_json.get("model_freshness", fallback_health.get("model_freshness")),
            "training_window": metrics_json.get("training_window", fallback_health.get("training_window")),
            "baseline_comparison": metrics_json.get(
                "baseline_comparison",
                fallback_health.get("baseline_comparison"),
            ),
            "feature_sources": metrics_json.get("feature_sources", fallback_health.get("feature_sources")),
            "retrain_status": metrics_json.get("retrain_status", fallback_health.get("retrain_status")),
            "provider_mode": metrics_json.get("provider_mode", fallback_health.get("provider_mode")),
        }

        return LatestBacktestResult(
            data={
                "product_code": normalized_code,
                "horizon_days": normalized_horizon,
                "model_type": latest.model_type,
                "window_type": latest.window_type,
                "metrics": {
                    "mae": round(float(winner_metrics.get("mae", 0.0)), 4),
                    "rmse": round(float(winner_metrics.get("rmse", 0.0)), 4),
                    "smape": round(float(winner_metrics.get("smape", 0.0)), 4),
                },
                "comparison": comparison,
                "trained_at": (
                    latest.finished_at.isoformat()
                    if latest.finished_at is not None
                    else latest.started_at.isoformat()
                ),
                "model_version": metrics_json.get("model_version"),
                **health_payload,
            },
            meta={
                "status": latest.status,
                "model_freshness": health_payload.get("model_freshness"),
                "provider_mode": health_payload.get("provider_mode"),
                "external_indicators_mode": health_payload.get("provider_mode"),
                "external_context": self._external_context_service.build_external_context_quality(),
            },
        )

    def _resolve_health_payload(
        self,
        *,
        model: ModelRecord | None,
        model_status: str,
        feature_manifest: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        metrics_json = {}
        if model is not None:
            raw_metrics = getattr(model, "metrics_json", {})
            if isinstance(raw_metrics, dict):
                metrics_json = raw_metrics
        resolved_feature_manifest = feature_manifest or self._load_latest_feature_refresh_manifest()
        model_freshness, retrain_status = self._compute_model_health(
            model_trained_at=getattr(model, "trained_at", None),
            model_status=model_status,
            feature_manifest=resolved_feature_manifest,
        )
        training_window = None
        if (
            model is not None
            and getattr(model, "train_window_start", None) is not None
            and getattr(model, "train_window_end", None) is not None
        ):
            training_window = {
                "start_date": model.train_window_start.isoformat(),  # type: ignore[union-attr]
                "end_date": model.train_window_end.isoformat(),  # type: ignore[union-attr]
            }
        elif isinstance(metrics_json.get("training_window"), dict):
            training_window = metrics_json["training_window"]

        provider_mode = self._resolve_provider_mode(
            metrics_json=metrics_json,
            feature_manifest=resolved_feature_manifest,
        )
        return {
            "model_freshness": model_freshness,
            "training_window": training_window,
            "baseline_comparison": self._resolve_baseline_comparison(metrics_json=metrics_json),
            "feature_sources": self._resolve_feature_sources(metrics_json=metrics_json),
            "retrain_status": retrain_status,
            "provider_mode": provider_mode,
        }

    def _compute_model_health(
        self,
        *,
        model_trained_at: datetime | None,
        model_status: str,
        feature_manifest: dict[str, Any] | None,
    ) -> tuple[str, str]:
        if model_status != "active":
            return "degraded", "degraded"
        if model_trained_at is None:
            return "degraded", "failed"

        now = datetime.now(UTC)
        model_age_days = (now.date() - model_trained_at.date()).days
        feature_age_days = 999
        coverage_ratio = 0.0

        if feature_manifest is not None:
            run_date_raw = feature_manifest.get("run_date")
            if isinstance(run_date_raw, str):
                try:
                    feature_date = date.fromisoformat(run_date_raw)
                    feature_age_days = (now.date() - feature_date).days
                except ValueError:
                    feature_age_days = 999
            coverage_ratio = float(feature_manifest.get("coverage_ratio") or 0.0)

        if (
            model_age_days <= MODEL_FRESH_DAYS
            and feature_age_days <= FEATURE_FRESH_DAYS
            and coverage_ratio >= FEATURE_COVERAGE_FRESH
        ):
            return "fresh", "ok"
        if (
            model_age_days <= MODEL_WARNING_DAYS
            and feature_age_days <= FEATURE_WARNING_DAYS
            and coverage_ratio >= FEATURE_COVERAGE_WARNING
        ):
            return "warning", "warning"
        return "degraded", "degraded"

    @staticmethod
    def _resolve_baseline_comparison(metrics_json: dict[str, Any]) -> dict[str, dict[str, float]] | None:
        value = metrics_json.get("baseline_comparison")
        if isinstance(value, dict):
            return value  # type: ignore[return-value]
        return None

    @staticmethod
    def _resolve_feature_sources(metrics_json: dict[str, Any]) -> list[str]:
        value = metrics_json.get("feature_sources")
        if isinstance(value, list):
            return [str(item) for item in value]
        return [*DEFAULT_FEATURE_SOURCES]

    @staticmethod
    def _resolve_provider_mode(
        *,
        metrics_json: dict[str, Any],
        feature_manifest: dict[str, Any] | None,
    ) -> str | None:
        value = metrics_json.get("provider_mode")
        if isinstance(value, str) and value:
            return value
        if feature_manifest is not None:
            candidate = feature_manifest.get("provider_mode")
            if isinstance(candidate, str) and candidate:
                return candidate
            mode_counts = feature_manifest.get("provider_mode_counts")
            if isinstance(mode_counts, dict) and mode_counts:
                sorted_modes = sorted(
                    (
                        (str(key), int(val))
                        for key, val in mode_counts.items()
                    ),
                    key=lambda item: item[1],
                    reverse=True,
                )
                if sorted_modes:
                    return sorted_modes[0][0]
        return None

    @staticmethod
    def _build_baseline_comparison(
        *,
        winner_metrics: dict[str, float],
        baseline_metrics: dict[str, float],
        winner_model_type: str,
    ) -> dict[str, dict[str, float]]:
        delta = {
            metric_name: round(
                float(winner_metrics.get(metric_name, 0.0)) - float(baseline_metrics.get(metric_name, 0.0)),
                4,
            )
            for metric_name in ("mae", "rmse", "smape")
        }
        return {
            "winner": winner_metrics,
            "seasonal_naive": baseline_metrics,
            "delta_vs_baseline": delta,
            "winner_model": {"code": 1.0 if winner_model_type == "catboost" else 0.0},
        }

    def _load_latest_feature_refresh_manifest(self) -> dict[str, Any] | None:
        feature_store_dir = getattr(self._settings, "feature_store_dir", None)
        if not isinstance(feature_store_dir, str) or not feature_store_dir.strip():
            return None
        root = Path(feature_store_dir)
        if not root.exists():
            return None
        manifests = sorted(
            root.glob("*/feature_refresh_manifest_*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if not manifests:
            return None
        payload = json.loads(manifests[0].read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        payload["manifest_path"] = str(manifests[0])
        return payload

    def _register_active_model(
        self,
        *,
        product_id: Any,
        product_code: str,
        horizon_days: int,
        winner: BacktestOutcome,
        history: list[Any],
    ) -> ModelRecord:
        now = datetime.now(UTC)
        version = now.strftime("%Y%m%d%H%M%S")
        artifact_dir = (
            Path(self._settings.model_artifacts_dir) / product_code / str(horizon_days) / version
        )
        artifact_dir.mkdir(parents=True, exist_ok=True)

        train_window_start = history[0].day
        train_window_end = history[-1].day
        metrics_json = {
            "mae": round(winner.mae, 6),
            "rmse": round(winner.rmse, 6),
            "smape": round(winner.smape, 6),
            "residual_std": round(winner.residual_std, 6),
            "folds": winner.folds,
        }

        artifact_path: Path
        if winner.model_type == "catboost":
            x_train, y_train = build_training_matrix(history)
            catboost_model = CatBoostDemandModel.train(x_train, y_train)
            artifact_path = artifact_dir / "model.cbm"
            catboost_model.save(artifact_path)

            metadata_path = artifact_dir / "metadata.json"
            feature_importance = catboost_model.feature_importance_map()
            metadata = {
                "feature_names": FEATURE_NAMES,
                "feature_importance": feature_importance,
                "residual_std": metrics_json["residual_std"],
                "trained_at": now.isoformat(),
            }
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            artifact_path = artifact_dir / "baseline.json"
            artifact_payload = {
                "model_type": "seasonal_naive",
                "seasonal_period": 7,
                "residual_std": metrics_json["residual_std"],
                "trained_at": now.isoformat(),
            }
            artifact_path.write_text(
                json.dumps(artifact_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        self._session.execute(
            update(ModelRecord)
            .where(
                ModelRecord.product_id == product_id,
                ModelRecord.horizon_days == horizon_days,
                ModelRecord.is_active.is_(True),
            )
            .values(is_active=False)
        )

        model_record = ModelRecord(
            product_id=product_id,
            horizon_days=horizon_days,
            model_type=winner.model_type,
            version=version,
            trained_at=now,
            train_window_start=train_window_start,
            train_window_end=train_window_end,
            metrics_json=metrics_json,
            artifact_path=str(artifact_path),
            is_active=True,
        )
        self._session.add(model_record)
        self._session.flush()
        return model_record

    def _write_backtest_report(
        self,
        *,
        product_code: str,
        horizon_days: int,
        window_type: WindowType,
        winner: str,
        comparison: dict[str, Any],
    ) -> Path:
        run_id = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        report_dir = (
            Path(self._settings.model_artifacts_dir)
            / "backtests"
            / product_code
            / str(horizon_days)
        )
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{run_id}.json"
        payload = {
            "run_id": run_id,
            "product_code": product_code,
            "horizon_days": horizon_days,
            "window_type": window_type,
            "winner": winner,
            "comparison": comparison,
            "created_at": datetime.now(UTC).isoformat(),
        }
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return report_path

    def _store_forecast_rows(
        self,
        *,
        product_id: Any,
        model_id: Any | None,
        horizon_days: int,
        scenario_name: str,
        scenario_params: dict[str, Any] | None,
        forecast_points: list[dict[str, Any]],
    ) -> None:
        forecast_date = datetime.now(UTC).date()
        for point in forecast_points:
            record = ForecastRecord(
                model_id=model_id,
                product_id=product_id,
                forecast_date=forecast_date,
                target_date=date.fromisoformat(point["target_date"]),
                horizon_days=horizon_days,
                scenario_name=scenario_name,
                scenario_params_json=scenario_params,
                y_hat=point["y_hat"],
                y_lo=point["y_lo"],
                y_hi=point["y_hi"],
            )
            self._session.add(record)
        self._session.commit()

    def _load_history(self, product_id: Any) -> list[Any]:
        rows = (
            self._session.execute(
                text(
                    """
                SELECT
                  date::date AS date,
                  volume_liters,
                  avg_retail_price_rub,
                  avg_purchase_price_rub,
                  gross_margin_rub_per_liter
                FROM vw_margin_daily
                WHERE product_id = :product_id
                ORDER BY date
                """
                ),
                {"product_id": product_id},
            )
            .mappings()
            .all()
        )
        return normalize_history_rows([dict(item) for item in rows])

    def _get_active_model(self, product_id: Any, horizon_days: int) -> ModelRecord | None:
        statement: Select[tuple[ModelRecord]] = (
            select(ModelRecord)
            .where(
                ModelRecord.product_id == product_id,
                ModelRecord.horizon_days == horizon_days,
                ModelRecord.is_active.is_(True),
            )
            .order_by(ModelRecord.trained_at.desc())
            .limit(1)
        )
        return self._session.scalar(statement)

    def _get_product(self, product_code: str) -> Product:
        statement: Select[tuple[Product]] = select(Product).where(Product.code == product_code)
        product = self._session.scalar(statement)
        if product is None:
            raise ValueError(f"Unknown product_code: {product_code}")
        return product

    @staticmethod
    def _target_dates(last_date: date, horizon_days: int) -> list[date]:
        return [last_date + timedelta(days=step) for step in range(1, horizon_days + 1)]

    @staticmethod
    def _scenario_delta_pct(scenario: dict[str, Any] | None) -> float:
        if scenario is None:
            return 0.0
        value = float(scenario.get("retail_price_delta_pct", 0.0))
        if value < -40.0 or value > 40.0:
            raise ValueError("scenario.retail_price_delta_pct must be between -40 and 40")
        return value

    @staticmethod
    def _normalize_product_code(product_code: str) -> str:
        normalized = product_code.strip().upper()
        if not normalized:
            raise ValueError("product_code is required")
        return normalized

    @staticmethod
    def _normalize_horizon_days(horizon_days: int) -> int:
        if horizon_days not in {1, 7, 30}:
            raise ValueError("horizon_days must be one of 1, 7, 30")
        return horizon_days

    @staticmethod
    def _normalize_window_type(window_type: str) -> WindowType:
        normalized = window_type.strip().lower()
        if normalized not in {"rolling", "expanding"}:
            raise ValueError("window_type must be one of rolling, expanding")
        return normalized  # type: ignore[return-value]

    def _build_reference_overlays(
        self,
        *,
        product_code: str,
        start_date: date,
        end_date: date,
    ) -> tuple[list[dict[str, Any]], str | None]:
        indicator_codes = [
            "crude_brent_usd",
            "usd_rub",
            self._resolve_wholesale_indicator(product_code),
            "event_pressure_score",
        ]
        try:
            rows_by_code = self._external_repository.get_points_with_mode(
                start_date=start_date,
                end_date=end_date,
                indicator_codes=indicator_codes,
            )
        except Exception:
            return [], None

        overlays: list[dict[str, Any]] = []
        modes: set[str] = set()
        for code in indicator_codes:
            rows = rows_by_code.get(code, [])
            if not rows:
                continue
            provider_mode = self._resolve_overlay_mode(rows)
            if provider_mode is not None:
                modes.add(provider_mode)
            overlays.append(
                {
                    "code": code,
                    "label": FORECAST_OVERLAY_LABELS.get(code, code),
                    "unit": rows[0].get("unit"),
                    "provider_mode": provider_mode,
                    "points": [
                        {
                            "date": row["indicator_date"].isoformat(),
                            "value": float(row["value_numeric"]),
                        }
                        for row in rows
                    ],
                }
            )
        return overlays, self._merge_modes(modes)

    @staticmethod
    def _resolve_wholesale_indicator(product_code: str) -> str:
        if product_code.startswith("DT_"):
            return "wholesale_diesel_index"
        return "wholesale_gasoline_index"

    @staticmethod
    def _resolve_overlay_mode(rows: list[dict[str, Any]]) -> str | None:
        modes = {str(row.get("provider_mode")).strip().lower() for row in rows if row.get("provider_mode")}
        return ForecastService._merge_modes(modes)

    @staticmethod
    def _merge_modes(modes: set[str]) -> str | None:
        if not modes:
            return None
        if "manual_snapshot" in modes:
            return "manual_snapshot"
        if "cached" in modes:
            return "cached"
        if modes == {"live"}:
            return "live"
        return None

    @staticmethod
    def _metric_float(metrics: dict[str, Any], key: str) -> float | None:
        value = metrics.get(key)
        if value is None:
            return None
        return float(value)

    def _build_catboost_drivers(self, model: ModelRecord, scenario_delta_pct: float) -> list[str]:
        metadata_path = Path(model.artifact_path).with_name("metadata.json")
        drivers: list[str] = []
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                importance: dict[str, float] = metadata.get("feature_importance", {})
                top_features = sorted(
                    importance.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:3]
                for feature_name, _ in top_features:
                    label = DRIVER_LABELS.get(feature_name)
                    if label is not None:
                        drivers.append(label)
            except Exception:
                drivers = []
        if not drivers:
            drivers = [
                "Лаги спроса остаются главным фактором прогноза.",
                "Календарные и ценовые признаки дополняют базовый тренд.",
            ]
        if scenario_delta_pct != 0:
            drivers.append(self._scenario_driver_text(scenario_delta_pct))
        return drivers

    def _build_baseline_drivers(self, scenario_delta_pct: float, *, fallback: bool) -> list[str]:
        drivers = [
            "Seasonal Naive baseline опирается на повторяемость недельного спроса.",
            "Модель не использует сложные нелинейные зависимости и служит надёжной базой.",
        ]
        if fallback:
            drivers.append("Активная ML-модель не найдена, поэтому используется baseline_fallback.")
        if scenario_delta_pct != 0:
            drivers.append(self._scenario_driver_text(scenario_delta_pct))
        return drivers

    @staticmethod
    def _scenario_driver_text(delta_pct: float) -> str:
        direction = "рост" if delta_pct > 0 else "снижение"
        return (
            f"Сценарий what-if учитывает {direction} розничной цены на "
            f"{abs(delta_pct):.2f}% только на горизонте прогноза."
        )
