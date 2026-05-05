from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

DefenseStatus = Literal["ok", "warning", "degraded", "failed"]
DefenseProfile = Literal["offline-safe", "cloud-enhanced"]


class DefenseStepPayload(BaseModel):
    name: str
    status: DefenseStatus
    details: str
    artifact_path: str | None = None


class DefenseBadgePayload(BaseModel):
    label: str
    status: DefenseStatus
    value: str


class DefenseReportPayload(BaseModel):
    run_id: str
    generated_at: str
    profile: DefenseProfile
    overall_status: DefenseStatus
    steps: list[DefenseStepPayload] = Field(default_factory=list)
    badges: list[DefenseBadgePayload] = Field(default_factory=list)
    data_quality: dict[str, object] = Field(default_factory=dict)
    model_quality: dict[str, object] = Field(default_factory=dict)
    provider_modes: dict[str, object] = Field(default_factory=dict)
    degradations: list[str] = Field(default_factory=list)
    executive_summary: dict[str, object] = Field(default_factory=dict)
    decision_journal: list[str] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
