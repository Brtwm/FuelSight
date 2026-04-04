from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from threading import Lock
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings

AlertSeverity = Literal["high", "medium", "low"]
AlertType = Literal["low_margin", "purchase_spike", "demand_anomaly"]

SEVERITY_RANK: dict[AlertSeverity, int] = {"high": 3, "medium": 2, "low": 1}
DEFAULT_DATE_RANGE_DAYS = 30
PURCHASE_SPIKE_PCT_THRESHOLD = 8.0
PURCHASE_SPIKE_PCT_HIGH = 15.0
DEMAND_ZSCORE_THRESHOLD = 2.0
DEMAND_ZSCORE_HIGH = 3.0


@dataclass(frozen=True)
class DateRange:
    date_from: date
    date_to: date


@dataclass(frozen=True)
class CacheEntry:
    expires_at: datetime
    payload: Any


@dataclass(frozen=True)
class SummaryResult:
    data: dict[str, Any] | None
    meta: dict[str, Any]


@dataclass(frozen=True)
class AlertsResult:
    data: list[dict[str, Any]]
    meta: dict[str, Any]


@dataclass(frozen=True)
class SnapshotResult:
    data: list[dict[str, Any]]
    meta: dict[str, Any]


class KpiService:
    _cache: dict[tuple[Any, ...], CacheEntry] = {}
    _cache_lock = Lock()
    _cache_ttl_seconds = 60

    def __init__(self, session: Session, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    def get_summary(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str | None,
    ) -> SummaryResult:
        date_range = self._resolve_date_range(date_from=date_from, date_to=date_to)
        normalized_code = self._normalize_product_code(product_code)
        cache_key = (
            "kpi_summary",
            date_range.date_from.isoformat(),
            date_range.date_to.isoformat(),
            normalized_code,
            self._settings.kpi_low_margin_threshold_rub_per_liter,
        )
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        sales_rows = self._query_sales_daily(date_range=date_range, product_code=normalized_code)
        if not sales_rows:
            empty_result = SummaryResult(
                data=None,
                meta={
                    "date_from": date_range.date_from.isoformat(),
                    "date_to": date_range.date_to.isoformat(),
                    "product_code": normalized_code,
                    "empty_state": "Нет данных за выбранный период. Загрузите импорт на /import.",
                },
            )
            self._cache_set(cache_key, empty_result)
            return empty_result

        margin_rows = self._query_margin_daily(date_range=date_range, product_code=normalized_code)
        purchase_rows = self._query_purchase_daily(
            date_range=date_range,
            product_code=normalized_code,
        )
        sales_by_product = self._query_sales_by_product_daily(
            date_range=date_range, product_code=normalized_code
        )

        margin_days = {row["date"] for row in margin_rows if not row["purchase_data_missing"]}
        sales_days = {row["date"] for row in sales_rows}
        covered_margin_rows = [row for row in margin_rows if not row["purchase_data_missing"]]

        sales_volume = sum(float(row["volume_liters"]) for row in sales_rows)
        revenue = sum(float(row["revenue_rub"]) for row in sales_rows)
        gross_margin_rub = sum(float(row["gross_margin_rub"]) for row in covered_margin_rows)
        covered_revenue = sum(float(row["revenue_rub"]) for row in covered_margin_rows)
        gross_margin_pct = (
            (gross_margin_rub / covered_revenue * 100.0) if covered_revenue > 0 else None
        )

        low_margin_alerts = self._build_low_margin_alerts(covered_margin_rows)
        purchase_spike_alerts = self._build_purchase_spike_alerts(purchase_rows)
        demand_anomaly_alerts = self._build_demand_anomaly_alerts(sales_by_product)

        summary = {
            "sales_volume_liters": round(sales_volume, 3),
            "revenue_rub": round(revenue, 2),
            "gross_margin_rub": round(gross_margin_rub, 2),
            "gross_margin_pct": None if gross_margin_pct is None else round(gross_margin_pct, 2),
            "low_margin_days": len({row["date"] for row in low_margin_alerts}),
            "anomaly_count": len(low_margin_alerts)
            + len(purchase_spike_alerts)
            + len(demand_anomaly_alerts),
        }
        result = SummaryResult(
            data=summary,
            meta={
                "date_from": date_range.date_from.isoformat(),
                "date_to": date_range.date_to.isoformat(),
                "product_code": normalized_code,
                "margin_coverage_days": len(margin_days),
                "margin_missing_days": max(len(sales_days) - len(margin_days), 0),
            },
        )
        self._cache_set(cache_key, result)
        return result

    def get_alerts(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str | None,
        severity: AlertSeverity | None,
    ) -> AlertsResult:
        date_range = self._resolve_date_range(date_from=date_from, date_to=date_to)
        normalized_code = self._normalize_product_code(product_code)
        cache_key = (
            "kpi_alerts",
            date_range.date_from.isoformat(),
            date_range.date_to.isoformat(),
            normalized_code,
            severity,
            self._settings.kpi_low_margin_threshold_rub_per_liter,
        )
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        margin_rows = self._query_margin_daily(date_range=date_range, product_code=normalized_code)
        purchase_rows = self._query_purchase_daily(
            date_range=date_range,
            product_code=normalized_code,
        )
        sales_by_product = self._query_sales_by_product_daily(
            date_range=date_range, product_code=normalized_code
        )
        alerts = [
            *self._build_low_margin_alerts(
                [row for row in margin_rows if not row["purchase_data_missing"]]
            ),
            *self._build_purchase_spike_alerts(purchase_rows),
            *self._build_demand_anomaly_alerts(sales_by_product),
        ]
        if severity is not None:
            alerts = [item for item in alerts if item["severity"] == severity]

        alerts.sort(
            key=lambda item: (
                -SEVERITY_RANK[item["severity"]],
                -item["date"].toordinal(),
                item["type"],
            ),
            reverse=False,
        )
        result = AlertsResult(
            data=alerts,
            meta={
                "date_from": date_range.date_from.isoformat(),
                "date_to": date_range.date_to.isoformat(),
                "product_code": normalized_code,
                "severity": severity,
                "count": len(alerts),
            },
        )
        self._cache_set(cache_key, result)
        return result

    def get_snapshot(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str | None,
    ) -> SnapshotResult:
        date_range = self._resolve_date_range(date_from=date_from, date_to=date_to)
        normalized_code = self._normalize_product_code(product_code)
        cache_key = (
            "kpi_snapshot",
            date_range.date_from.isoformat(),
            date_range.date_to.isoformat(),
            normalized_code,
        )
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        rows = self._query_sales_daily(date_range=date_range, product_code=normalized_code)
        snapshot = [
            {
                "date": row["date"],
                "volume_liters": round(float(row["volume_liters"]), 3),
                "avg_retail_price_rub": None
                if row["avg_retail_price_rub"] is None
                else round(float(row["avg_retail_price_rub"]), 4),
            }
            for row in rows
        ]
        result = SnapshotResult(
            data=snapshot,
            meta={
                "date_from": date_range.date_from.isoformat(),
                "date_to": date_range.date_to.isoformat(),
                "product_code": normalized_code,
                "points": len(snapshot),
            },
        )
        self._cache_set(cache_key, result)
        return result

    def _query_sales_daily(
        self,
        *,
        date_range: DateRange,
        product_code: str | None,
    ) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT
              sd.sale_date::date AS date,
              SUM(sd.volume_liters)::numeric AS volume_liters,
              SUM(sd.revenue_rub)::numeric AS revenue_rub,
              CASE
                WHEN SUM(sd.volume_liters) > 0
                THEN (SUM(sd.revenue_rub) / SUM(sd.volume_liters))::numeric
                ELSE NULL
              END AS avg_retail_price_rub
            FROM sales_daily sd
            JOIN products p ON p.id = sd.product_id
            WHERE sd.sale_date BETWEEN :date_from AND :date_to
              AND (CAST(:product_code AS VARCHAR) IS NULL OR p.code = :product_code)
            GROUP BY sd.sale_date
            ORDER BY sd.sale_date
            """
        )
        return self._execute_mapping_query(
            query=query,
            date_range=date_range,
            product_code=product_code,
        )

    def _query_sales_by_product_daily(
        self,
        *,
        date_range: DateRange,
        product_code: str | None,
    ) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT
              sd.sale_date::date AS date,
              p.code AS product_code,
              SUM(sd.volume_liters)::numeric AS volume_liters
            FROM sales_daily sd
            JOIN products p ON p.id = sd.product_id
            WHERE sd.sale_date BETWEEN :date_from AND :date_to
              AND (CAST(:product_code AS VARCHAR) IS NULL OR p.code = :product_code)
            GROUP BY sd.sale_date, p.code
            ORDER BY p.code, sd.sale_date
            """
        )
        return self._execute_mapping_query(
            query=query,
            date_range=date_range,
            product_code=product_code,
        )

    def _query_purchase_daily(
        self,
        *,
        date_range: DateRange,
        product_code: str | None,
    ) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT
              pd.purchase_date::date AS date,
              p.code AS product_code,
              CASE
                WHEN SUM(pd.volume_liters) > 0
                THEN (
                  SUM(pd.volume_liters * pd.purchase_price_rub) / SUM(pd.volume_liters)
                )::numeric
                ELSE NULL
              END AS avg_purchase_price_rub
            FROM purchases_daily pd
            JOIN products p ON p.id = pd.product_id
            WHERE pd.purchase_date BETWEEN :date_from AND :date_to
              AND (CAST(:product_code AS VARCHAR) IS NULL OR p.code = :product_code)
            GROUP BY pd.purchase_date, p.code
            ORDER BY p.code, pd.purchase_date
            """
        )
        return self._execute_mapping_query(
            query=query,
            date_range=date_range,
            product_code=product_code,
        )

    def _query_margin_daily(
        self,
        *,
        date_range: DateRange,
        product_code: str | None,
    ) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT
              date::date AS date,
              product_code,
              volume_liters,
              revenue_rub,
              avg_retail_price_rub,
              avg_purchase_price_rub,
              purchase_data_missing,
              gross_margin_rub,
              gross_margin_rub_per_liter,
              gross_margin_pct
            FROM vw_margin_daily
            WHERE date BETWEEN :date_from AND :date_to
              AND (CAST(:product_code AS VARCHAR) IS NULL OR product_code = :product_code)
            ORDER BY date, product_code
            """
        )
        return self._execute_mapping_query(
            query=query,
            date_range=date_range,
            product_code=product_code,
        )

    def _build_low_margin_alerts(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        threshold = self._settings.kpi_low_margin_threshold_rub_per_liter
        alerts: list[dict[str, Any]] = []
        for row in rows:
            margin_value = self._to_float(row.get("gross_margin_rub_per_liter"))
            if margin_value is None or margin_value >= threshold:
                continue
            severity: AlertSeverity = "high" if margin_value <= (threshold * 0.5) else "medium"
            alerts.append(
                {
                    "type": "low_margin",
                    "severity": severity,
                    "date": row["date"],
                    "product_code": row["product_code"],
                    "message": (
                        f"Маржа {margin_value:.2f} руб/л ниже порога {threshold:.2f} руб/л"
                    ),
                    "metric": "margin",
                    "actual_value": round(margin_value, 4),
                    "expected_range": (round(threshold, 4), round(threshold * 1.5, 4)),
                    "target_path": "/analytics/margin",
                }
            )
        return alerts

    def _build_purchase_spike_alerts(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["product_code"]].append(row)
        for code in grouped:
            grouped[code].sort(key=lambda item: item["date"])

        alerts: list[dict[str, Any]] = []
        for product_code, product_rows in grouped.items():
            previous_price: float | None = None
            previous_date: date | None = None
            for row in product_rows:
                current_price = self._to_float(row.get("avg_purchase_price_rub"))
                if current_price is None:
                    continue
                if previous_price is None or previous_price <= 0:
                    previous_price = current_price
                    previous_date = row["date"]
                    continue
                delta_pct = ((current_price - previous_price) / previous_price) * 100.0
                if delta_pct >= PURCHASE_SPIKE_PCT_THRESHOLD:
                    severity: AlertSeverity = (
                        "high" if delta_pct >= PURCHASE_SPIKE_PCT_HIGH else "medium"
                    )
                    alerts.append(
                        {
                            "type": "purchase_spike",
                            "severity": severity,
                            "date": row["date"],
                            "product_code": product_code,
                            "message": (
                                f"Закупочная цена выросла на {delta_pct:.1f}%"
                                f" к {previous_date.isoformat()}"
                            ),
                            "metric": "purchase_price",
                            "actual_value": round(current_price, 4),
                            "expected_range": (
                                round(previous_price * 0.92, 4),
                                round(previous_price * 1.08, 4),
                            ),
                            "target_path": "/analytics/margin",
                        }
                    )
                previous_price = current_price
                previous_date = row["date"]
        return alerts

    def _build_demand_anomaly_alerts(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["product_code"]].append(row)

        alerts: list[dict[str, Any]] = []
        for product_code, product_rows in grouped.items():
            volumes = [self._to_float(row.get("volume_liters")) for row in product_rows]
            valid = [value for value in volumes if value is not None]
            if len(valid) < 7:
                continue
            mean_value = sum(valid) / len(valid)
            variance = sum((value - mean_value) ** 2 for value in valid) / len(valid)
            stddev = variance**0.5
            if stddev <= 0:
                continue
            for row in product_rows:
                actual = self._to_float(row.get("volume_liters"))
                if actual is None:
                    continue
                zscore = (actual - mean_value) / stddev
                if abs(zscore) < DEMAND_ZSCORE_THRESHOLD:
                    continue
                severity: AlertSeverity = "high" if abs(zscore) >= DEMAND_ZSCORE_HIGH else "medium"
                direction = "выше" if zscore > 0 else "ниже"
                expected_lo = mean_value - (DEMAND_ZSCORE_THRESHOLD * stddev)
                expected_hi = mean_value + (DEMAND_ZSCORE_THRESHOLD * stddev)
                alerts.append(
                    {
                        "type": "demand_anomaly",
                        "severity": severity,
                        "date": row["date"],
                        "product_code": product_code,
                        "message": (f"Спрос {direction} ожиданий: z-score {zscore:.2f}"),
                        "metric": "sales",
                        "actual_value": round(actual, 3),
                        "expected_range": (round(expected_lo, 3), round(expected_hi, 3)),
                        "target_path": "/analytics/sales",
                    }
                )
        return alerts

    @staticmethod
    def _normalize_product_code(product_code: str | None) -> str | None:
        if product_code is None:
            return None
        normalized = product_code.strip().upper()
        return normalized or None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, float):
            return value
        if isinstance(value, int):
            return float(value)
        if isinstance(value, Decimal):
            return float(value)
        return float(value)

    @staticmethod
    def _base_params(date_range: DateRange, product_code: str | None) -> dict[str, Any]:
        return {
            "date_from": date_range.date_from,
            "date_to": date_range.date_to,
            "product_code": product_code,
        }

    def _execute_mapping_query(
        self,
        *,
        query,
        date_range: DateRange,
        product_code: str | None,
    ) -> list[dict[str, Any]]:
        result = self._session.execute(query, self._base_params(date_range, product_code))
        return [dict(row) for row in result.mappings().all()]

    @staticmethod
    def _resolve_date_range(*, date_from: date | None, date_to: date | None) -> DateRange:
        today = datetime.now(UTC).date()
        resolved_to = date_to or today
        resolved_from = date_from or (resolved_to - timedelta(days=DEFAULT_DATE_RANGE_DAYS - 1))
        if resolved_from > resolved_to:
            raise ValueError("date_from must be less than or equal to date_to")
        return DateRange(date_from=resolved_from, date_to=resolved_to)

    def _cache_get(self, key: tuple[Any, ...]) -> Any | None:
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.expires_at <= datetime.now(UTC):
                self._cache.pop(key, None)
                return None
            return entry.payload

    def _cache_set(self, key: tuple[Any, ...], value: Any) -> None:
        with self._cache_lock:
            self._cache[key] = CacheEntry(
                expires_at=datetime.now(UTC) + timedelta(seconds=self._cache_ttl_seconds),
                payload=value,
            )
