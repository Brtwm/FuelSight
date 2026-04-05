#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = REPO_ROOT / "scripts" / "last-smoke-result.json"


@dataclass
class StepResult:
    name: str
    status: str
    started_at: str
    finished_at: str
    duration_ms: int
    details: str


class DemoRunner:
    def __init__(self, with_airflow: bool, rebuild: bool) -> None:
        self.with_airflow = with_airflow
        self.rebuild = rebuild
        self.steps: list[StepResult] = []
        self.compose_cmd = ["docker", "compose", "-f", "compose/docker-compose.yml"]

    def run(self) -> int:
        started_at = datetime.now(UTC)
        try:
            self._step("compose_up", self._compose_up)
            self._step("wait_backend_health", self._wait_backend_health)
            if self.with_airflow:
                self._step("wait_airflow_health", self._wait_airflow_health)

            self._step(
                "backend_migrate",
                lambda: self._run_command(
                    self.compose_cmd + ["exec", "-T", "backend", "uv", "run", "alembic", "upgrade", "head"]
                ),
            )
            self._step(
                "backend_seed",
                lambda: self._run_command(
                    self.compose_cmd + ["exec", "-T", "backend", "uv", "run", "fuelsight-seed-core"]
                ),
            )
            self._step(
                "generate_demo_data",
                lambda: self._run_command(
                    self.compose_cmd
                    + [
                        "exec",
                        "-T",
                        "backend",
                        "uv",
                        "run",
                        "python",
                        "-m",
                        "app.scripts.pipeline_runner",
                        "generate-demo-data",
                        "--replace-existing",
                        "--start-date",
                        "2025-01-01",
                        "--end-date",
                        "2025-12-31",
                    ]
                ),
            )
            self._step(
                "build_feature_store",
                lambda: self._run_command(
                    self.compose_cmd
                    + [
                        "exec",
                        "-T",
                        "backend",
                        "uv",
                        "run",
                        "python",
                        "-m",
                        "app.scripts.pipeline_runner",
                        "build-feature-store-daily",
                    ]
                ),
            )
            self._step(
                "train_models_weekly",
                lambda: self._run_command(
                    self.compose_cmd
                    + [
                        "exec",
                        "-T",
                        "backend",
                        "uv",
                        "run",
                        "python",
                        "-m",
                        "app.scripts.pipeline_runner",
                        "train-models-weekly",
                    ]
                ),
            )
            self._step(
                "external_indicators_stub",
                lambda: self._run_command(
                    self.compose_cmd
                    + [
                        "exec",
                        "-T",
                        "backend",
                        "uv",
                        "run",
                        "python",
                        "-m",
                        "app.scripts.pipeline_runner",
                        "ingest-external-indicators-daily",
                    ]
                ),
            )

            self._step("api_healthcheck", self._check_api_health)
            if self.with_airflow:
                self._step("airflow_dag_contract", self._check_airflow_dags)

            self._write_summary(started_at=started_at, status="PASS")
            return 0
        except Exception as exc:
            self._write_summary(started_at=started_at, status="FAIL", error=str(exc))
            return 1

    def _step(self, name: str, action) -> None:
        started = datetime.now(UTC)
        try:
            details = action()
            status = "PASS"
            if not details:
                details = "ok"
        except Exception as exc:
            finished = datetime.now(UTC)
            self.steps.append(
                StepResult(
                    name=name,
                    status="FAIL",
                    started_at=started.isoformat(),
                    finished_at=finished.isoformat(),
                    duration_ms=int((finished - started).total_seconds() * 1000),
                    details=str(exc),
                )
            )
            raise

        finished = datetime.now(UTC)
        self.steps.append(
            StepResult(
                name=name,
                status=status,
                started_at=started.isoformat(),
                finished_at=finished.isoformat(),
                duration_ms=int((finished - started).total_seconds() * 1000),
                details=details,
            )
        )

    def _compose_up(self) -> str:
        args = self.compose_cmd + ["--profile", "core"]
        if self.with_airflow:
            args += ["--profile", "airflow"]
        args += ["up", "-d"]
        if self.rebuild:
            args.append("--build")
        self._run_command(args)
        return "core services are up"

    def _wait_backend_health(self) -> str:
        self._wait_http("http://localhost:8061/api/v1/health", timeout_sec=180)
        return "backend health endpoint is ready"

    def _wait_airflow_health(self) -> str:
        self._wait_http("http://localhost:8080/health", timeout_sec=240)
        return "airflow webserver health endpoint is ready"

    def _check_api_health(self) -> str:
        payload = self._read_json_url("http://localhost:8061/api/v1/health")
        if payload.get("data", {}).get("ok") is not True:
            raise RuntimeError("Backend health payload does not contain data.ok=true")
        return "backend API health contract is valid"

    def _check_airflow_dags(self) -> str:
        output = self._run_command(
            self.compose_cmd + ["exec", "-T", "airflow-webserver", "airflow", "dags", "list", "--output", "json"]
        )
        rows = None
        for line in output.splitlines():
            normalized = line.strip()
            if normalized.startswith("["):
                rows = json.loads(normalized)
                break
        if rows is None:
            rows = json.loads(output)
        dag_ids = {item["dag_id"] for item in rows}
        expected = {
            "ingest_internal_sales_daily",
            "ingest_internal_purchases_daily",
            "build_feature_store_daily",
            "train_models_weekly",
            "ingest_external_indicators_daily",
        }
        missing = sorted(expected - dag_ids)
        if missing:
            raise RuntimeError(f"Missing DAG ids: {', '.join(missing)}")
        return "all Phase 7 DAG ids are registered"

    @staticmethod
    def _run_command(args: list[str]) -> str:
        process = subprocess.run(
            args,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            stderr = process.stderr.strip()
            stdout = process.stdout.strip()
            message = stderr or stdout or f"command failed with code {process.returncode}"
            raise RuntimeError(f"{args}: {message}")
        return process.stdout.strip() or "ok"

    @staticmethod
    def _wait_http(url: str, timeout_sec: int) -> None:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            try:
                with urlopen(url, timeout=3) as response:
                    if response.status < 400:
                        return
            except Exception:
                pass
            time.sleep(2)
        raise RuntimeError(f"Timeout waiting for {url}")

    @staticmethod
    def _read_json_url(url: str) -> dict:
        with urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _write_summary(self, *, started_at: datetime, status: str, error: str | None = None) -> None:
        finished_at = datetime.now(UTC)
        payload = {
            "status": status,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_ms": int((finished_at - started_at).total_seconds() * 1000),
            "steps": [asdict(step) for step in self.steps],
            "logs_hint": "docker compose -f compose/docker-compose.yml logs --tail=200",
        }
        if error:
            payload["error"] = error

        RESULT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full FuelSight demo chain")
    parser.add_argument("--without-airflow", action="store_true", help="Run only core stack")
    parser.add_argument("--no-build", action="store_true", help="Skip image rebuild")
    args = parser.parse_args()

    runner = DemoRunner(with_airflow=not args.without_airflow, rebuild=not args.no_build)
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
