from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.forecasts import HorizonDays, ModelType

WindowType = Literal["rolling", "expanding"]


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


class BacktestPayload(BaseModel):
    product_code: str
    horizon_days: HorizonDays
    model_type: ModelType
    window_type: WindowType
    metrics: BacktestMetrics
    comparison: dict[str, BacktestMetrics]
    trained_at: datetime
    model_version: str | None = None
