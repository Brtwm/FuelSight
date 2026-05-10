from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

FRESH_MAX_AGE_DAYS = 2
WARNING_MAX_AGE_DAYS = 7


def confidence_for_mode(mode: str | None) -> float | None:
    if mode == "live":
        return 0.9
    if mode == "cached":
        return 0.75
    if mode == "manual_snapshot":
        return 0.6
    return None


def merge_modes(modes: set[str]) -> str | None:
    if not modes:
        return None
    if "manual_snapshot" in modes:
        return "manual_snapshot"
    if "cached" in modes:
        return "cached"
    if modes == {"live"}:
        return "live"
    return None


def resolve_data_freshness(rows: list[dict[str, Any]], date_key: str = "date") -> str:
    if not rows:
        return "degraded"
    points = [item[date_key] for item in rows if item.get(date_key) is not None]
    if not points:
        return "degraded"
    last_point = max(points)
    lag_days = max((datetime.now(UTC).date() - last_point).days, 0)
    if lag_days <= FRESH_MAX_AGE_DAYS:
        return "fresh"
    if lag_days <= WARNING_MAX_AGE_DAYS:
        return "warning"
    return "degraded"


def resolve_wholesale_indicator(product_code: str) -> str:
    if product_code.startswith("AI_"):
        return "wholesale_gasoline_index"
    return "wholesale_diesel_index"


def bucket_start(source: date, granularity: str) -> date:
    if granularity == "day":
        return source
    if granularity == "week":
        return source - timedelta(days=source.isoweekday() - 1)
    return source.replace(day=1)


def shift_one_year_back(value: date) -> date:
    try:
        return value.replace(year=value.year - 1)
    except ValueError:
        return value.replace(year=value.year - 1, day=28)


def pct_change(*, current: float | None, baseline: float | None) -> float | None:
    if current is None or baseline is None or baseline <= 0:
        return None
    return round(((current - baseline) / baseline) * 100.0, 4)


def normalize_product_code(product_code: str) -> str:
    normalized = product_code.strip().upper()
    if not normalized:
        raise ValueError("product_code is required")
    return normalized


def normalize_granularity(granularity: str) -> str:
    normalized = granularity.strip().lower()
    if normalized not in {"day", "week", "month"}:
        raise ValueError("granularity must be one of day, week, month")
    return normalized


def normalize_metric(metric: str) -> str:
    normalized = metric.strip().lower()
    if normalized not in {"sales", "margin", "purchase_price"}:
        raise ValueError("metric must be one of sales, margin, purchase_price")
    return normalized


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    if isinstance(value, Decimal):
        return float(value)
    return float(value)
