from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean, median, pstdev
from typing import Any

MAX_LAG = 28
ROLLING_WINDOWS = (7, 14, 28)
FEATURE_NAMES = [
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "rolling_mean_7",
    "rolling_median_7",
    "rolling_std_7",
    "rolling_mean_14",
    "rolling_median_14",
    "rolling_std_14",
    "rolling_mean_28",
    "rolling_median_28",
    "rolling_std_28",
    "weekday",
    "month",
    "is_weekend",
    "is_holiday_ru",
    "avg_retail_price_rub",
    "avg_purchase_price_rub",
    "gross_margin_rub_per_liter",
    "retail_price_change_pct",
    "crude_brent_usd",
    "usd_rub",
    "wholesale_gasoline_index",
    "wholesale_diesel_index",
    "holiday_flag",
    "event_pressure_score",
    "product_share_in_group",
    "group_volume_liters",
    "group_volume_lag_1",
    "group_volume_lag_7",
]

RU_HOLIDAYS_FIXED = {
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (1, 7),
    (1, 8),
    (2, 23),
    (3, 8),
    (5, 1),
    (5, 9),
    (6, 12),
    (11, 4),
}


@dataclass(frozen=True)
class HistoryPoint:
    day: date
    volume_liters: float
    avg_retail_price_rub: float
    avg_purchase_price_rub: float
    gross_margin_rub_per_liter: float
    crude_brent_usd: float = 0.0
    usd_rub: float = 0.0
    wholesale_gasoline_index: float = 0.0
    wholesale_diesel_index: float = 0.0
    holiday_flag: float = 0.0
    event_pressure_score: float = 0.0
    product_share_in_group: float = 0.0
    group_volume_liters: float = 0.0
    group_volume_lag_1: float = 0.0
    group_volume_lag_7: float = 0.0


def _to_float(value: Any, fallback: float) -> float:
    if value is None:
        return fallback
    return float(value)


def _is_russian_holiday(source: date) -> bool:
    return (source.month, source.day) in RU_HOLIDAYS_FIXED


def normalize_history_rows(rows: list[dict[str, Any]]) -> list[HistoryPoint]:
    points: list[HistoryPoint] = []
    for row in sorted(rows, key=lambda item: item["date"]):
        retail = _to_float(row.get("avg_retail_price_rub"), 0.0)
        purchase = _to_float(row.get("avg_purchase_price_rub"), retail * 0.9 if retail > 0 else 0.0)
        margin = _to_float(row.get("gross_margin_rub_per_liter"), retail - purchase)
        points.append(
            HistoryPoint(
                day=row["date"],
                volume_liters=_to_float(row.get("volume_liters"), 0.0),
                avg_retail_price_rub=retail,
                avg_purchase_price_rub=purchase,
                gross_margin_rub_per_liter=margin,
                crude_brent_usd=_to_float(row.get("crude_brent_usd"), 0.0),
                usd_rub=_to_float(row.get("usd_rub"), 0.0),
                wholesale_gasoline_index=_to_float(row.get("wholesale_gasoline_index"), 0.0),
                wholesale_diesel_index=_to_float(row.get("wholesale_diesel_index"), 0.0),
                holiday_flag=_to_float(row.get("holiday_flag"), 0.0),
                event_pressure_score=_to_float(row.get("event_pressure_score"), 0.0),
                product_share_in_group=_to_float(row.get("product_share_in_group"), 0.0),
                group_volume_liters=_to_float(row.get("group_volume_liters"), 0.0),
                group_volume_lag_1=_to_float(row.get("group_volume_lag_1"), 0.0),
                group_volume_lag_7=_to_float(row.get("group_volume_lag_7"), 0.0),
            )
        )
    return points


def _rolling_values(points: list[HistoryPoint], index: int, window: int) -> list[float]:
    start = index - window
    values = [item.volume_liters for item in points[start:index]]
    return values


def build_feature_vector(points: list[HistoryPoint], index: int) -> list[float]:
    if index < MAX_LAG:
        raise ValueError(f"Not enough history for features: need >= {MAX_LAG} days")
    if index >= len(points):
        raise ValueError("index is out of bounds")

    current = points[index]
    previous = points[index - 1]

    features: list[float] = [
        points[index - 1].volume_liters,
        points[index - 7].volume_liters,
        points[index - 14].volume_liters,
        points[index - 28].volume_liters,
    ]

    for window in ROLLING_WINDOWS:
        values = _rolling_values(points, index, window)
        features.extend(
            [
                mean(values),
                median(values),
                pstdev(values) if len(values) > 1 else 0.0,
            ]
        )

    retail_price_change_pct = 0.0
    if previous.avg_retail_price_rub > 0:
        retail_price_change_pct = (
            (current.avg_retail_price_rub - previous.avg_retail_price_rub)
            / previous.avg_retail_price_rub
        ) * 100.0

    features.extend(
        [
            float(current.day.isoweekday()),
            float(current.day.month),
            1.0 if current.day.isoweekday() >= 6 else 0.0,
            1.0 if _is_russian_holiday(current.day) else 0.0,
            current.avg_retail_price_rub,
            current.avg_purchase_price_rub,
            current.gross_margin_rub_per_liter,
            retail_price_change_pct,
            current.crude_brent_usd,
            current.usd_rub,
            current.wholesale_gasoline_index,
            current.wholesale_diesel_index,
            current.holiday_flag,
            current.event_pressure_score,
            current.product_share_in_group,
            current.group_volume_liters,
            current.group_volume_lag_1,
            current.group_volume_lag_7,
        ]
    )
    return features


def build_training_matrix(points: list[HistoryPoint]) -> tuple[list[list[float]], list[float]]:
    x_train: list[list[float]] = []
    y_train: list[float] = []
    for index in range(MAX_LAG, len(points) - 1):
        x_train.append(build_feature_vector(points, index))
        y_train.append(points[index + 1].volume_liters)
    return x_train, y_train


def scenario_demand_multiplier(delta_pct: float, elasticity: float = 0.25) -> float:
    normalized = max(-40.0, min(40.0, delta_pct))
    factor = 1.0 - (elasticity * normalized / 100.0)
    return max(0.2, factor)


def append_future_point(
    points: list[HistoryPoint],
    scenario_delta_pct: float = 0.0,
) -> HistoryPoint:
    if not points:
        raise ValueError("History points are required")
    last = points[-1]
    next_day = last.day + timedelta(days=1)
    next_retail = last.avg_retail_price_rub * (1.0 + scenario_delta_pct / 100.0)
    next_purchase = last.avg_purchase_price_rub
    next_margin = next_retail - next_purchase
    return HistoryPoint(
        day=next_day,
        volume_liters=last.volume_liters,
        avg_retail_price_rub=next_retail,
        avg_purchase_price_rub=next_purchase,
        gross_margin_rub_per_liter=next_margin,
        crude_brent_usd=last.crude_brent_usd,
        usd_rub=last.usd_rub,
        wholesale_gasoline_index=last.wholesale_gasoline_index,
        wholesale_diesel_index=last.wholesale_diesel_index,
        holiday_flag=last.holiday_flag,
        event_pressure_score=last.event_pressure_score,
        product_share_in_group=last.product_share_in_group,
        group_volume_liters=last.group_volume_liters,
        group_volume_lag_1=last.group_volume_lag_1,
        group_volume_lag_7=last.group_volume_lag_7,
    )
