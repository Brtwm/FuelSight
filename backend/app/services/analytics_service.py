from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.repositories.external_indicators_repository import ExternalIndicatorsRepository
from app.services.event_catalog_service import EventCatalogService
from app.services.analytics_helpers import (
    bucket_start,
    confidence_for_mode,
    merge_modes,
    normalize_granularity,
    normalize_metric,
    normalize_product_code,
    pct_change,
    resolve_data_freshness,
    resolve_wholesale_indicator,
    shift_one_year_back,
    to_float,
)
from app.services.external_context_service import ExternalContextService
from app.services.kpi_service import (
    DEMAND_ZSCORE_HIGH,
    DEMAND_ZSCORE_THRESHOLD,
    PURCHASE_SPIKE_PCT_HIGH,
    PURCHASE_SPIKE_PCT_THRESHOLD,
)

DEFAULT_DATE_RANGE_DAYS = 30
SEVERITY_RANK: dict[str, int] = {"high": 3, "medium": 2, "low": 1}
WEEKDAY_LABELS = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
OVERLAY_LABELS: dict[str, str] = {
    "crude_brent_usd": "Brent, $/баррель",
    "usd_rub": "USD/RUB",
    "wholesale_gasoline_index": "Оптовый индекс бензина",
    "wholesale_diesel_index": "Оптовый индекс дизеля",
    "event_pressure_score": "Событийное давление",
}


@dataclass(frozen=True)
class DateRange:
    date_from: date
    date_to: date


@dataclass(frozen=True)
class SalesAnalyticsResult:
    data: dict[str, Any]
    meta: dict[str, Any]


@dataclass(frozen=True)
class MarginAnalyticsResult:
    data: dict[str, Any]
    meta: dict[str, Any]


@dataclass(frozen=True)
class AnomaliesResult:
    data: list[dict[str, Any]]
    meta: dict[str, Any]


