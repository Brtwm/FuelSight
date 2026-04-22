from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import (
    DataProviderMode,
    DegradationStatus,
    FreshnessStatus,
    ProviderMode,
    QualityStatus,
    ReferenceOverlayPayload,
)

HorizonDays = Literal[1, 7, 30]
ModelType = Literal["catboost", "seasonal_naive"]
ModelStatus = Literal["active", "baseline_fallback"]


class ForecastScenario(BaseModel):
    retail_price_delta_pct: float = Field(ge=-40.0, le=40.0)


class ForecastRunRequest(BaseModel):
    product_code: str = Field(min_length=1)
    horizon_days: HorizonDays
    scenario: ForecastScenario | None = None

    @model_validator(mode="after")
    def _normalize(self) -> "ForecastRunRequest":
        self.product_code = self.product_code.strip().upper()
        return self


class ForecastPoint(BaseModel):
    target_date: date
    y_hat: float
    y_lo: float | None
    y_hi: float | None


class TrainingWindowPayload(BaseModel):
    start_date: date
    end_date: date


class ExternalContextQualityPayload(BaseModel):
    provider_mode: DataProviderMode | None = None
    coverage_ratio: float | None = None
    fallback_ratio: float | None = None
    quality_status: QualityStatus | None = None
    reasons: list[str] = Field(default_factory=list)
    manifest_run_date: str | None = None
    source_refs: list[dict[str, object]] = Field(default_factory=list)


class ForecastEventContextPayload(BaseModel):
    event_code: str
    title: str
    start_date: date
    end_date: date
    pressure_score: float
    demand_delta_pct: float
    purchase_delta_pct: float
    source_mode: str


class ForecastPayload(BaseModel):
    product_code: str
    horizon_days: HorizonDays
    model_type: ModelType
    model_status: ModelStatus
    scenario_name: str
    scenario_params: dict | None = None
    forecast_points: list[ForecastPoint]
    base_forecast_points: list[ForecastPoint] | None = None
    scenario_forecast_points: list[ForecastPoint] | None = None
    drivers: list[str]
    model_freshness: FreshnessStatus | None = None
    training_window: TrainingWindowPayload | None = None
    baseline_comparison: dict[str, dict[str, float]] | None = None
    feature_sources: list[str] | None = None
    retrain_status: DegradationStatus | None = None
    provider_mode: ProviderMode | None = None
    external_context_quality: ExternalContextQualityPayload | None = None
    event_context: list[ForecastEventContextPayload] = Field(default_factory=list)
    reference_overlays: list[ReferenceOverlayPayload] = Field(default_factory=list)
