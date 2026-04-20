from __future__ import annotations

import json
from types import SimpleNamespace

from app.services.external_context_service import ExternalContextService


def test_external_context_service_handles_missing_cache_dir() -> None:
    service = ExternalContextService(settings=SimpleNamespace())
    context = service.build_external_context()

    assert context["quality_status"] == "failed"
    assert "external_manifest_missing" in context["reasons"]
    assert context["fallback_ratio"] == 1.0


def test_external_context_service_reads_latest_manifest(tmp_path) -> None:  # noqa: ANN001
    manifests_dir = tmp_path / "manifests" / "2026-04-20"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifests_dir / "external_indicators_manifest_run-123.json"
    manifest_path.write_text(
        json.dumps(
            {
                "run_id": "run-123",
                "run_date": "2026-04-20",
                "status": "warning",
                "coverage_ratio": 0.94,
                "fallback_ratio": 0.27,
                "provider_mode_counts": {"cached": 12, "live": 8},
                "indicator_coverage": [
                    {
                        "indicator_code": "usd_rub",
                        "coverage_ratio": 0.9,
                        "provider_mode": "cached",
                        "latest_mode": "cached",
                        "latest_date": "2026-04-20",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    service = ExternalContextService(
        settings=SimpleNamespace(external_cache_dir=str(tmp_path)),
    )
    context = service.build_external_context()

    assert context["quality_status"] == "warning"
    assert context["provider_mode"] == "cached"
    assert context["manifest_run_date"] == "2026-04-20"
    assert context["source_refs"]
