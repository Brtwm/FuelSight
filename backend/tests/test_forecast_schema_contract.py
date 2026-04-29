from __future__ import annotations

from pydantic import ValidationError

from app.schemas.forecasts import ForecastRunRequest


def test_forecast_scenario_rejects_non_price_delta_fields() -> None:
    try:
        ForecastRunRequest(
            product_code="AI_95",
            horizon_days=7,
            scenario={
                "retail_price_delta_pct": 2.5,
                "marketing_budget_delta_pct": 10.0,
            },
        )
    except ValidationError as exc:
        assert "marketing_budget_delta_pct" in str(exc)
    else:
        raise AssertionError("Expected unsupported scenario fields to be rejected")
