from __future__ import annotations

import math
from datetime import date, timedelta

import pytest

from ml.features import (
    FEATURE_NAMES,
    MAX_LAG,
    HistoryPoint,
    append_future_point,
    build_feature_vector,
)


def test_feature_vector_includes_cyclical_calendar_features() -> None:
    start = date(2026, 1, 1)
    points = [
        HistoryPoint(
            day=start + timedelta(days=index),
            volume_liters=1000.0 + index,
            avg_retail_price_rub=58.0,
            avg_purchase_price_rub=50.0,
            gross_margin_rub_per_liter=8.0,
        )
        for index in range(MAX_LAG + 1)
    ]

    vector = build_feature_vector(points, MAX_LAG)
    values = dict(zip(FEATURE_NAMES, vector, strict=True))
    expected_weekday_angle = 2 * math.pi * (points[MAX_LAG].day.isoweekday() - 1) / 7
    expected_doy_angle = 2 * math.pi * (points[MAX_LAG].day.timetuple().tm_yday - 1) / 366

    assert values["weekday_sin"] == pytest.approx(math.sin(expected_weekday_angle))
    assert values["weekday_cos"] == pytest.approx(math.cos(expected_weekday_angle))
    assert values["day_of_year_sin"] == pytest.approx(math.sin(expected_doy_angle))
    assert values["day_of_year_cos"] == pytest.approx(math.cos(expected_doy_angle))


def test_append_future_point_recomputes_fixed_holiday_flag() -> None:
    point = HistoryPoint(
        day=date(2026, 1, 8),
        volume_liters=1000.0,
        avg_retail_price_rub=58.0,
        avg_purchase_price_rub=50.0,
        gross_margin_rub_per_liter=8.0,
        holiday_flag=1.0,
    )

    future = append_future_point([point])

    assert future.day == date(2026, 1, 9)
    assert future.holiday_flag == 0.0
