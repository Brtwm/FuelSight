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