class AnalyticsService:
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

    def get_sales(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
        granularity: str = "day",
    ) -> SalesAnalyticsResult:
        date_range = self._resolve_date_range(date_from=date_from, date_to=date_to)
        normalized_code = self._normalize_product_code(product_code)
        normalized_granularity = self._normalize_granularity(granularity)
        self._assert_product_exists(normalized_code)

        daily_rows = self._query_sales_daily(date_range=date_range, product_code=normalized_code)
        series = self._aggregate_sales_series(
            daily_rows=daily_rows,
            granularity=normalized_granularity,
        )
        seasonality = self._build_seasonality(daily_rows=daily_rows)
        comparisons = self._build_sales_comparisons(
            date_range=date_range,
            product_code=normalized_code,
        )
        anomalies = self._build_sales_anomalies(rows=daily_rows, product_code=normalized_code)
        indicator_overlays, provider_mode = self._build_reference_overlays(
            date_range=date_range,
            product_code=normalized_code,
        )
        event_overlays = self._event_catalog_service.build_event_overlays(
            start_date=date_range.date_from,
            end_date=date_range.date_to,
        )
        overlays = [*indicator_overlays, *event_overlays]
        data_mode, resolved_provider_mode = self._resolve_sales_data_mode(indicator_overlays)
        provider_mode = resolved_provider_mode or provider_mode
        chart_annotations = self._build_sales_annotations(
            anomalies=anomalies,
            comparisons=comparisons,
            granularity=normalized_granularity,
        )
        supporting_refs = self._build_sales_supporting_refs(
            product_code=normalized_code,
            annotations=chart_annotations,
            overlays=overlays,
            comparisons=comparisons,
        )
        external_context = self._external_context_service.build_external_context(
            source_refs=supporting_refs,
        )
        provider_mode = external_context.get("provider_mode") or provider_mode

        data = {
            "product_code": normalized_code,
            "granularity": normalized_granularity,
            "series": series,
            "seasonality": seasonality,
            "comparisons": comparisons,
        }
        meta: dict[str, Any] = {
            "date_from": date_range.date_from.isoformat(),
            "date_to": date_range.date_to.isoformat(),
            "product_code": normalized_code,
            "granularity": normalized_granularity,
            "points": len(series),
            "business_summary": self._build_sales_business_summary(
                comparisons=comparisons,
                data_mode=data_mode,
                rows=daily_rows,
            ),
            "chart_annotations": chart_annotations,
            "reference_overlays": overlays,
            "supporting_refs": supporting_refs,
            "data_mode": data_mode,
            "provider_mode": provider_mode,
            "external_indicators_mode": provider_mode,
            "external_context": external_context,
            "data_freshness": self._resolve_data_freshness(daily_rows),
        }
        if not daily_rows:
            meta["empty_state"] = "Нет данных продаж за выбранный период."
        return SalesAnalyticsResult(data=data, meta=meta)

    def get_margin(
        self,
        *,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
        granularity: str = "day",
    ) -> MarginAnalyticsResult:
        date_range = self._resolve_date_range(date_from=date_from, date_to=date_to)
        normalized_code = self._normalize_product_code(product_code)
        normalized_granularity = self._normalize_granularity(granularity)
        self._assert_product_exists(normalized_code)

        daily_rows = self._query_margin_daily(date_range=date_range, product_code=normalized_code)
        threshold = self._settings.kpi_low_margin_threshold_rub_per_liter
        series = self._aggregate_margin_series(
            daily_rows=daily_rows,
            granularity=normalized_granularity,
        )
        low_margin_days = self._build_low_margin_days(daily_rows=daily_rows, threshold=threshold)
        indicator_overlays, provider_mode = self._build_reference_overlays(
            date_range=date_range,
            product_code=normalized_code,
        )
        event_overlays = self._event_catalog_service.build_event_overlays(
            start_date=date_range.date_from,
            end_date=date_range.date_to,
        )
        overlays = [*indicator_overlays, *event_overlays]
        missing_purchase_days = sum(
            1 for row in daily_rows if bool(row.get("purchase_data_missing"))
        )
        supporting_refs = self._build_margin_supporting_refs(
            product_code=normalized_code,
            low_margin_days=low_margin_days,
            overlays=overlays,
            missing_purchase_days=missing_purchase_days,
        )
        external_context = self._external_context_service.build_external_context(
            source_refs=supporting_refs,
        )
        provider_mode = external_context.get("provider_mode") or provider_mode

        data = {
            "product_code": normalized_code,
            "granularity": normalized_granularity,
            "series": series,
            "threshold_rub_per_liter": round(threshold, 4),
            "below_threshold_days": len(low_margin_days),
            "low_margin_days": low_margin_days,
        }
        meta: dict[str, Any] = {
            "date_from": date_range.date_from.isoformat(),
            "date_to": date_range.date_to.isoformat(),
            "product_code": normalized_code,
            "granularity": normalized_granularity,
            "points": len(series),
            "business_summary": self._build_margin_business_summary(
                threshold=threshold,
                below_threshold_days=len(low_margin_days),
                missing_purchase_days=missing_purchase_days,
            ),
            "chart_annotations": self._build_margin_annotations(
                rows=daily_rows,
                threshold=threshold,
                granularity=normalized_granularity,
            ),
            "reference_overlays": overlays,
            "thresholds": self._build_margin_thresholds(
                threshold=threshold,
                below_threshold_days=len(low_margin_days),
                missing_purchase_days=missing_purchase_days,
            ),
            "supporting_refs": supporting_refs,
            "provider_mode": provider_mode,
            "external_indicators_mode": provider_mode,
            "external_context": external_context,
            "data_freshness": self._resolve_data_freshness(daily_rows),
        }
        if not daily_rows:
            meta["empty_state"] = "Нет данных маржи за выбранный период."
        return MarginAnalyticsResult(data=data, meta=meta)

    def get_anomalies(
        self,
        *,
        metric: str,
        date_from: date | None,
        date_to: date | None,
        product_code: str,
    ) -> AnomaliesResult:
        date_range = self._resolve_date_range(date_from=date_from, date_to=date_to)
        normalized_code = self._normalize_product_code(product_code)
        normalized_metric = self._normalize_metric(metric)
        self._assert_product_exists(normalized_code)

        if normalized_metric == "sales":
            rows = self._query_sales_daily(date_range=date_range, product_code=normalized_code)
            anomalies = self._build_sales_anomalies(rows=rows, product_code=normalized_code)
        elif normalized_metric == "purchase_price":
            rows = self._query_purchase_daily(date_range=date_range, product_code=normalized_code)
            anomalies = self._build_purchase_price_anomalies(
                rows=rows,
                product_code=normalized_code,
            )
        else:
            rows = self._query_margin_daily(date_range=date_range, product_code=normalized_code)
            anomalies = self._build_margin_anomalies(rows=rows, product_code=normalized_code)

        anomalies.sort(
            key=lambda item: (
                item["date"],
                SEVERITY_RANK.get(item["severity"], 0),
            ),
            reverse=True,
        )

        return AnomaliesResult(
            data=anomalies,
            meta={
                "date_from": date_range.date_from.isoformat(),
                "date_to": date_range.date_to.isoformat(),
                "product_code": normalized_code,
                "metric": normalized_metric,
                "count": len(anomalies),
            },
        )

    def _build_reference_overlays(
        self,
        *,
        date_range: DateRange,
        product_code: str,
    ) -> tuple[list[dict[str, Any]], str | None]:
        indicator_codes = [
            "crude_brent_usd",
            "usd_rub",
            self._resolve_wholesale_indicator(product_code),
            "event_pressure_score",
        ]
        try:
            rows_by_code = self._external_repository.get_points_with_mode(
                start_date=date_range.date_from,
                end_date=date_range.date_to,
                indicator_codes=indicator_codes,
            )
        except Exception:
            return [], None

        overlays: list[dict[str, Any]] = []
        modes: set[str] = set()
        for code in indicator_codes:
            rows = rows_by_code.get(code, [])
            if not rows:
                continue
            overlay_mode = self._resolve_overlay_mode(rows)
            if overlay_mode is not None:
                modes.add(overlay_mode)
            overlays.append(
                {
                    "code": code,
                    "label": OVERLAY_LABELS.get(code, code),
                    "unit": rows[0].get("unit"),
                    "provider_mode": overlay_mode,
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

    def _build_sales_business_summary(
        self,
        *,
        comparisons: dict[str, float | None],
        data_mode: str,
        rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not rows:
            return {
                "title": "Нет продаж для анализа",
                "summary": "В выбранном периоде отсутствуют данные продаж.",
                "bullets": ["Проверьте период или продукт в фильтрах."],
            }
        start_volume = self._to_float(rows[0].get("volume_liters")) or 0.0
        end_volume = self._to_float(rows[-1].get("volume_liters")) or 0.0
        delta_volume = end_volume - start_volume
        direction = (
            "рост" if delta_volume > 0 else "снижение" if delta_volume < 0 else "стабильность"
        )
        yoy = comparisons["yoy_pct"]
        yoy_text = "N/A (недостаточно истории)" if yoy is None else f"{yoy:.2f}%"
        mom = comparisons["mom_pct"]
        mom_text = "N/A" if mom is None else f"{mom:.2f}%"
        return {
            "title": "Краткое объяснение динамики",
            "summary": (
                f"За период наблюдается {direction} спроса "
                f"({abs(delta_volume):.0f} л между началом и концом периода)."
            ),
            "bullets": [
                f"MoM: {mom_text}.",
                f"YoY: {yoy_text}.",
                "Внешние сигналы проверены по доступному контексту.",
            ],
        }

    def _build_sales_annotations(
        self,
        *,
        anomalies: list[dict[str, Any]],
        comparisons: dict[str, float | None],
        granularity: str,
    ) -> list[dict[str, Any]]:
        resolved_anomalies = self._bucket_sales_anomalies(
            anomalies=anomalies,
            granularity=granularity,
        )
        annotations: list[dict[str, Any]] = []
        for index, anomaly in enumerate(resolved_anomalies[:4]):
            annotations.append(
                {
                    "id": f"sales-anomaly-{index}",
                    "date": anomaly["date"].isoformat(),
                    "label": "Аномалия спроса",
                    "severity": anomaly["severity"],
                    "message": anomaly["possible_reasons"][0],
                }
            )
        if comparisons["yoy_pct"] is None:
            annotations.append(
                {
                    "id": "sales-yoy-na",
                    "date": None,
                    "label": "YoY = N/A",
                    "severity": "info",
                    "message": "Год-к-году не рассчитан: недостаточно сопоставимой истории.",
                }
            )
        return annotations

    def _bucket_sales_anomalies(
        self,
        *,
        anomalies: list[dict[str, Any]],
        granularity: str,
    ) -> list[dict[str, Any]]:
        if granularity == "day":
            return anomalies

        by_bucket: dict[date, dict[str, Any]] = {}
        for anomaly in anomalies:
            source_date = anomaly.get("date")
            if not isinstance(source_date, date):
                continue
            bucket_date = self._bucket_start(source_date, granularity)
            current = by_bucket.get(bucket_date)
            if current is None:
                by_bucket[bucket_date] = {**anomaly, "date": bucket_date}
                continue
            current_rank = SEVERITY_RANK.get(str(current.get("severity")), 0)
            next_rank = SEVERITY_RANK.get(str(anomaly.get("severity")), 0)
            if next_rank >= current_rank:
                by_bucket[bucket_date] = {**anomaly, "date": bucket_date}

        return [by_bucket[key] for key in sorted(by_bucket)]

    @staticmethod
    def _build_margin_business_summary(
        *,
        threshold: float,
        below_threshold_days: int,
        missing_purchase_days: int,
    ) -> dict[str, Any]:
        risk_level = "повышенный" if below_threshold_days > 0 else "контролируемый"
        return {
            "title": "Маржинальный риск",
            "summary": (
                f"Риск по марже оценивается как {risk_level}. "
                f"Порог: {threshold:.2f} руб/л, дней ниже порога: {below_threshold_days}."
            ),
            "bullets": [
                f"Дней без полного покрытия закупки: {missing_purchase_days}.",
                "Выделенные дни на графике синхронизированы с таблицей и пояснениями.",
            ],
        }

    def _build_margin_annotations(
        self,
        *,
        rows: list[dict[str, Any]],
        threshold: float,
        granularity: str,
    ) -> list[dict[str, Any]]:
        annotations: list[dict[str, Any]] = []
        for row in rows:
            margin_value = self._to_float(row.get("gross_margin_rub_per_liter"))
            if margin_value is None or margin_value >= threshold:
                continue
            severity = "high" if margin_value <= (threshold * 0.5) else "medium"
            annotations.append(
                {
                    "id": f"margin-below-threshold-{row['date'].isoformat()}",
                    "date": row["date"].isoformat(),
                    "label": "Ниже порога",
                    "severity": severity,
                    "message": (
                        f"Маржа {margin_value:.2f} руб/л ниже порога {threshold:.2f} руб/л."
                    ),
                }
            )
            if len(annotations) >= 5:
                break
        missing_rows = [row for row in rows if bool(row.get("purchase_data_missing"))]
        if missing_rows:
            annotations.append(
                {
                    "id": "margin-missing-purchase",
                    "date": missing_rows[0]["date"].isoformat(),
                    "label": "Неполные закупки",
                    "severity": "warning",
                    "message": (
                        "Часть дат имеет неполные данные закупки, интерпретируйте маржу аккуратно."
                    ),
                }
            )
        if granularity == "day":
            return annotations
        return self._bucket_margin_annotations(
            annotations=annotations,
            granularity=granularity,
        )

    def _bucket_margin_annotations(
        self,
        *,
        annotations: list[dict[str, Any]],
        granularity: str,
    ) -> list[dict[str, Any]]:
        by_bucket: dict[date, dict[str, Any]] = {}
        for annotation in annotations:
            source_date = annotation.get("date")
            if not isinstance(source_date, str):
                continue
            try:
                parsed_date = date.fromisoformat(source_date)
            except ValueError:
                continue
            bucket_date = self._bucket_start(parsed_date, granularity)
            existing = by_bucket.get(bucket_date)
            if existing is None:
                by_bucket[bucket_date] = {**annotation, "date": bucket_date.isoformat()}
                continue
            existing_rank = self._annotation_severity_rank(existing.get("severity"))
            next_rank = self._annotation_severity_rank(annotation.get("severity"))
            if next_rank >= existing_rank:
                by_bucket[bucket_date] = {**annotation, "date": bucket_date.isoformat()}
        return [by_bucket[key] for key in sorted(by_bucket)]

    @staticmethod
    def _annotation_severity_rank(value: Any) -> int:
        normalized = str(value).strip().lower() if value is not None else ""
        if normalized == "high":
            return 4
        if normalized == "medium":
            return 3
        if normalized == "warning":
            return 2
        if normalized == "low":
            return 1
        return 0

    def _build_margin_supporting_refs(
        self,
        *,
        product_code: str,
        low_margin_days: list[dict[str, Any]],
        overlays: list[dict[str, Any]],
        missing_purchase_days: int,
    ) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        for day in low_margin_days[:3]:
            refs.append(
                {
                    "type": "margin_day",
                    "ref_id": f"margin:{product_code}:{day['date'].isoformat()}",
                    "title": f"День ниже порога: {day['date'].isoformat()}",
                    "source_type": "internal_margin",
                    "confidence": 0.9,
                }
            )
        if missing_purchase_days > 0:
            refs.append(
                {
                    "type": "coverage",
                    "ref_id": f"coverage:{product_code}",
                    "title": f"Дней с неполным покрытием закупки: {missing_purchase_days}",
                    "source_type": "internal_margin",
                    "confidence": 0.85,
                }
            )
        for overlay in overlays[:3]:
            points = overlay.get("points", [])
            if not points:
                continue
            latest = points[-1]
            confidence = self._confidence_for_mode(overlay.get("provider_mode"))
            refs.append(
                {
                    "type": "indicator",
                    "ref_id": f"indicator:{overlay['code']}:{latest['date']}",
                    "title": f"{overlay['label']}: {latest['value']:.2f} ({latest['date']})",
                    "provider_mode": overlay.get("provider_mode"),
                    "source_type": "external_indicator",
                    "confidence": confidence,
                }
            )
        return refs

    @staticmethod
    def _build_margin_thresholds(
        *,
        threshold: float,
        below_threshold_days: int,
        missing_purchase_days: int,
    ) -> list[dict[str, Any]]:
        severity = "high" if below_threshold_days > 0 else "low"
        return [
            {
                "id": "margin-threshold-rub-per-liter",
                "label": "Порог маржи",
                "value": round(threshold, 4),
                "unit": "RUB/L",
                "severity": severity,
                "description": (
                    f"Дней ниже порога: {below_threshold_days}; "
                    f"дней с неполным покрытием закупки: {missing_purchase_days}."
                ),
            }
        ]

    def _build_sales_supporting_refs(
        self,
        *,
        product_code: str,
        annotations: list[dict[str, Any]],
        overlays: list[dict[str, Any]],
        comparisons: dict[str, float | None],
    ) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        for item in annotations[:3]:
            ref_id = str(item.get("id", "")).strip()
            if not ref_id:
                continue
            refs.append(
                {
                    "type": "annotation",
                    "ref_id": ref_id,
                    "title": item.get("message") or item.get("label") or ref_id,
                    "source_type": "internal_sales",
                    "confidence": 0.9,
                }
            )
        for overlay in overlays[:3]:
            points = overlay.get("points", [])
            if not points:
                continue
            latest = points[-1]
            refs.append(
                {
                    "type": "indicator",
                    "ref_id": f"indicator:{overlay['code']}:{latest['date']}",
                    "title": f"{overlay['label']}: {latest['value']:.2f} ({latest['date']})",
                    "provider_mode": overlay.get("provider_mode"),
                    "source_type": "external_indicator",
                    "confidence": self._confidence_for_mode(overlay.get("provider_mode")),
                }
            )
        for period_name, value in (
            ("MoM", comparisons.get("mom_pct")),
            ("YoY", comparisons.get("yoy_pct")),
        ):
            if value is None:
                continue
            refs.append(
                {
                    "type": "comparison",
                    "ref_id": f"sales:{product_code}:{period_name.lower()}",
                    "title": f"{period_name}: {value:.2f}%",
                    "source_type": "internal_sales",
                    "confidence": 0.95,
                }
            )
        return refs

    @staticmethod
    def _confidence_for_mode(mode: str | None) -> float | None:
        return confidence_for_mode(mode)

    def _resolve_sales_data_mode(
        self,
        overlays: list[dict[str, Any]],
    ) -> tuple[str, str | None]:
        if not overlays:
            return "degraded", None
        modes = {
            str(item.get("provider_mode")).strip().lower()
            for item in overlays
            if item.get("provider_mode")
        }
        if not modes:
            return "degraded", None
        if modes == {"live"}:
            return "live", "live"
        if "manual_snapshot" in modes:
            return "cached", "manual_snapshot"
        if "cached" in modes:
            return "cached", "cached"
        return "degraded", None

    @staticmethod
    def _resolve_overlay_mode(rows: list[dict[str, Any]]) -> str | None:
        modes = {
            str(row.get("provider_mode")).strip().lower()
            for row in rows
            if row.get("provider_mode")
        }
        return AnalyticsService._merge_modes(modes)

    @staticmethod
    def _merge_modes(modes: set[str]) -> str | None:
        return merge_modes(modes)

    @staticmethod
    def _resolve_data_freshness(rows: list[dict[str, Any]], date_key: str = "date") -> str:
        return resolve_data_freshness(rows, date_key=date_key)

    @staticmethod
    def _resolve_wholesale_indicator(product_code: str) -> str:
        return resolve_wholesale_indicator(product_code)

    def _query_sales_daily(
        self,
        *,
        date_range: DateRange,
        product_code: str,
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
            WHERE p.code = :product_code
              AND sd.sale_date BETWEEN :date_from AND :date_to
            GROUP BY sd.sale_date
            ORDER BY sd.sale_date
            """
        )
        return self._execute_mapping_query(
            query=query,
            date_range=date_range,
            product_code=product_code,
        )

    def _query_sales_total(
        self,
        *,
        date_range: DateRange,
        product_code: str,
    ) -> float | None:
        query = text(
            """
            SELECT SUM(sd.volume_liters)::numeric AS volume_total
            FROM sales_daily sd
            JOIN products p ON p.id = sd.product_id
            WHERE p.code = :product_code
              AND sd.sale_date BETWEEN :date_from AND :date_to
            """
        )
        rows = self._execute_mapping_query(
            query=query,
            date_range=date_range,
            product_code=product_code,
        )
        if not rows:
            return None
        volume_total = self._to_float(rows[0].get("volume_total"))
        return volume_total

    def _query_purchase_daily(
        self,
        *,
        date_range: DateRange,
        product_code: str,
    ) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT
              pd.purchase_date::date AS date,
              CASE
                WHEN SUM(pd.volume_liters) > 0
                THEN (
                  SUM(pd.volume_liters * pd.purchase_price_rub) / SUM(pd.volume_liters)
                )::numeric
                ELSE NULL
              END AS avg_purchase_price_rub
            FROM purchases_daily pd
            JOIN products p ON p.id = pd.product_id
            WHERE p.code = :product_code
              AND pd.purchase_date BETWEEN :date_from AND :date_to
            GROUP BY pd.purchase_date
            ORDER BY pd.purchase_date
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
        product_code: str,
    ) -> list[dict[str, Any]]:
        query = text(
            """
            SELECT
              date::date AS date,
              volume_liters,
              revenue_rub,
              purchase_volume_liters,
              avg_retail_price_rub,
              avg_purchase_price_rub,
              purchase_data_missing,
              gross_margin_rub,
              gross_margin_rub_per_liter,
              gross_margin_pct
            FROM vw_margin_daily
            WHERE product_code = :product_code
              AND date BETWEEN :date_from AND :date_to
            ORDER BY date
            """
        )
        return self._execute_mapping_query(
            query=query,
            date_range=date_range,
            product_code=product_code,
        )

    def _aggregate_sales_series(
        self,
        *,
        daily_rows: list[dict[str, Any]],
        granularity: str,
    ) -> list[dict[str, Any]]:
        grouped: dict[date, dict[str, float]] = defaultdict(
            lambda: {"volume_liters": 0.0, "revenue_rub": 0.0}
        )
        for row in daily_rows:
            row_date: date = row["date"]
            bucket = self._bucket_start(row_date, granularity)
            grouped[bucket]["volume_liters"] += self._to_float(row.get("volume_liters")) or 0.0
            grouped[bucket]["revenue_rub"] += self._to_float(row.get("revenue_rub")) or 0.0

        results: list[dict[str, Any]] = []
        for period_start in sorted(grouped):
            volume = grouped[period_start]["volume_liters"]
            revenue = grouped[period_start]["revenue_rub"]
            avg_price = (revenue / volume) if volume > 0 else None
            results.append(
                {
                    "period_start": period_start,
                    "volume_liters": round(volume, 3),
                    "avg_retail_price_rub": round(avg_price, 4) if avg_price is not None else None,
                }
            )
        return results

    def _aggregate_margin_series(
        self,
        *,
        daily_rows: list[dict[str, Any]],
        granularity: str,
    ) -> list[dict[str, Any]]:
        buckets: dict[date, list[dict[str, Any]]] = defaultdict(list)
        for row in daily_rows:
            bucket = self._bucket_start(row["date"], granularity)
            buckets[bucket].append(row)

        results: list[dict[str, Any]] = []
        for period_start in sorted(buckets):
            rows = buckets[period_start]
            total_volume = sum((self._to_float(item.get("volume_liters")) or 0.0) for item in rows)
            total_revenue = sum((self._to_float(item.get("revenue_rub")) or 0.0) for item in rows)

            purchase_weighted_sum = 0.0
            purchase_weight = 0.0
            covered_margin_rub = 0.0
            covered_volume = 0.0
            covered_revenue = 0.0
            has_covered_margin = False
            has_missing_purchase = False

            for row in rows:
                purchase_volume = self._to_float(row.get("purchase_volume_liters")) or 0.0
                avg_purchase = self._to_float(row.get("avg_purchase_price_rub"))
                if avg_purchase is not None and purchase_volume > 0:
                    purchase_weighted_sum += avg_purchase * purchase_volume
                    purchase_weight += purchase_volume

                missing_purchase = bool(row.get("purchase_data_missing"))
                has_missing_purchase = has_missing_purchase or missing_purchase
                if not missing_purchase:
                    margin_rub = self._to_float(row.get("gross_margin_rub"))
                    row_volume = self._to_float(row.get("volume_liters")) or 0.0
                    row_revenue = self._to_float(row.get("revenue_rub")) or 0.0
                    if margin_rub is not None:
                        covered_margin_rub += margin_rub
                        covered_volume += row_volume
                        covered_revenue += row_revenue
                        has_covered_margin = True

            avg_retail = (total_revenue / total_volume) if total_volume > 0 else None
            avg_purchase = (
                (purchase_weighted_sum / purchase_weight) if purchase_weight > 0 else None
            )
            gross_margin_rub = covered_margin_rub if has_covered_margin else None
            gross_margin_rub_per_liter = (
                covered_margin_rub / covered_volume if covered_volume > 0 else None
            )
            gross_margin_pct = (
                (covered_margin_rub / covered_revenue * 100.0) if covered_revenue > 0 else None
            )

            results.append(
                {
                    "period_start": period_start,
                    "avg_purchase_price_rub": (
                        round(avg_purchase, 4) if avg_purchase is not None else None
                    ),
                    "avg_retail_price_rub": (
                        round(avg_retail, 4) if avg_retail is not None else None
                    ),
                    "gross_margin_rub": (
                        round(gross_margin_rub, 4) if gross_margin_rub is not None else None
                    ),
                    "gross_margin_rub_per_liter": (
                        round(gross_margin_rub_per_liter, 4)
                        if gross_margin_rub_per_liter is not None
                        else None
                    ),
                    "gross_margin_pct": round(gross_margin_pct, 4)
                    if gross_margin_pct is not None
                    else None,
                    "purchase_data_missing": has_missing_purchase,
                }
            )
        return results

    def _build_seasonality(
        self,
        *,
        daily_rows: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        weekday_acc: dict[int, list[float]] = defaultdict(list)
        month_acc: dict[int, list[float]] = defaultdict(list)
        for row in daily_rows:
            volume = self._to_float(row.get("volume_liters"))
            if volume is None:
                continue
            row_date: date = row["date"]
            weekday_acc[row_date.isoweekday()].append(volume)
            month_acc[row_date.month].append(volume)

        by_weekday = [
            {
                "weekday": WEEKDAY_LABELS[idx],
                "avg_volume_liters": round(sum(values) / len(values), 3),
            }
            for idx, values in sorted(weekday_acc.items())
            if values
        ]
        by_month = [
            {
                "month": month,
                "avg_volume_liters": round(sum(values) / len(values), 3),
            }
            for month, values in sorted(month_acc.items())
            if values
        ]
        return {"by_weekday": by_weekday, "by_month": by_month}

    def _build_sales_comparisons(
        self,
        *,
        date_range: DateRange,
        product_code: str,
    ) -> dict[str, float | None]:
        current_total = self._query_sales_total(date_range=date_range, product_code=product_code)
        if current_total is None:
            return {"mom_pct": None, "yoy_pct": None}

        range_days = (date_range.date_to - date_range.date_from).days + 1
        prev_to = date_range.date_from - timedelta(days=1)
        prev_from = prev_to - timedelta(days=range_days - 1)
        previous_range = DateRange(date_from=prev_from, date_to=prev_to)

        yoy_from = self._shift_one_year_back(date_range.date_from)
        yoy_to = self._shift_one_year_back(date_range.date_to)
        yoy_range = DateRange(date_from=yoy_from, date_to=yoy_to)

        prev_total = self._query_sales_total(date_range=previous_range, product_code=product_code)
        yoy_total = self._query_sales_total(date_range=yoy_range, product_code=product_code)

        return {
            "mom_pct": self._pct_change(current=current_total, baseline=prev_total),
            "yoy_pct": self._pct_change(current=current_total, baseline=yoy_total),
        }

    def _build_low_margin_days(
        self,
        *,
        daily_rows: list[dict[str, Any]],
        threshold: float,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for row in daily_rows:
            margin_value = self._to_float(row.get("gross_margin_rub_per_liter"))
            if margin_value is None or margin_value >= threshold:
                continue
            results.append(
                {
                    "date": row["date"],
                    "gross_margin_rub_per_liter": round(margin_value, 4),
                    "purchase_data_missing": bool(row.get("purchase_data_missing")),
                }
            )
        return results

    def _build_sales_anomalies(
        self,
        *,
        rows: list[dict[str, Any]],
        product_code: str,
    ) -> list[dict[str, Any]]:
        valid_rows = []
        for row in rows:
            volume = self._to_float(row.get("volume_liters"))
            if volume is None:
                continue
            valid_rows.append((row, volume))

        if len(valid_rows) < 7:
            return []

        values = [volume for _, volume in valid_rows]
        mean_value = sum(values) / len(values)
        variance = sum((value - mean_value) ** 2 for value in values) / len(values)
        stddev = variance**0.5
        if stddev <= 0:
            return []

        expected_lo = mean_value - (DEMAND_ZSCORE_THRESHOLD * stddev)
        expected_hi = mean_value + (DEMAND_ZSCORE_THRESHOLD * stddev)
        anomalies: list[dict[str, Any]] = []
        for row, actual in valid_rows:
            zscore = (actual - mean_value) / stddev
            if abs(zscore) < DEMAND_ZSCORE_THRESHOLD:
                continue
            severity = "high" if abs(zscore) >= DEMAND_ZSCORE_HIGH else "medium"
            possible_reasons = (
                [
                    "Спрос заметно выше исторического уровня.",
                    "Возможны промо-активность или краткосрочный всплеск трафика.",
                ]
                if zscore > 0
                else [
                    "Спрос заметно ниже исторического уровня.",
                    "Возможны сезонный спад или чувствительность к изменению цены.",
                ]
            )
            anomalies.append(
                {
                    "date": row["date"],
                    "product_code": product_code,
                    "metric": "sales",
                    "severity": severity,
                    "actual_value": round(actual, 3),
                    "expected_range": (round(expected_lo, 3), round(expected_hi, 3)),
                    "possible_reasons": possible_reasons,
                    "target_path": "/analytics/sales",
                }
            )
        return anomalies

    def _build_purchase_price_anomalies(
        self,
        *,
        rows: list[dict[str, Any]],
        product_code: str,
    ) -> list[dict[str, Any]]:
        rows_sorted = sorted(rows, key=lambda item: item["date"])
        anomalies: list[dict[str, Any]] = []
        previous_price: float | None = None
        for row in rows_sorted:
            current_price = self._to_float(row.get("avg_purchase_price_rub"))
            if current_price is None:
                continue
            if previous_price is None or previous_price <= 0:
                previous_price = current_price
                continue
            delta_pct = ((current_price - previous_price) / previous_price) * 100.0
            if delta_pct >= PURCHASE_SPIKE_PCT_THRESHOLD:
                severity = "high" if delta_pct >= PURCHASE_SPIKE_PCT_HIGH else "medium"
                anomalies.append(
                    {
                        "date": row["date"],
                        "product_code": product_code,
                        "metric": "purchase_price",
                        "severity": severity,
                        "actual_value": round(current_price, 4),
                        "expected_range": (
                            round(previous_price * 0.92, 4),
                            round(previous_price * 1.08, 4),
                        ),
                        "possible_reasons": [
                            "Закупочная цена выросла быстрее обычного day-over-day.",
                            "Проверьте источник импорта закупок на выбросы по цене.",
                        ],
                        "target_path": "/analytics/margin",
                    }
                )
            previous_price = current_price
        return anomalies

    def _build_margin_anomalies(
        self,
        *,
        rows: list[dict[str, Any]],
        product_code: str,
    ) -> list[dict[str, Any]]:
        threshold = self._settings.kpi_low_margin_threshold_rub_per_liter
        anomalies: list[dict[str, Any]] = []
        for row in rows:
            margin_value = self._to_float(row.get("gross_margin_rub_per_liter"))
            if margin_value is None or margin_value >= threshold:
                continue

            severity = "high" if margin_value <= (threshold * 0.5) else "medium"
            reasons: list[str] = []
            purchase_missing = bool(row.get("purchase_data_missing"))
            if purchase_missing:
                reasons.append("По части дат нет закупок, расчет маржи неполный.")
            avg_purchase = self._to_float(row.get("avg_purchase_price_rub"))
            avg_retail = self._to_float(row.get("avg_retail_price_rub"))
            if avg_purchase is not None and avg_retail is not None and avg_purchase > avg_retail:
                reasons.append("Закупочная цена превысила розничную цену.")
            if not reasons:
                reasons = [
                    "Маржа ниже бизнес-порога, проверьте корректировку розничной цены.",
                    "Рост закупочной цены мог опередить изменение цены продажи.",
                ]

            anomalies.append(
                {
                    "date": row["date"],
                    "product_code": product_code,
                    "metric": "margin",
                    "severity": severity,
                    "actual_value": round(margin_value, 4),
                    "expected_range": (round(threshold, 4), round(threshold * 1.5, 4)),
                    "possible_reasons": reasons,
                    "target_path": "/analytics/margin",
                }
            )
        return anomalies

    @staticmethod
    def _bucket_start(source: date, granularity: str) -> date:
        return bucket_start(source, granularity)

    @staticmethod
    def _shift_one_year_back(value: date) -> date:
        return shift_one_year_back(value)

    @staticmethod
    def _pct_change(*, current: float | None, baseline: float | None) -> float | None:
        return pct_change(current=current, baseline=baseline)

    @staticmethod
    def _normalize_product_code(product_code: str) -> str:
        return normalize_product_code(product_code)

    @staticmethod
    def _normalize_granularity(granularity: str) -> str:
        return normalize_granularity(granularity)

    @staticmethod
    def _normalize_metric(metric: str) -> str:
        return normalize_metric(metric)

    def _assert_product_exists(self, product_code: str) -> None:
        query = text(
            """
            SELECT 1
            FROM products
            WHERE code = :product_code
            LIMIT 1
            """
        )
        result = self._session.execute(query, {"product_code": product_code}).scalar_one_or_none()
        if result is None:
            raise ValueError(f"Unknown product_code: {product_code}")

    @staticmethod
    def _to_float(value: Any) -> float | None:
        return to_float(value)

    @staticmethod
    def _base_params(date_range: DateRange, product_code: str) -> dict[str, Any]:
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
        product_code: str,
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
