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
    ExplainabilityChartPayload,
    ExplainabilityPayload,
    ExplainabilityStatePayload,
    ExplainabilityThresholdPayload,
    ExplainabilityTrustPayload,
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
    "external_context": None,
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
    "thresholds": [],
}

_EXPLAINABILITY_STATE_ALLOWED = {"ready", "empty", "degraded", "error"}


def _pick_optional(meta: dict[str, Any], *keys: str) -> dict[str, Any]:
    return {key: meta[key] for key in keys if key in meta and meta[key] is not None}


def _normalize_thresholds(
    value: Any, *, fallback_threshold_info: str | None = None
) -> list[dict[str, Any]]:
    rows = value if isinstance(value, list) else []
    normalized: list[dict[str, Any]] = []
    for item in rows:
        try:
            if isinstance(item, ExplainabilityThresholdPayload):
                normalized.append(item.model_dump(mode="json"))
            elif isinstance(item, dict):
                normalized.append(ExplainabilityThresholdPayload(**item).model_dump(mode="json"))
        except Exception:
            continue

    threshold_info = (
        fallback_threshold_info.strip() if isinstance(fallback_threshold_info, str) else None
    )
    if threshold_info:
        normalized.append(
            {
                "id": "legacy-threshold-info",
                "label": "Порог",
                "description": threshold_info,
            }
        )
    return normalized


def _resolve_explainability_state(meta: dict[str, Any]) -> dict[str, Any]:
    state_payload = meta.get("state")
    if isinstance(state_payload, dict):
        raw_status = str(state_payload.get("status", "ready")).strip().lower()
        status = raw_status if raw_status in _EXPLAINABILITY_STATE_ALLOWED else "ready"
        reason = state_payload.get("reason")
        return ExplainabilityStatePayload(status=status, reason=reason).model_dump(mode="json")

    reason = None
    status = "ready"
    if isinstance(meta.get("empty_state"), str) and meta["empty_state"].strip():
        status = "empty"
        reason = meta["empty_state"]
    elif isinstance(meta.get("degraded_reason"), str) and meta["degraded_reason"].strip():
        status = "degraded"
        reason = meta["degraded_reason"]
    elif meta.get("data_mode") == "degraded" or meta.get("data_freshness") == "degraded":
        status = "degraded"
    return ExplainabilityStatePayload(status=status, reason=reason).model_dump(mode="json")


def _build_explainability(meta: dict[str, Any]) -> dict[str, Any]:
    mode = _normalize_data_provider_mode(
        meta.get("provider_mode") or meta.get("external_indicators_mode")
    )
    trust = ExplainabilityTrustPayload(
        data_freshness=_normalize_freshness(meta.get("data_freshness")),
        mode=mode,
        data_mode=meta.get("data_mode"),
        external_context=_normalize_external_context(meta.get("external_context")),
    )
    chart = ExplainabilityChartPayload(
        annotations=_normalize_annotations(meta.get("chart_annotations")),
        overlays=_normalize_overlays(meta.get("reference_overlays")),
        thresholds=_normalize_thresholds(
            meta.get("thresholds"),
            fallback_threshold_info=meta.get("threshold_info"),
        ),
        supporting_refs=_normalize_supporting_refs(meta.get("supporting_refs")),
    )
    explainability = ExplainabilityPayload(
        summary=_normalize_business_summary(meta.get("business_summary")),
        chart=chart,
        trust=trust,
        state=_resolve_explainability_state(meta),
    )
    return explainability.model_dump(mode="json")


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


def _normalize_external_context(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
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
    meta["external_context"] = _normalize_external_context(meta.get("external_context"))
    meta.update(request_meta(request))
    return meta


def build_kpi_summary_meta(
    request: Request, extra_meta: dict[str, Any] | None = None
) -> dict[str, Any]:
    meta = _build_meta(request=request, defaults=_KPI_SUMMARY_DEFAULTS, extra_meta=extra_meta)
    explainability = _build_explainability(meta)
    validated = KpiSummaryMeta(
        explainability=explainability,
        margin_coverage_days=meta.get("margin_coverage_days"),
        margin_missing_days=meta.get("margin_missing_days"),
    ).model_dump(mode="json")
    payload: dict[str, Any] = {
        **_pick_optional(meta, "request_id", "date_from", "date_to", "product_code"),
        **validated,
    }
    return payload


def build_kpi_snapshot_meta(
    request: Request, extra_meta: dict[str, Any] | None = None
) -> dict[str, Any]:
    meta = _build_meta(request=request, defaults=_BASE_META_DEFAULTS, extra_meta=extra_meta)
    explainability = _build_explainability(meta)
    validated = KpiSnapshotMeta(
        explainability=explainability,
    ).model_dump(mode="json")
    payload: dict[str, Any] = {
        **_pick_optional(meta, "request_id", "date_from", "date_to", "product_code", "points"),
        **validated,
    }
    return payload


def build_sales_meta(request: Request, extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = _build_meta(
        request=request,
        defaults=_ANALYTICS_SALES_DEFAULTS,
        extra_meta=extra_meta,
    )
    explainability = _build_explainability(meta)
    validated = SalesAnalyticsMeta(
        explainability=explainability,
    ).model_dump(mode="json")
    payload: dict[str, Any] = {
        **_pick_optional(
            meta,
            "request_id",
            "date_from",
            "date_to",
            "product_code",
            "granularity",
            "points",
        ),
        **validated,
    }
    return payload


def build_margin_meta(request: Request, extra_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = _build_meta(
        request=request,
        defaults=_ANALYTICS_MARGIN_DEFAULTS,
        extra_meta=extra_meta,
    )
    explainability = _build_explainability(meta)
    validated = MarginAnalyticsMeta(
        explainability=explainability,
    ).model_dump(mode="json")
    payload: dict[str, Any] = {
        **_pick_optional(
            meta,
            "request_id",
            "date_from",
            "date_to",
            "product_code",
            "granularity",
            "points",
        ),
        **validated,
    }
    return payload


def build_generic_domain_meta(
    request: Request, extra_meta: dict[str, Any] | None = None
) -> dict[str, Any]:
    return _build_meta(request=request, defaults=_BASE_META_DEFAULTS, extra_meta=extra_meta)
