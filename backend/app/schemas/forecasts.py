from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import DegradationStatus, FreshnessStatus, ProviderMode

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


class ForecastPayload(BaseModel):
    product_code: str
    horizon_days: HorizonDays
    model_type: ModelType
    model_status: ModelStatus
    scenario_name: str
    scenario_params: dict | None = None
    forecast_points: list[ForecastPoint]
    drivers: list[str]
    model_freshness: FreshnessStatus | None = None
    training_window: TrainingWindowPayload | None = None
    baseline_comparison: dict[str, dict[str, float]] | None = None
    feature_sources: list[str] | None = None
    retrain_status: DegradationStatus | None = None
    provider_mode: ProviderMode | None = None
