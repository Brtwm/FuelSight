from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.imports import GenerateDemoRequest


def test_generate_demo_request_normalizes_products() -> None:
    payload = GenerateDemoRequest(
        start_date="2025-01-01",
        end_date="2025-12-31",
        products=["ai_92", "AI_95", "AI_92", " dt_s "],
        seed=42,
        replace_existing=False,
    )

    assert payload.products == ["AI_92", "AI_95", "DT_S"]


def test_generate_demo_request_rejects_invalid_range() -> None:
    with pytest.raises(ValidationError):
        GenerateDemoRequest(
            start_date="2026-12-31",
            end_date="2026-01-01",
            products=["AI_95"],
            seed=42,
            replace_existing=False,
        )


def test_generate_demo_request_rejects_unknown_product_codes() -> None:
    with pytest.raises(ValidationError) as exc_info:
        GenerateDemoRequest(
            start_date="2025-01-01",
            end_date="2025-12-31",
            products=["AI_95", "DT"],
            seed=42,
            replace_existing=False,
        )

    assert "unsupported product codes" in str(exc_info.value)
