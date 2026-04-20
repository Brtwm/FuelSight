from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, Field

DataProviderMode: TypeAlias = Literal["live", "cached", "manual_snapshot"]
ProviderMode: TypeAlias = Literal[
    "live",
    "cached",
    "manual_snapshot",
    "cloud_llm",
    "local_llm",
    "retrieval_only",
]
FreshnessStatus: TypeAlias = Literal["fresh", "warning", "degraded"]
DegradationStatus: TypeAlias = Literal["ok", "warning", "degraded", "failed"]
QualityStatus: TypeAlias = Literal["ok", "warning", "degraded", "failed"]
DisplayLabelCode: TypeAlias = Literal["sales", "purchases", "initial_history"]
ExplainabilityStateStatus: TypeAlias = Literal["ready", "empty", "degraded", "error"]


class BusinessSummaryPayload(BaseModel):
    title: str | None = None
    summary: str | None = None
    bullets: list[str] = Field(default_factory=list)


class ChartAnnotationPayload(BaseModel):
    id: str
    date: str | None = None
    label: str
    severity: str | None = None
    message: str | None = None


class ReferenceOverlayPayload(BaseModel):
    code: str
    label: str
    unit: str | None = None
    provider_mode: ProviderMode | None = None
    points: list[dict[str, str | float | int | None]] = Field(default_factory=list)


class SupportingRefPayload(BaseModel):
    type: str
    ref_id: str
    title: str
    provider_mode: ProviderMode | None = None
    confidence: float | None = None
    source_type: str | None = None


class ExplainabilityThresholdPayload(BaseModel):
    id: str
    label: str
    value: float | None = None
    unit: str | None = None
    severity: str | None = None
    description: str | None = None


class ExplainabilityChartPayload(BaseModel):
    annotations: list[ChartAnnotationPayload] = Field(default_factory=list)
    overlays: list[ReferenceOverlayPayload] = Field(default_factory=list)
    thresholds: list[ExplainabilityThresholdPayload] = Field(default_factory=list)
    supporting_refs: list[SupportingRefPayload] = Field(default_factory=list)


class ExplainabilityTrustPayload(BaseModel):
    data_freshness: FreshnessStatus | None = None
    mode: DataProviderMode | None = None
    data_mode: str | None = None
    external_context: dict[str, object] | None = None


class ExplainabilityStatePayload(BaseModel):
    status: ExplainabilityStateStatus = "ready"
    reason: str | None = None


class ExplainabilityPayload(BaseModel):
    summary: BusinessSummaryPayload | None = None
    chart: ExplainabilityChartPayload = Field(default_factory=ExplainabilityChartPayload)
    trust: ExplainabilityTrustPayload = Field(default_factory=ExplainabilityTrustPayload)
    state: ExplainabilityStatePayload = Field(default_factory=ExplainabilityStatePayload)
