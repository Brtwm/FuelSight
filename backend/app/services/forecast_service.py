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
from ml.backtesting import BacktestOutcome, run_rolling_backtest, select_best_outcome
from ml.features import FEATURE_NAMES, MAX_LAG, build_training_matrix, normalize_history_rows
from ml.inference import forecast_with_baseline, forecast_with_catboost
from ml.models import CatBoostDemandModel, is_catboost_available

ModelType = Literal["catboost", "seasonal_naive"]
WindowType = Literal["rolling", "expanding"]

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
                model_status = "active"

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
            },
            meta={
                "points": len(forecast_points),
                "scenario_delta_pct": scenario_delta,
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
        model_id = rows[0]["model_id"]
        if model_id is not None:
            model = self._session.get(ModelRecord, model_id)
            if model is not None:
                model_type = model.model_type  # type: ignore[assignment]
                model_status = "active"
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
            },
            meta={
                "forecast_date": latest["forecast_date"].isoformat(),
                "points": len(forecast_points),
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

        outcomes: list[BacktestOutcome] = []
        baseline_outcome = run_rolling_backtest(
            history,
            model_type="seasonal_naive",
            horizon_days=normalized_horizon,
            window_type=normalized_window,
        )
        outcomes.append(baseline_outcome)

        if is_catboost_available():
            try:
                catboost_outcome = run_rolling_backtest(
                    history,
                    model_type="catboost",
                    horizon_days=normalized_horizon,
                    window_type=normalized_window,
                )
                outcomes.append(catboost_outcome)
            except ValueError:
                pass

        winner = select_best_outcome(outcomes)
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
            metrics_json={
                "winner": winner.model_type,
                "winner_metrics": winner_metrics,
                "comparison": comparison,
                "folds": winner.folds,
                "residual_std": round(winner.residual_std, 6),
                "model_version": trained_model.version,
            },
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
            },
            meta={"folds": winner.folds},
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
            },
            meta={"status": latest.status},
        )

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
