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
from app.repositories.external_indicators_repository import ExternalIndicatorsRepository
from app.services.event_catalog_service import EventCatalogService
from app.services.external_context_service import ExternalContextService

AlertSeverity = Literal["high", "medium", "low"]
AlertType = Literal["low_margin", "purchase_spike", "demand_anomaly"]

SEVERITY_RANK: dict[AlertSeverity, int] = {"high": 3, "medium": 2, "low": 1}
DEFAULT_DATE_RANGE_DAYS = 30
PURCHASE_SPIKE_PCT_THRESHOLD = 8.0
PURCHASE_SPIKE_PCT_HIGH = 15.0
DEMAND_ZSCORE_THRESHOLD = 2.0
DEMAND_ZSCORE_HIGH = 3.0
FRESH_MAX_AGE_DAYS = 2
WARNING_MAX_AGE_DAYS = 7

KPI_OVERLAY_LABELS: dict[str, str] = {
    "crude_brent_usd": "Brent, $/баррель",
    "usd_rub": "USD/RUB",
    "event_pressure_score": "Событийное давление",
}


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

    def __init__(
        self,
        session: Session,
        settings: Settings | None = None,
        external_repository: ExternalIndicatorsRepository | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._external_repository = external_repository or ExternalIndicatorsRepository(session)
        self._event_catalog_service = EventCatalogService(session)
        self._external_context_service = ExternalContextService(self._settings)

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
                    "empty_state": "Нет данных за выбранный период.",
                    "data_freshness": "degraded",
                    "business_summary": {
                        "title": "Нет фактических данных",
                        "summary": "За выбранный период не найдено продаж для расчета KPI.",
                        "bullets": [
                            "Проверьте фильтры по датам и продукту.",
                            "После обновления данных обзор KPI станет доступен автоматически.",
                        ],
                    },
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
            date_range=date_range,
            product_code=normalized_code,
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
        margin_missing_days = max(len(sales_days) - len(margin_days), 0)
        result = SummaryResult(
            data=summary,
            meta={
                "date_from": date_range.date_from.isoformat(),
                "date_to": date_range.date_to.isoformat(),
                "product_code": normalized_code,
                "margin_coverage_days": len(margin_days),
                "margin_missing_days": margin_missing_days,
                "data_freshness": self._resolve_data_freshness(sales_rows),
                "external_context": self._external_context_service.build_external_context(),
                "business_summary": self._build_summary_business_summary(
                    summary=summary,
                    margin_coverage_days=len(margin_days),
                    margin_missing_days=margin_missing_days,
                ),
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
            date_range=date_range,
            product_code=normalized_code,
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
        indicator_overlays, provider_mode = self._build_reference_overlays(date_range=date_range)
        event_overlays = self._event_catalog_service.build_event_overlays(
            start_date=date_range.date_from,
            end_date=date_range.date_to,
        )
        overlays = [*indicator_overlays, *event_overlays]
        annotations = self._build_snapshot_annotations(snapshot)
        supporting_refs = self._build_snapshot_supporting_refs(
            annotations=annotations,
            overlays=overlays,
        )
        external_context = self._external_context_service.build_external_context(
            source_refs=supporting_refs,
        )
        resolved_provider_mode = external_context.get("provider_mode") or provider_mode
        result = SnapshotResult(
            data=snapshot,
            meta={
                "date_from": date_range.date_from.isoformat(),
                "date_to": date_range.date_to.isoformat(),
                "product_code": normalized_code,
                "points": len(snapshot),
                "business_summary": self._build_snapshot_business_summary(
                    snapshot=snapshot,
                    provider_mode=resolved_provider_mode,
                ),
                "chart_annotations": annotations,
                "reference_overlays": overlays,
                "supporting_refs": supporting_refs,
                "provider_mode": resolved_provider_mode,
                "external_indicators_mode": resolved_provider_mode,
                "external_context": external_context,
                "data_freshness": self._resolve_data_freshness(rows),
            },
        )
        if not rows:
            result.meta["empty_state"] = "Нет динамики спроса за выбранный период."
        self._cache_set(cache_key, result)
        return result

    def _build_summary_business_summary(
        self,
        *,
        summary: dict[str, Any],
        margin_coverage_days: int,
        margin_missing_days: int,
    ) -> dict[str, Any]:
        margin_pct = summary["gross_margin_pct"]
        margin_text = "n/a" if margin_pct is None else f"{margin_pct:.2f}%"
        return {
            "title": "Итог за выбранный период",
            "summary": (
                f"Продажи составили {summary['sales_volume_liters']:.0f} л, "
                f"маржа {summary['gross_margin_rub']:.0f} руб ({margin_text})."
            ),
            "bullets": [
                f"Дней с маржой ниже порога: {summary['low_margin_days']}.",
                f"Всего сигналов риска/аномалий: {summary['anomaly_count']}.",
                (
                    "Покрытие маржи: "
                    f"{margin_coverage_days} дн.; без закупок: {margin_missing_days} дн."
                ),
            ],
        }

    def _build_snapshot_business_summary(
        self,
        *,
        snapshot: list[dict[str, Any]],
        provider_mode: str | None,
    ) -> dict[str, Any]:
        if not snapshot:
            return {
                "title": "Срез спроса недоступен",
                "summary": "Для выбранного периода нет точек продаж.",
                "bullets": ["Измените период или обновите данные."],
            }
        first = snapshot[0]
        last = snapshot[-1]
        delta = float(last["volume_liters"]) - float(first["volume_liters"])
        delta_text = "рост" if delta > 0 else "снижение" if delta < 0 else "без изменений"
        provider_text = provider_mode or "n/a"
        return {
            "title": "Динамика спроса и контекст",
            "summary": (
                f"За период наблюдается {delta_text} спроса на {abs(delta):.0f} л. "
                f"Контекст индикаторов: {provider_text}."
            ),
            "bullets": [
                f"Последний день в выборке: {last['date'].isoformat()}.",
                "Аннотации выделяют пики и просадки спроса.",
            ],
        }

    def _build_snapshot_annotations(self, snapshot: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not snapshot:
            return []
        max_row = max(snapshot, key=lambda item: float(item["volume_liters"]))
        min_row = min(snapshot, key=lambda item: float(item["volume_liters"]))
        annotations: list[dict[str, Any]] = [
            {
                "id": "kpi-snapshot-max-demand",
                "date": max_row["date"].isoformat(),
                "label": "Пик спроса",
                "severity": "medium",
                "message": (
                    f"Максимальный объем: {float(max_row['volume_liters']):.0f} л "
                    f"({max_row['date'].isoformat()})."
                ),
            }
        ]
        if max_row["date"] != min_row["date"]:
            annotations.append(
                {
                    "id": "kpi-snapshot-min-demand",
                    "date": min_row["date"].isoformat(),
                    "label": "Просадка спроса",
                    "severity": "warning",
                    "message": (
                        f"Минимальный объем: {float(min_row['volume_liters']):.0f} л "
                        f"({min_row['date'].isoformat()})."
                    ),
                }
            )
        return annotations

    @staticmethod
    def _build_snapshot_supporting_refs(
        *,
        annotations: list[dict[str, Any]],
        overlays: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        for item in annotations[:3]:
            item_id = str(item.get("id", "")).strip()
            if not item_id:
                continue
            refs.append(
                {
                    "type": "annotation",
                    "ref_id": item_id,
                    "title": item.get("message") or item.get("label") or item_id,
                    "source_type": "internal_kpi",
                    "confidence": 0.9,
                }
            )
        for overlay in overlays[:3]:
            points = overlay.get("points") or []
            if not points:
                continue
            latest = points[-1]
            latest_date = latest.get("date")
            latest_value = latest.get("value")
            refs.append(
                {
                    "type": "overlay",
                    "ref_id": f"overlay:{overlay.get('code')}:{latest_date}",
                    "title": f"{overlay.get('label')}: {latest_value} ({latest_date})",
                    "provider_mode": overlay.get("provider_mode"),
                    "source_type": "external_indicator",
                    "confidence": 0.8,
                }
            )
        return refs

    def _build_reference_overlays(
        self, *, date_range: DateRange
    ) -> tuple[list[dict[str, Any]], str | None]:
        try:
            rows_by_code = self._external_repository.get_points_with_mode(
                start_date=date_range.date_from,
                end_date=date_range.date_to,
                indicator_codes=list(KPI_OVERLAY_LABELS.keys()),
            )
        except Exception:
            return [], None

        overlays: list[dict[str, Any]] = []
        modes: set[str] = set()
        for code, label in KPI_OVERLAY_LABELS.items():
            rows = rows_by_code.get(code, [])
            if not rows:
                continue
            provider_mode = self._resolve_overlay_mode(rows)
            if provider_mode:
                modes.add(provider_mode)
            overlays.append(
                {
                    "code": code,
                    "label": label,
                    "unit": rows[0].get("unit"),
                    "provider_mode": provider_mode,
                    "points": [
                        {
                            "date": row["indicator_date"].isoformat(),
                            "value": float(row["value_numeric"]),
                        }
                        for row in rows
                    ],
                }
            )
        return overlays, self._merge_modes(modes)

    @staticmethod
    def _resolve_overlay_mode(rows: list[dict[str, Any]]) -> str | None:
        modes = {
            str(row.get("provider_mode")).strip().lower()
            for row in rows
            if row.get("provider_mode")
        }
        return KpiService._merge_modes(modes)

    @staticmethod
    def _merge_modes(modes: set[str]) -> str | None:
        if not modes:
            return None
        if "manual_snapshot" in modes:
            return "manual_snapshot"
        if "cached" in modes:
            return "cached"
        if modes == {"live"}:
            return "live"
        return None

    @staticmethod
    def _resolve_data_freshness(rows: list[dict[str, Any]], date_key: str = "date") -> str:
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
                        "message": f"Спрос {direction} ожиданий: z-score {zscore:.2f}",
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
