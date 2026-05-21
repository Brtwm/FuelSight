from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExecutiveReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def _validate_period(self) -> "ExecutiveReportRequest":
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must be less than or equal to date_to")
        return self


class ExecutiveReportPeriod(BaseModel):
    date_from: date
    date_to: date


class ExecutiveReportKpi(BaseModel):
    revenue_rub: float
    sales_volume_liters: float
    gross_margin_rub: float
    gross_margin_pct: float


class ExecutiveProblemProduct(BaseModel):
    product_code: str
    product_name: str
    reason: str
    margin_pct: float
    recommendation: str


class ExecutiveDemandForecastItem(BaseModel):
    product_code: str
    product_name: str
    forecast_period: str
    forecast_volume_liters: float
    risk_level: Literal["low", "medium", "high"]


class ExecutiveMarginRisk(BaseModel):
    product_code: str
    risk: str
    impact: str
    recommendation: str


class ExecutiveMarketContextItem(BaseModel):
    title: str
    summary: str
    source: str | None = None
    published_at: datetime | None = None


class ExecutiveDataQuality(BaseModel):
    has_sales_data: bool
    has_purchase_data: bool
    has_forecast_data: bool
    has_news_data: bool
    warnings: list[str] = Field(default_factory=list)


class ExecutiveReportPayload(BaseModel):
    report_id: str
    generated_at: datetime
    period: ExecutiveReportPeriod
    executive_summary: str
    kpi: ExecutiveReportKpi
    problem_products: list[ExecutiveProblemProduct] = Field(default_factory=list)
    demand_forecast: list[ExecutiveDemandForecastItem] = Field(default_factory=list)
    margin_risks: list[ExecutiveMarginRisk] = Field(default_factory=list)
    market_context: list[ExecutiveMarketContextItem] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    data_quality: ExecutiveDataQuality
