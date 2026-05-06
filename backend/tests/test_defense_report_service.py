from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.schemas.defense import DefenseReportPayload
from app.services.defense_report_service import DefenseReportService


def test_defense_report_treats_offline_retrieval_as_expected_mode(tmp_path: Path) -> None:
    service = DefenseReportService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(
            model_artifacts_dir=str(tmp_path),
            defense_profile="offline-safe",
            enable_llm=False,
            llm_provider_mode="retrieval_only",
        ),
    )

    steps = service._build_steps(  # noqa: SLF001
        profile="offline-safe",
        data_quality={"status": "ok", "coverage_ratio": 1.0},
        model_quality={"status": "ok", "smape": 4.2},
        provider_modes={"llm_active": {"mode": "retrieval_only"}},
        executive_summary={"news_digest": {"summary": "ok"}, "forecast": {"items": []}},
    )

    llm_step = next(step for step in steps if step["name"] == "llm_mode")
    assert llm_step["status"] == "ok"
    assert "Offline-safe" in llm_step["details"]


def test_defense_report_marks_cloud_enhanced_missing_cloud_as_warning(tmp_path: Path) -> None:
    service = DefenseReportService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(model_artifacts_dir=str(tmp_path), defense_profile="cloud-enhanced"),
    )

    steps = service._build_steps(  # noqa: SLF001
        profile="cloud-enhanced",
        data_quality={"status": "ok", "coverage_ratio": 1.0},
        model_quality={"status": "ok", "smape": 4.2},
        provider_modes={"llm_active": {"mode": "retrieval_only"}},
        executive_summary={"news_digest": {"summary": "ok"}, "forecast": {"items": []}},
    )

    llm_step = next(step for step in steps if step["name"] == "llm_mode")
    assert llm_step["status"] == "warning"
    assert service._overall_status([step["status"] for step in steps]) == "warning"  # noqa: SLF001


def test_defense_report_reads_enriched_winner_metrics(tmp_path: Path) -> None:
    service = DefenseReportService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(model_artifacts_dir=str(tmp_path)),
    )

    metrics = service._resolve_backtest_metrics(  # noqa: SLF001
        {
            "winner_metrics": {
                "mae": 412.0,
                "rmse": 553.0,
                "smape": 4.8,
            },
            "comparison": {},
        }
    )

    assert metrics == {"mae": 412.0, "rmse": 553.0, "smape": 4.8}


def test_defense_report_keeps_legacy_root_metrics(tmp_path: Path) -> None:
    service = DefenseReportService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(model_artifacts_dir=str(tmp_path)),
    )

    metrics = service._resolve_backtest_metrics(  # noqa: SLF001
        {"mae": 510.0, "rmse": 680.0, "smape": 5.3}
    )

    assert metrics == {"mae": 510.0, "rmse": 680.0, "smape": 5.3}


def test_defense_report_prefers_demo_product_for_executive_output(tmp_path: Path) -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.calls = 0

        def scalar(self, statement):  # noqa: ANN001
            self.calls += 1
            return "AI_95" if self.calls == 1 else "AI_92"

    service = DefenseReportService(
        session=FakeSession(),  # type: ignore[arg-type]
        settings=Settings(model_artifacts_dir=str(tmp_path)),
    )

    assert service._default_product_code() == "AI_95"  # noqa: SLF001


def test_defense_pdf_export_creates_non_empty_cyrillic_report(tmp_path: Path) -> None:
    service = DefenseReportService(
        session=None,  # type: ignore[arg-type]
        settings=Settings(model_artifacts_dir=str(tmp_path), defense_profile="offline-safe"),
    )
    report = DefenseReportPayload(
        run_id="run-001",
        generated_at="2026-05-03T12:00:00+00:00",
        profile="offline-safe",
        overall_status="ok",
        badges=[{"label": "Defense", "status": "ok", "value": "offline-safe"}],
        data_quality={"status": "ok"},
        model_quality={"status": "ok", "smape": 4.2, "model_type": "catboost"},
        provider_modes={"llm_active": {"mode": "retrieval_only"}},
        executive_summary={
            "kpi": {
                "revenue_rub": 1000000,
                "gross_margin_rub": 180000,
                "sales_volume_liters": 20000,
            },
            "news_digest": {"bullet_points": ["Маржа стабильна по внутренним данным."]},
        },
        decision_journal=["Профиль защиты: offline-safe."],
    )

    artifacts = service.write_artifacts(report)

    json_path = Path(artifacts["json"])
    pdf_path = Path(artifacts["pdf"])
    assert json_path.exists()
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")
    assert pdf_path.stat().st_size > 1000
