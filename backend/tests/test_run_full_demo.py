from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_run_full_demo_module():
    module_path = Path(__file__).resolve().parents[2] / "scripts" / "run_full_demo.py"
    spec = importlib.util.spec_from_file_location("run_full_demo", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_core_api_flow_waits_for_generated_demo_job_before_reading_analytics(monkeypatch):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=False,
        with_mobile_e2e=False,
    )
    calls: list[str] = []
    job_statuses = iter(["queued", "processing", "completed"])
    job_id = "11111111-1111-1111-1111-111111111111"

    monkeypatch.setattr(runner, "_api_login", lambda **_: "token")
    monkeypatch.setattr(runner, "_demo_date_window", lambda: ("2025-04-26", "2026-04-25"))
    monkeypatch.setattr(run_full_demo.time, "sleep", lambda _: None)

    def fake_request_json(*, method, url, payload=None, headers=None, expected_statuses=None):
        calls.append(url)
        if url.endswith("/api/v1/import/generate-demo"):
            return {"data": {"job_id": job_id}, "error": None, "meta": {}}, 202
        if url.endswith(f"/api/v1/import/jobs/{job_id}"):
            return {
                "data": {"id": job_id, "status": next(job_statuses)},
                "error": None,
                "meta": {},
            }, 200
        if url.endswith("/api/v1/backtests/latest?product_code=AI_95&horizon_days=7"):
            return {"data": {"metrics": {"smape": 4.8}}, "error": None, "meta": {}}, 200
        return {"data": {}, "error": None, "meta": {}}, 200

    monkeypatch.setattr(runner, "_request_json", fake_request_json)

    runner._check_core_api_flow()

    job_poll_indexes = [
        index for index, url in enumerate(calls) if url.endswith(f"/api/v1/import/jobs/{job_id}")
    ]
    kpi_index = calls.index("http://localhost:8061/api/v1/kpi/summary?product_code=AI_95")

    assert len(job_poll_indexes) == 3
    assert job_poll_indexes[-1] < kpi_index


def test_rag_index_refresh_requires_manifest_and_written_chunks(monkeypatch):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=False,
        with_mobile_e2e=False,
    )
    commands: list[list[str]] = []

    def fake_run_command(command: list[str]) -> str:
        commands.append(command)
        if "refresh-rag-index-daily" in command:
            return (
                '{"result":{"manifest_path":'
                '"/opt/fuelsight/artifacts/news/manifests/rag.json","written_chunks":3}}'
            )
        if command[-2:] == ["-f", "/opt/fuelsight/artifacts/news/manifests/rag.json"]:
            return ""
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    result = runner._refresh_rag_index()

    assert "written_chunks=3" in result
    assert any("refresh-rag-index-daily" in command for command in commands)
    assert commands[-2:] == [
        [
            *runner.compose_cmd,
            "exec",
            "-T",
            "backend",
            "uv",
            "run",
            "python",
            "-m",
            "app.scripts.pipeline_runner",
            "refresh-rag-index-daily",
        ],
        [
            *runner.compose_cmd,
            "exec",
            "-T",
            "backend",
            "test",
            "-f",
            "/opt/fuelsight/artifacts/news/manifests/rag.json",
        ],
    ]
