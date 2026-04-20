from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings


class ExternalContextService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def build_external_context(
        self,
        *,
        source_refs: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        manifest = self._load_latest_external_manifest()
        if manifest is None:
            return {
                "provider_mode": None,
                "coverage_ratio": 0.0,
                "fallback_ratio": 1.0,
                "quality_status": "failed",
                "reasons": ["external_manifest_missing"],
                "manifest_run_date": None,
                "source_refs": source_refs or [],
            }

        provider_mode = _resolve_provider_mode(manifest)
        coverage_ratio = float(manifest.get("coverage_ratio") or 0.0)
        fallback_ratio = float(manifest.get("fallback_ratio") or 1.0)
        run_date = manifest.get("run_date")
        quality_status = str(manifest.get("quality_status") or manifest.get("status") or "").strip().lower()
        reasons = [str(item) for item in manifest.get("reasons") or [] if isinstance(item, str)]
        if quality_status not in {"ok", "warning", "degraded", "failed"}:
            quality_status, fallback_reasons = _classify_quality(
                coverage_ratio=coverage_ratio,
                fallback_ratio=fallback_ratio,
            )
            if not reasons:
                reasons = fallback_reasons

        resolved_refs = source_refs if source_refs is not None else self._build_refs_from_manifest(manifest)
        return {
            "provider_mode": provider_mode,
            "coverage_ratio": round(coverage_ratio, 6),
            "fallback_ratio": round(fallback_ratio, 6),
            "quality_status": quality_status,
            "reasons": reasons,
            "manifest_run_date": run_date if isinstance(run_date, str) else None,
            "source_refs": resolved_refs,
        }

    def build_external_context_quality(self) -> dict[str, Any]:
        context = self.build_external_context()
        return {
            "provider_mode": context.get("provider_mode"),
            "coverage_ratio": context.get("coverage_ratio"),
            "fallback_ratio": context.get("fallback_ratio"),
            "quality_status": context.get("quality_status"),
            "reasons": context.get("reasons"),
            "manifest_run_date": context.get("manifest_run_date"),
            "source_refs": context.get("source_refs"),
        }

    def _load_latest_external_manifest(self) -> dict[str, Any] | None:
        cache_dir = getattr(self._settings, "external_cache_dir", None)
        if not isinstance(cache_dir, str) or not cache_dir.strip():
            return None
        root = Path(cache_dir) / "manifests"
        if not root.exists():
            return None
        manifests = sorted(
            root.glob("*/external_indicators_manifest_*.json"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        if not manifests:
            return None
        payload = json.loads(manifests[0].read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        payload["manifest_path"] = str(manifests[0])
        return payload

    @staticmethod
    def _build_refs_from_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        for item in manifest.get("indicator_coverage") or []:
            if not isinstance(item, dict):
                continue
            code = str(item.get("indicator_code") or "").strip()
            latest_date = str(item.get("latest_date") or "").strip()
            if not code or not latest_date:
                continue
            refs.append(
                {
                    "type": "indicator",
                    "ref_id": f"indicator:{code}:{latest_date}",
                    "title": (
                        f"{code}: coverage={float(item.get('coverage_ratio') or 0.0):.2f}, "
                        f"mode={item.get('provider_mode') or item.get('latest_mode')}"
                    ),
                    "provider_mode": item.get("provider_mode") or item.get("latest_mode"),
                    "source_type": "external_indicator",
                    "confidence": _confidence_for_mode(item.get("provider_mode") or item.get("latest_mode")),
                }
            )
            if len(refs) >= 5:
                break
        return refs


def _resolve_provider_mode(manifest: dict[str, Any]) -> str | None:
    mode = manifest.get("provider_mode")
    if isinstance(mode, str) and mode.strip():
        return mode.strip().lower()
    mode_counts = manifest.get("provider_mode_counts")
    if isinstance(mode_counts, dict) and mode_counts:
        sorted_modes = sorted(
            [(str(key), int(value)) for key, value in mode_counts.items()],
            key=lambda item: item[1],
            reverse=True,
        )
        if sorted_modes:
            return sorted_modes[0][0]
    return None


def _classify_quality(*, coverage_ratio: float, fallback_ratio: float) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if coverage_ratio < 0.85:
        reasons.append(f"coverage_ratio={coverage_ratio:.3f}<0.85")
    elif coverage_ratio < 0.95:
        reasons.append(f"coverage_ratio={coverage_ratio:.3f}<0.95")
    if fallback_ratio > 0.5:
        reasons.append(f"fallback_ratio={fallback_ratio:.3f}>0.5")
    elif fallback_ratio > 0.25:
        reasons.append(f"fallback_ratio={fallback_ratio:.3f}>0.25")
    if coverage_ratio < 0.85 or fallback_ratio > 0.5:
        return "degraded", reasons
    if reasons:
        return "warning", reasons
    return "ok", reasons


def _confidence_for_mode(mode: Any) -> float | None:
    normalized = str(mode).strip().lower() if mode is not None else ""
    if normalized == "live":
        return 0.9
    if normalized == "cached":
        return 0.75
    if normalized == "manual_snapshot":
        return 0.6
    return None
