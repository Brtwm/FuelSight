from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import DegradationStatus, FreshnessStatus, ProviderMode
from app.schemas.forecasts import HorizonDays, ModelType, TrainingWindowPayload

WindowType = Literal["rolling", "expanding"]
ValidationStatus = Literal["OK", "LIMITED", "UNKNOWN"]


class BacktestRunRequest(BaseModel):
    product_code: str = Field(min_length=1)
    horizon_days: HorizonDays
    window_type: WindowType = "rolling"

    @model_validator(mode="after")
    def _normalize(self) -> "BacktestRunRequest":
        self.product_code = self.product_code.strip().upper()
        return self


class BacktestMetrics(BaseModel):
    mae: float
    rmse: float
    smape: float


class ValidationPeriod(BaseModel):
    start: date | None = None
    end: date | None = None


class ValidationObservations(BaseModel):
    total: int | None = None
    train: int | None = None
    test: int | None = None


class ValidationMetricValues(BaseModel):
    mae: float | None = None
    rmse: float | None = None
    smape: float | None = None


class ValidationImprovement(BaseModel):
    mae_pct: float | None = None
    rmse_pct: float | None = None
    smape_pct: float | None = None


class ValidationMetrics(BaseModel):
    catboost: ValidationMetricValues | None = None
    seasonal_naive: ValidationMetricValues | None = None
    improvement: ValidationImprovement | None = None


class ValidationSeriesPoint(BaseModel):
    date: date
    actual: float | None = None
    catboost_prediction: float | None = None
    seasonal_naive_prediction: float | None = None


class ValidationSummary(BaseModel):
    status: ValidationStatus
    status_reason: str
    train_period: ValidationPeriod | None = None
    test_period: ValidationPeriod | None = None
    observations: ValidationObservations | None = None
    metrics: ValidationMetrics | None = None
    series: list[ValidationSeriesPoint] = Field(default_factory=list)


class BacktestPayload(BaseModel):
    product_code: str
    horizon_days: HorizonDays
    model_type: ModelType
    window_type: WindowType
    metrics: BacktestMetrics
    comparison: dict[str, BacktestMetrics]
    trained_at: datetime
    model_version: str | None = None
    model_freshness: FreshnessStatus | None = None
    training_window: TrainingWindowPayload | None = None
    baseline_comparison: dict[str, dict[str, float]] | None = None
    feature_sources: list[str] | None = None
    retrain_status: DegradationStatus | None = None
    provider_mode: ProviderMode | None = None
    validation_summary: ValidationSummary | None = None
