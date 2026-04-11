from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import (
    BusinessSummaryPayload,
    ChartAnnotationPayload,
    DataProviderMode,
    ReferenceOverlayPayload,
    SupportingRefPayload,
)

AnalyticsGranularity = Literal["day", "week", "month"]
AnalyticsMetric = Literal["sales", "margin", "purchase_price"]
AnalyticsSeverity = Literal["high", "medium", "low"]
AnalyticsDataMode = Literal["live", "cached", "degraded"]


class SalesSeriesPoint(BaseModel):
    period_start: date
    volume_liters: float
    avg_retail_price_rub: float | None


class SalesSeasonalityWeekday(BaseModel):
    weekday: str
    avg_volume_liters: float


class SalesSeasonalityMonth(BaseModel):
    month: int
    avg_volume_liters: float


class SalesSeasonality(BaseModel):
    by_weekday: list[SalesSeasonalityWeekday]
    by_month: list[SalesSeasonalityMonth]


class SalesComparisons(BaseModel):
    mom_pct: float | None
    yoy_pct: float | None


class SalesAnalyticsPayload(BaseModel):
    product_code: str
    granularity: AnalyticsGranularity
    series: list[SalesSeriesPoint]
    seasonality: SalesSeasonality
    comparisons: SalesComparisons


class MarginSeriesPoint(BaseModel):
    period_start: date
    avg_purchase_price_rub: float | None
    avg_retail_price_rub: float | None
    gross_margin_rub: float | None
    gross_margin_rub_per_liter: float | None
    gross_margin_pct: float | None
    purchase_data_missing: bool


class LowMarginDay(BaseModel):
    date: date
    gross_margin_rub_per_liter: float | None
    purchase_data_missing: bool


class MarginAnalyticsPayload(BaseModel):
    product_code: str
    granularity: AnalyticsGranularity
    series: list[MarginSeriesPoint]
    threshold_rub_per_liter: float
    below_threshold_days: int
    low_margin_days: list[LowMarginDay]


class AnalyticsAnomaly(BaseModel):
    date: date
    product_code: str
    metric: AnalyticsMetric
    severity: AnalyticsSeverity
    actual_value: float
    expected_range: tuple[float, float] | None = None
    possible_reasons: list[str]
    target_path: str


class SalesAnalyticsMeta(BaseModel):
    business_summary: BusinessSummaryPayload | None = None
    chart_annotations: list[ChartAnnotationPayload] = Field(default_factory=list)
    reference_overlays: list[ReferenceOverlayPayload] = Field(default_factory=list)
    data_mode: AnalyticsDataMode | None = None
    provider_mode: DataProviderMode | None = None


class MarginAnalyticsMeta(BaseModel):
    business_summary: BusinessSummaryPayload | None = None
    chart_annotations: list[ChartAnnotationPayload] = Field(default_factory=list)
    reference_overlays: list[ReferenceOverlayPayload] = Field(default_factory=list)
    threshold_info: str | None = None
    supporting_refs: list[SupportingRefPayload] = Field(default_factory=list)
    provider_mode: DataProviderMode | None = None
