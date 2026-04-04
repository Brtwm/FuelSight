from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.imports import GenerateDemoRequest


def test_generate_demo_request_normalizes_products() -> None:
    payload = GenerateDemoRequest(
        start_date="2025-01-01",
        end_date="2025-12-31",
        products=["ai_92", "AI_95", "AI_92", " dt "],
        seed=42,
        replace_existing=False,
    )

    assert payload.products == ["AI_92", "AI_95", "DT"]


def test_generate_demo_request_rejects_invalid_range() -> None:
    with pytest.raises(ValidationError):
        GenerateDemoRequest(
            start_date="2026-12-31",
            end_date="2026-01-01",
            products=["AI_95"],
            seed=42,
            replace_existing=False,
        )
