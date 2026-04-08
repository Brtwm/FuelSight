from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import (
    BusinessSummaryPayload,
    ChartAnnotationPayload,
    FreshnessStatus,
    ReferenceOverlayPayload,
)

AlertSeverity = Literal["high", "medium", "low"]
AlertType = Literal["low_margin", "purchase_spike", "demand_anomaly"]


class KpiSummary(BaseModel):
    sales_volume_liters: float
    revenue_rub: float
    gross_margin_rub: float
    gross_margin_pct: float | None
    low_margin_days: int
    anomaly_count: int


class KpiAlert(BaseModel):
    type: AlertType
    severity: AlertSeverity
    date: date
    product_code: str
    message: str
    metric: str
    actual_value: float
    expected_range: tuple[float, float] | None = None
    target_path: str


class KpiSnapshotPoint(BaseModel):
    date: date
    volume_liters: float
    avg_retail_price_rub: float | None


class KpiSummaryMeta(BaseModel):
    business_summary: BusinessSummaryPayload | None = None
    data_freshness: FreshnessStatus | None = None
    margin_coverage_days: int | None = None
    margin_missing_days: int | None = None


class KpiSnapshotMeta(BaseModel):
    business_summary: BusinessSummaryPayload | None = None
    chart_annotations: list[ChartAnnotationPayload] = Field(default_factory=list)
    reference_overlays: list[ReferenceOverlayPayload] = Field(default_factory=list)
