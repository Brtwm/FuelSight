from __future__ import annotations

import importlib.util
import subprocess
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

    def fake_request_json(
        *, method, url, payload=None, headers=None, expected_statuses=None, timeout_sec=15
    ):
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


def test_demo_runner_applies_offline_safe_compose_profile_and_manual_providers(monkeypatch):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=False,
        with_mobile_e2e=False,
        profile="offline-safe",
    )
    commands: list[list[str]] = []

    def fake_run_command(command: list[str]) -> str:
        commands.append(command)
        if "refresh-news-daily" in command:
            return (
                '{"result":{"status":"ok","manifest_path":"/tmp/news.json",'
                '"provider_mode":"manual_snapshot","written_news_count":5,'
                '"created_digests":1,"coverage_ratio":1.0}}'
            )
        if "ingest-external-indicators-daily" in command:
            return (
                '{"result":{"status":"ok","quality_status":"ok","manifest_path":"/tmp/ext.json",'
                '"expected_points":10,"written_points":10,"fallback_ratio":0.0,'
                '"coverage_ratio":1.0}}'
            )
        if command[-2:] in (["-f", "/tmp/news.json"], ["-f", "/tmp/ext.json"]):
            return ""
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    runner._refresh_news()
    runner._refresh_external_indicators()

    assert "compose/docker-compose.offline-safe.yml" in runner.compose_cmd
    provider_values = [
        command[command.index("--provider") + 1] for command in commands if "--provider" in command
    ]
    news_command = next(command for command in commands if "refresh-news-daily" in command)
    assert provider_values == ["manual_snapshot", "manual_snapshot"]
    assert news_command[news_command.index("--lookback-days") + 1] == "30"


def test_demo_runner_cloud_enhanced_uses_cloud_profile_and_auto_providers(monkeypatch):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=False,
        with_mobile_e2e=False,
        profile="cloud-enhanced",
    )
    commands: list[list[str]] = []

    def fake_run_command(command: list[str]) -> str:
        commands.append(command)
        if "refresh-news-daily" in command:
            return (
                '{"result":{"status":"ok","manifest_path":"/tmp/news.json",'
                '"provider_mode":"live","written_news_count":5,'
                '"created_digests":1,"coverage_ratio":1.0}}'
            )
        if "ingest-external-indicators-daily" in command:
            return (
                '{"result":{"status":"ok","quality_status":"ok","manifest_path":"/tmp/ext.json",'
                '"expected_points":10,"written_points":10,"fallback_ratio":0.0,'
                '"coverage_ratio":1.0}}'
            )
        if command[-2:] in (["-f", "/tmp/news.json"], ["-f", "/tmp/ext.json"]):
            return ""
        raise AssertionError(f"Unexpected command: {command}")

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    runner._refresh_news()
    runner._refresh_external_indicators()

    assert "compose/docker-compose.cloud-enhanced.yml" in runner.compose_cmd
    provider_values = [
        command[command.index("--provider") + 1] for command in commands if "--provider" in command
    ]
    news_command = next(command for command in commands if "refresh-news-daily" in command)
    assert provider_values == ["auto", "auto"]
    assert news_command[news_command.index("--lookback-days") + 1] == "14"


