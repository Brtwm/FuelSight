from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import DataProviderMode, DisplayLabelCode, QualityStatus

ImportJobStatus = Literal["queued", "processing", "completed", "completed_with_errors", "failed"]
ImportEntityType = Literal["sales", "purchases", "historical_data"]


class ImportQueuedResponse(BaseModel):
    job_id: UUID
    entity_type: ImportEntityType
    status: ImportJobStatus
    display_label: DisplayLabelCode | None = None
    provenance_mode: DataProviderMode | None = None
    quality_status: QualityStatus | None = None


class GenerateDemoRequest(BaseModel):
    start_date: date
    end_date: date
    products: list[str] = Field(min_length=1)
    seed: int = 42
    replace_existing: bool = False

    @model_validator(mode="after")
    def validate_range(self) -> "GenerateDemoRequest":
        if self.start_date > self.end_date:
            raise ValueError("start_date must be earlier than end_date")
        normalized_codes = [code.upper().strip() for code in self.products if code.strip()]
        if not normalized_codes:
            raise ValueError("products must contain at least one value")
        self.products = list(dict.fromkeys(normalized_codes))
        return self


class ImportJobSummary(BaseModel):
    id: UUID
    entity_type: str
    source_type: str
    file_name: str | None
    status: ImportJobStatus
    rows_total: int
    rows_success: int
    rows_failed: int
    error_report_path: str | None
    started_at: datetime
    finished_at: datetime | None
    display_label: DisplayLabelCode | None = None
    provenance_mode: DataProviderMode | None = None
    quality_status: QualityStatus | None = None


class ImportJobDetails(ImportJobSummary):
    started_by: UUID
