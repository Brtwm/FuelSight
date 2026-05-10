from datetime import date

import pytest

from app.services.analytics_helpers import (
    bucket_start,
    merge_modes,
    normalize_granularity,
    normalize_metric,
    normalize_product_code,
    pct_change,
    resolve_wholesale_indicator,
)


def test_analytics_helpers_keep_business_rules_small_and_explicit() -> None:
    assert merge_modes({"live"}) == "live"
    assert merge_modes({"live", "cached"}) == "cached"
    assert merge_modes({"live", "manual_snapshot"}) == "manual_snapshot"
    assert resolve_wholesale_indicator("AI_95") == "wholesale_gasoline_index"
    assert resolve_wholesale_indicator("DT_W") == "wholesale_diesel_index"
    assert bucket_start(date(2026, 5, 6), "week") == date(2026, 5, 4)
    assert pct_change(current=120.0, baseline=100.0) == 20.0


def test_analytics_helpers_validate_small_enums() -> None:
    assert normalize_product_code(" ai_92 ") == "AI_92"
    assert normalize_granularity("Week") == "week"
    assert normalize_metric("Margin") == "margin"

    with pytest.raises(ValueError):
        normalize_granularity("quarter")