def test_cloud_provider_fallback_smoke_requires_fallback_verified_when_degraded(monkeypatch):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=False,
        with_mobile_e2e=False,
    )

    monkeypatch.setattr(
        runner,
        "_read_json_url",
        lambda url: {
            "data": {
                "ok": True,
                "llm_active": {
                    "provider": "neuraldeep",
                    "mode": "cloud_llm",
                    "model": "gpt-oss-120b",
                    "degradation_reason": None,
                },
            },
            "error": None,
            "meta": {},
        },
    )
    monkeypatch.setattr(runner, "_api_login", lambda **_: "token")

    timeouts_by_url: dict[str, int] = {}

    def fake_request_json(
        *, method, url, payload=None, headers=None, expected_statuses=None, timeout_sec=15
    ):
        timeouts_by_url[url] = timeout_sec
        if url.endswith("/api/v1/chat/sessions"):
            return {"data": {"id": "session-1"}, "error": None, "meta": {}}, 200
        if url.endswith("/api/v1/chat/sessions/session-1/messages"):
            return {
                "data": {
                    "answer": "По найденным источникам...",
                    "citations": [{"ref_id": "analytics_margin_AI_95", "title": "Маржа"}],
                    "mode": "retrieval_only",
                    "verification": {
                        "status": "fallback_verified",
                        "reason": "provider_unavailable",
                        "severity": "warning",
                    },
                },
                "error": None,
                "meta": {
                    "llm_provider": {
                        "provider": "neuraldeep",
                        "mode": "retrieval_only",
                        "model": "gpt-oss-120b",
                        "degradation_reason": "cloud_provider_unavailable",
                    }
                },
            }, 200
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(runner, "_request_json", fake_request_json)

    result = runner._check_cloud_provider_fallback_api_flow()

    assert "cloud provider fallback smoke passed" in result
    assert "cloud_provider_unavailable" in result
    assert timeouts_by_url["http://localhost:8061/api/v1/chat/sessions/session-1/messages"] == 90


def test_cloud_enhanced_smoke_fails_when_cloud_llm_is_inactive(monkeypatch):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=False,
        with_mobile_e2e=False,
        profile="cloud-enhanced",
    )

    monkeypatch.setattr(
        runner,
        "_read_json_url",
        lambda url: {
            "data": {
                "ok": True,
                "llm_active": {
                    "provider": "none",
                    "mode": "retrieval_only",
                    "model": None,
                    "degradation_reason": "cloud_api_key_missing",
                },
            },
            "error": None,
            "meta": {},
        },
    )

    try:
        runner._check_cloud_provider_fallback_api_flow()
    except RuntimeError as exc:
        assert "cloud LLM is not active" in str(exc)
        assert "cloud_api_key_missing" in str(exc)
    else:
        raise AssertionError("Expected inactive cloud LLM to fail cloud-enhanced smoke")


def test_cloud_enhanced_run_skips_llm_off_smoke(monkeypatch, tmp_path):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=False,
        with_mobile_e2e=False,
        profile="cloud-enhanced",
    )
    step_names: list[str] = []

    monkeypatch.setattr(run_full_demo, "RESULT_PATH", tmp_path / "last-smoke-result.json")
    monkeypatch.setattr(runner, "_check_llm_off_api_flow", lambda: "unexpected")

    def recording_step(name, func):
        step_names.append(name)
        return None

    monkeypatch.setattr(runner, "_step", recording_step)

    assert runner.run() == 0
    assert "llm_off_smoke" not in step_names
    assert "cloud_provider_fallback_smoke" in step_names


def test_run_command_handles_missing_process_streams(monkeypatch):
    run_full_demo = _load_run_full_demo_module()

    captured_kwargs: dict[str, object] = {}

    def fake_run(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout=None, stderr=None)

    monkeypatch.setattr(run_full_demo.subprocess, "run", fake_run)

    try:
        run_full_demo.DemoRunner._run_command(["demo"])
    except RuntimeError as exc:
        assert "command failed with code 1" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")

    assert captured_kwargs["encoding"] == "utf-8"
    assert captured_kwargs["errors"] == "replace"


def test_demo_runner_uses_split_playwright_scripts(monkeypatch):
    run_full_demo = _load_run_full_demo_module()
    runner = run_full_demo.DemoRunner(
        with_airflow=False,
        rebuild=False,
        with_e2e=True,
        with_mobile_e2e=True,
    )
    commands: list[list[str]] = []

    monkeypatch.setattr(run_full_demo.shutil, "which", lambda name: f"C:/bin/{name}.cmd")

    def fake_run_command(command: list[str]) -> str:
        commands.append(command)
        return "ok"

    monkeypatch.setattr(runner, "_run_command", fake_run_command)

    runner._run_frontend_e2e()
    runner._run_frontend_mobile_e2e()

    assert commands[0][-1] == "test:e2e:desktop"
    assert commands[1][-1] == "test:e2e:mobile"
