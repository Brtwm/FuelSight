#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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
    def __init__(self, with_airflow: bool, rebuild: bool, with_e2e: bool) -> None:
        self.with_airflow = with_airflow
        self.rebuild = rebuild
        self.with_e2e = with_e2e
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
            self._step("core_api_flow_smoke", self._check_core_api_flow)
            self._step("llm_off_smoke", self._check_llm_off_api_flow)
            if self.with_airflow:
                self._step("airflow_dag_contract", self._check_airflow_dags)
            if self.with_e2e:
                self._step("frontend_e2e_happy_path", self._run_frontend_e2e)

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

    def _request_json(
        self,
        *,
        method: str,
        url: str,
        payload: dict | None = None,
        headers: dict[str, str] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> tuple[dict, int]:
        expected = expected_statuses or {200}
        request_headers = {"accept": "application/json"}
        if headers:
            request_headers.update(headers)
        body = None
        if payload is not None:
            request_headers["content-type"] = "application/json"
            body = json.dumps(payload).encode("utf-8")

        request = Request(url=url, data=body, headers=request_headers, method=method.upper())
        status = 0
        raw_payload = ""
        try:
            with urlopen(request, timeout=15) as response:
                status = response.status
                raw_payload = response.read().decode("utf-8")
        except HTTPError as exc:
            status = exc.code
            raw_payload = exc.read().decode("utf-8")

        if status not in expected:
            raise RuntimeError(f"Unexpected status {status} for {method} {url}: {raw_payload}")

        try:
            parsed = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON response for {method} {url}: {raw_payload}") from exc

        return parsed, status

    @staticmethod
    def _require_envelope_ok(payload: dict, *, endpoint: str) -> None:
        if not isinstance(payload, dict) or {"data", "error", "meta"} - payload.keys():
            raise RuntimeError(f"{endpoint}: invalid envelope shape")
        if payload.get("error") is not None:
            raise RuntimeError(f"{endpoint}: expected error=null, got {payload.get('error')}")

    def _api_login(self, *, email: str, password: str) -> str:
        payload, _ = self._request_json(
            method="POST",
            url="http://localhost:8061/api/v1/auth/login",
            payload={"email": email, "password": password},
        )
        self._require_envelope_ok(payload, endpoint="/auth/login")
        access_token = payload.get("data", {}).get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise RuntimeError("/auth/login: missing access_token")
        return access_token

    def _check_core_api_flow(self) -> str:
        token = self._api_login(email="admin@fuelsight.local", password="admin12345")
        auth_headers = {"authorization": f"Bearer {token}"}

        generate_demo_payload, generate_status = self._request_json(
            method="POST",
            url="http://localhost:8061/api/v1/import/generate-demo",
            payload={
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "products": ["AI_92", "AI_95", "DT_S", "DT_W"],
                "seed": 42,
                "replace_existing": True,
            },
            headers=auth_headers,
            expected_statuses={202},
        )
        self._require_envelope_ok(generate_demo_payload, endpoint="/import/generate-demo")

        kpi_payload, _ = self._request_json(
            method="GET",
            url="http://localhost:8061/api/v1/kpi/summary?product_code=AI_95",
            headers=auth_headers,
        )
        self._require_envelope_ok(kpi_payload, endpoint="/kpi/summary")

        sales_payload, _ = self._request_json(
            method="GET",
            url="http://localhost:8061/api/v1/analytics/sales?product_code=AI_95&granularity=day",
            headers=auth_headers,
        )
        self._require_envelope_ok(sales_payload, endpoint="/analytics/sales")

        margin_payload, _ = self._request_json(
            method="GET",
            url="http://localhost:8061/api/v1/analytics/margin?product_code=AI_95&granularity=day",
            headers=auth_headers,
        )
        self._require_envelope_ok(margin_payload, endpoint="/analytics/margin")

        forecast_payload, _ = self._request_json(
            method="POST",
            url="http://localhost:8061/api/v1/forecasts/run",
            payload={
                "product_code": "AI_95",
                "horizon_days": 7,
                "scenario": {"retail_price_delta_pct": 2.5},
            },
            headers=auth_headers,
        )
        self._require_envelope_ok(forecast_payload, endpoint="/forecasts/run")

        backtest_payload, _ = self._request_json(
            method="GET",
            url="http://localhost:8061/api/v1/backtests/latest?product_code=AI_95&horizon_days=7",
            headers=auth_headers,
        )
        self._require_envelope_ok(backtest_payload, endpoint="/backtests/latest")
        if backtest_payload.get("data") is None:
            raise RuntimeError("/backtests/latest: expected non-empty data after pipeline training")

        return (
            "core flow smoke passed: "
            f"generate_demo_status={generate_status}, "
            "kpi/sales/margin/forecast/backtest contracts are valid"
        )

    def _check_llm_off_api_flow(self) -> str:
        token = self._api_login(email="analyst@fuelsight.local", password="analyst12345")
        auth_headers = {"authorization": f"Bearer {token}"}

        digest_payload, _ = self._request_json(
            method="GET",
            url="http://localhost:8061/api/v1/news/digests/latest?period_type=daily",
            headers=auth_headers,
        )
        self._require_envelope_ok(digest_payload, endpoint="/news/digests/latest")

        search_payload, _ = self._request_json(
            method="GET",
            url="http://localhost:8061/api/v1/news/search?q=logistics",
            headers=auth_headers,
        )
        self._require_envelope_ok(search_payload, endpoint="/news/search")

        session_payload, _ = self._request_json(
            method="POST",
            url="http://localhost:8061/api/v1/chat/sessions",
            payload={"title": "LLM off smoke"},
            headers=auth_headers,
        )
        self._require_envelope_ok(session_payload, endpoint="/chat/sessions")
        session_id = session_payload.get("data", {}).get("id")
        if not isinstance(session_id, str) or not session_id:
            raise RuntimeError("/chat/sessions: missing session id")

        chat_payload, chat_status = self._request_json(
            method="POST",
            url=f"http://localhost:8061/api/v1/chat/sessions/{session_id}/messages",
            payload={
                "question": "Почему упала маржа?",
                "context_scope": ["internal_analytics", "news_digest"],
            },
            headers=auth_headers,
            expected_statuses={503},
        )
        error_code = chat_payload.get("error", {}).get("code")
        if chat_status != 503 or error_code != "llm_disabled":
            raise RuntimeError(
                "/chat/sessions/{id}/messages: expected 503 llm_disabled with ENABLE_LLM=false"
            )

        return "LLM off smoke passed: digest/search alive, chat generation returns 503 llm_disabled"

    def _run_frontend_e2e(self) -> str:
        corepack_bin = shutil.which("corepack") or shutil.which("corepack.cmd")
        pnpm_bin = shutil.which("pnpm") or shutil.which("pnpm.cmd")
        if corepack_bin:
            command = [corepack_bin, "pnpm", "--filter", "frontend", "test:e2e"]
        elif pnpm_bin:
            command = [pnpm_bin, "--filter", "frontend", "test:e2e"]
        else:
            raise RuntimeError("Neither corepack nor pnpm is available in PATH for frontend_e2e_happy_path")

        output = self._run_command(
            command
        )
        return output or "frontend playwright happy-path passed"

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
        return "all Phase 9 DAG ids are registered"

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
    parser.add_argument("--with-e2e", action="store_true", help="Run Playwright E2E happy-path after smoke")
    args = parser.parse_args()

    runner = DemoRunner(
        with_airflow=not args.without_airflow,
        rebuild=not args.no_build,
        with_e2e=args.with_e2e,
    )
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
