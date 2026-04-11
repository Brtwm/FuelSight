from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import Request

from app.core.responses import request_meta
from app.schemas.analytics import MarginAnalyticsMeta, SalesAnalyticsMeta
from app.schemas.common import (
    BusinessSummaryPayload,
    ChartAnnotationPayload,
    DataProviderMode,
    FreshnessStatus,
    ProviderMode,
    ReferenceOverlayPayload,
    SupportingRefPayload,
)
from app.schemas.kpi import KpiSnapshotMeta, KpiSummaryMeta

_BASE_META_DEFAULTS: dict[str, Any] = {
    "business_summary": None,
    "chart_annotations": [],
    "reference_overlays": [],
    "supporting_refs": [],
    "data_freshness": None,
    "model_freshness": None,
    "news_freshness": None,
    "external_indicators_mode": None,
    "provider_mode": None,
    "llm_mode": None,
}

_KPI_SUMMARY_DEFAULTS: dict[str, Any] = {
    **_BASE_META_DEFAULTS,
    "margin_coverage_days": None,
    "margin_missing_days": None,
}

_ANALYTICS_SALES_DEFAULTS: dict[str, Any] = {
    **_BASE_META_DEFAULTS,
    "data_mode": None,
}

_ANALYTICS_MARGIN_DEFAULTS: dict[str, Any] = {
    **_BASE_META_DEFAULTS,
    "threshold_info": None,
}


def _normalize_business_summary(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        if isinstance(value, BusinessSummaryPayload):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            return BusinessSummaryPayload(**value).model_dump(mode="json")
    except Exception:
        return None
    return None


def _normalize_annotations(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    rows = value if isinstance(value, list) else []
    normalized: list[dict[str, Any]] = []
    for item in rows:
        try:
            if isinstance(item, ChartAnnotationPayload):
                normalized.append(item.model_dump(mode="json"))
            elif isinstance(item, dict):
                normalized.append(ChartAnnotationPayload(**item).model_dump(mode="json"))
        except Exception:
            continue
    return normalized


def _normalize_overlays(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    rows = value if isinstance(value, list) else []
    normalized: list[dict[str, Any]] = []
    for item in rows:
        try:
            if isinstance(item, ReferenceOverlayPayload):
                normalized.append(item.model_dump(mode="json"))
            elif isinstance(item, dict):
                normalized.append(ReferenceOverlayPayload(**item).model_dump(mode="json"))
        except Exception:
            continue
    return normalized


def _normalize_supporting_refs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    rows = value if isinstance(value, list) else []
    normalized: list[dict[str, Any]] = []
    for item in rows:
        try:
            if isinstance(item, SupportingRefPayload):
                normalized.append(item.model_dump(mode="json"))
            elif isinstance(item, dict):
                normalized.append(SupportingRefPayload(**item).model_dump(mode="json"))
        except Exception:
            continue
    return normalized


def _normalize_freshness(value: Any) -> FreshnessStatus | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in {"fresh", "warning", "degraded"}:
        return normalized  # type: ignore[return-value]
    return None


def _normalize_provider_mode(value: Any) -> ProviderMode | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    allowed = {
        "live",
        "cached",
        "manual_snapshot",
        "cloud_llm",
        "local_llm",
        "retrieval_only",
    }
    if normalized in allowed:
        return normalized  # type: ignore[return-value]
    return None


def _normalize_data_provider_mode(value: Any) -> DataProviderMode | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    allowed = {"live", "cached", "manual_snapshot"}
    if normalized in allowed:
        return normalized  # type: ignore[return-value]
    return None


def _build_meta(
    *,
    request: Request,
    defaults: dict[str, Any],
    extra_meta: dict[str, Any] | None,
) -> dict[str, Any]:
    meta = deepcopy(defaults)
    if extra_meta:
        meta.update(extra_meta)

    meta["business_summary"] = _normalize_business_summary(meta.get("business_summary"))
    meta["chart_annotations"] = _normalize_annotations(meta.get("chart_annotations"))
    meta["reference_overlays"] = _normalize_overlays(meta.get("reference_overlays"))
    meta["supporting_refs"] = _normalize_supporting_refs(meta.get("supporting_refs"))
    meta["data_freshness"] = _normalize_freshness(meta.get("data_freshness"))
    meta["model_freshness"] = _normalize_freshness(meta.get("model_freshness"))
    meta["news_freshness"] = _normalize_freshness(meta.get("news_freshness"))
    meta["external_indicators_mode"] = _normalize_data_provider_mode(
        meta.get("external_indicators_mode")
    )
    meta["provider_mode"] = _normalize_provider_mode(meta.get("provider_mode"))
    meta["llm_mode"] = _normalize_provider_mode(meta.get("llm_mode"))
    meta.update(request_meta(request))
    return meta


def build_kpi_summary_meta(request: Request, extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = _build_meta(request=request, defaults=_KPI_SUMMARY_DEFAULTS, extra_meta=extra_meta)
    validated = KpiSummaryMeta(
        business_summary=meta["business_summary"],
        data_freshness=meta["data_freshness"],
        margin_coverage_days=meta.get("margin_coverage_days"),
        margin_missing_days=meta.get("margin_missing_days"),
    ).model_dump(mode="json")
    meta.update(validated)
    return meta


def build_kpi_snapshot_meta(
    request: Request, extra_meta: dict[str, Any] | None = None
) -> dict[str, Any]:
    meta = _build_meta(request=request, defaults=_BASE_META_DEFAULTS, extra_meta=extra_meta)
    validated = KpiSnapshotMeta(
        business_summary=meta["business_summary"],
        chart_annotations=meta["chart_annotations"],
        reference_overlays=meta["reference_overlays"],
    ).model_dump(mode="json")
    meta.update(validated)
    return meta


def build_sales_meta(request: Request, extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = _build_meta(
        request=request,
        defaults=_ANALYTICS_SALES_DEFAULTS,
        extra_meta=extra_meta,
    )
    validated = SalesAnalyticsMeta(
        business_summary=meta["business_summary"],
        chart_annotations=meta["chart_annotations"],
        reference_overlays=meta["reference_overlays"],
        data_mode=meta.get("data_mode"),
        provider_mode=meta.get("provider_mode"),
    ).model_dump(mode="json")
    meta.update(validated)
    return meta


def build_margin_meta(request: Request, extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = _build_meta(
        request=request,
        defaults=_ANALYTICS_MARGIN_DEFAULTS,
        extra_meta=extra_meta,
    )
    validated = MarginAnalyticsMeta(
        business_summary=meta["business_summary"],
        chart_annotations=meta["chart_annotations"],
        reference_overlays=meta["reference_overlays"],
        threshold_info=meta.get("threshold_info"),
        supporting_refs=meta.get("supporting_refs"),
        provider_mode=meta.get("provider_mode"),
    ).model_dump(mode="json")
    meta.update(validated)
    return meta


def build_generic_domain_meta(
    request: Request, extra_meta: dict[str, Any] | None = None
) -> dict[str, Any]:
    return _build_meta(request=request, defaults=_BASE_META_DEFAULTS, extra_meta=extra_meta)
