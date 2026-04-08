from __future__ import annotations

from app.models.external_indicator_daily import ExternalIndicatorDaily
from sqlalchemy import UniqueConstraint


def test_external_indicators_daily_has_unique_date_code_provider_constraint() -> None:
    table = ExternalIndicatorDaily.__table__
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]
    assert unique_constraints

    target = next(
        (
            constraint
            for constraint in unique_constraints
            if constraint.name == "uq_external_indicators_daily_date_code_provider"
        ),
        None,
    )
    assert target is not None
    assert {column.name for column in target.columns} == {
        "indicator_date",
        "indicator_code",
        "provider_name",
    }
