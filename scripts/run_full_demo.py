#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = REPO_ROOT / "scripts" / "last-smoke-result.json"
DEFENSE_RESULT_PATH = REPO_ROOT / "scripts" / "last-defense-report.json"
DEMO_HISTORY_DAYS = 365
IMPORT_JOB_POLL_INTERVAL_SEC = 2
IMPORT_JOB_TIMEOUT_SEC = 180
IMPORT_JOB_TERMINAL_STATUSES = {"completed", "completed_with_errors", "failed"}
DEMO_PROFILES = {"offline-safe", "cloud-enhanced"}


@dataclass
class StepResult:
    name: str
    status: str
    started_at: str
    finished_at: str
    duration_ms: int
    details: str


@dataclass(frozen=True)
class StepOutcome:
    status: str
    details: str


class DemoRunner:
    def __init__(
        self,
        with_airflow: bool,
        rebuild: bool,
        with_e2e: bool,
        with_mobile_e2e: bool,
        profile: str = "offline-safe",
    ) -> None:
        normalized_profile = profile.strip().lower()
        if normalized_profile not in DEMO_PROFILES:
            raise ValueError("profile must be one of offline-safe, cloud-enhanced")
        self.profile = normalized_profile
        self.with_airflow = with_airflow
        self.rebuild = rebuild
        self.with_e2e = with_e2e
        self.with_mobile_e2e = with_mobile_e2e
        self.steps: list[StepResult] = []
        self.compose_cmd = [
            "docker",
            "compose",
            "-f",
            "compose/docker-compose.yml",
            "-f",
            f"compose/docker-compose.{self.profile}.yml",
        ]

    @staticmethod
    def _demo_date_window() -> tuple[str, str]:
        end_date = datetime.now(UTC).date()
        start_date = end_date - timedelta(days=DEMO_HISTORY_DAYS - 1)
        return start_date.isoformat(), end_date.isoformat()

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
            demo_start_date, demo_end_date = self._demo_date_window()
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
                        demo_start_date,
                        "--end-date",
                        demo_end_date,
                    ]
                ),
            )
            self._step(
                "external_indicators_refresh",
                self._refresh_external_indicators,
            )
            self._step(
                "build_feature_store",
                self._build_feature_store_refresh,
            )
            self._step(
                "train_models_weekly",
                self._train_models_weekly,
            )
            self._step(
                "news_refresh",
                self._refresh_news,
            )
            self._step(
                "rag_index_refresh",
                self._refresh_rag_index,
            )

            self._step("api_healthcheck", self._check_api_health)
            self._step("core_api_flow_smoke", self._check_core_api_flow)
            if self.profile == "offline-safe":
                self._step("llm_off_smoke", self._check_llm_off_api_flow)
            self._step("cloud_provider_fallback_smoke", self._check_cloud_provider_fallback_api_flow)
            if self.with_airflow:
                self._step("airflow_dag_contract", self._check_airflow_dags)
            if self.with_e2e:
                self._step("frontend_e2e_happy_path", self._run_frontend_e2e)
            if self.with_mobile_e2e:
                self._step("frontend_e2e_mobile_smoke", self._run_frontend_mobile_e2e)

            self._step("defense_report", self._build_defense_report)
            self._write_summary(started_at=started_at, status="PASS")
            return 0
        except Exception as exc:
            self._write_summary(started_at=started_at, status="FAIL", error=str(exc))
            return 1

    def _step(self, name: str, action) -> None:
        started = datetime.now(UTC)
        try:
            outcome = action()
            if isinstance(outcome, StepOutcome):
                details = outcome.details
                status = outcome.status
            else:
                details = outcome or "ok"
                status = "ok"
        except Exception as exc:
            finished = datetime.now(UTC)
            self.steps.append(
                StepResult(
                    name=name,
                    status="failed",
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
        timeout_sec: int = 15,
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
            with urlopen(request, timeout=timeout_sec) as response:
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

    def _wait_import_job_completed(self, *, job_id: str, headers: dict[str, str]) -> str:
        deadline = time.time() + IMPORT_JOB_TIMEOUT_SEC
        last_status = "unknown"
        while time.time() < deadline:
            payload, _ = self._request_json(
                method="GET",
                url=f"http://localhost:8061/api/v1/import/jobs/{job_id}",
                headers=headers,
            )
            self._require_envelope_ok(payload, endpoint=f"/import/jobs/{job_id}")
            job_data = payload.get("data", {})
            status = job_data.get("status")
            if isinstance(status, str):
                last_status = status
            if status in IMPORT_JOB_TERMINAL_STATUSES:
                if status == "failed":
                    raise RuntimeError(f"/import/jobs/{job_id}: demo import failed")
                return status
            time.sleep(IMPORT_JOB_POLL_INTERVAL_SEC)
        raise RuntimeError(
            f"Timeout waiting for /import/jobs/{job_id}; last_status={last_status}"
        )

    def _check_core_api_flow(self) -> str:
        token = self._api_login(email="admin@fuelsight.local", password="admin12345")
        auth_headers = {"authorization": f"Bearer {token}"}

        demo_start_date, demo_end_date = self._demo_date_window()
        generate_demo_payload, generate_status = self._request_json(
            method="POST",
            url="http://localhost:8061/api/v1/import/generate-demo",
            payload={
                "start_date": demo_start_date,
                "end_date": demo_end_date,
                "products": ["AI_92", "AI_95", "DT_S", "DT_W"],
                "seed": 42,
                "replace_existing": True,
            },
            headers=auth_headers,
            expected_statuses={202},
        )
        self._require_envelope_ok(generate_demo_payload, endpoint="/import/generate-demo")
        job_id = generate_demo_payload.get("data", {}).get("job_id")
        if not isinstance(job_id, str) or not job_id:
            raise RuntimeError("/import/generate-demo: missing job_id")
        generate_demo_job_status = self._wait_import_job_completed(
            job_id=job_id,
            headers=auth_headers,
        )

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
            f"generate_demo_job_status={generate_demo_job_status}, "
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
                "context_scope": ["internal_analytics", "news_digest", "news_raw", "forecast"],
            },
            headers=auth_headers,
            expected_statuses={200},
            timeout_sec=90,
        )
        self._require_envelope_ok(chat_payload, endpoint="/chat/sessions/{id}/messages")
        chat_data = chat_payload.get("data", {})
        citations = chat_data.get("citations")
        selected_count = chat_payload.get("meta", {}).get("retrieval", {}).get("selected_count")
        if chat_status != 200 or chat_data.get("mode") != "retrieval_only":
            raise RuntimeError(
                "/chat/sessions/{id}/messages: expected retrieval_only answer with ENABLE_LLM=false"
            )
        if not isinstance(citations, list) or not citations:
            raise RuntimeError("/chat/sessions/{id}/messages: expected non-empty citations")
        if not isinstance(selected_count, int) or selected_count <= 0:
            raise RuntimeError("/chat/sessions/{id}/messages: expected selected retrieval evidence")

        return "LLM off smoke passed: digest/search/chat alive, chat returns retrieval_only citations"

    def _check_cloud_provider_fallback_api_flow(self) -> str:
        health_payload = self._read_json_url("http://localhost:8061/api/v1/health")
        self._require_envelope_ok(health_payload, endpoint="/health")
        health_data = health_payload.get("data", {})
        llm_active = health_data.get("llm_active") if isinstance(health_data, dict) else None
        if not isinstance(llm_active, dict) or llm_active.get("mode") != "cloud_llm":
            if self.profile == "cloud-enhanced":
                reason = None
                if isinstance(llm_active, dict):
                    reason = llm_active.get("degradation_reason")
                raise RuntimeError(
                    "cloud provider fallback smoke failed: "
                    f"cloud LLM is not active ({reason or 'unknown_reason'})"
                )
            return "cloud provider fallback smoke skipped: cloud LLM is not active"

        token = self._api_login(email="analyst@fuelsight.local", password="analyst12345")
        auth_headers = {"authorization": f"Bearer {token}"}
        session_payload, _ = self._request_json(
            method="POST",
            url="http://localhost:8061/api/v1/chat/sessions",
            payload={"title": "Cloud fallback smoke"},
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
                "question": "Почему изменилась маржа AI_95?",
                "context_scope": ["internal_analytics", "news_digest", "news_raw", "forecast"],
            },
            headers=auth_headers,
            expected_statuses={200},
            timeout_sec=90,
        )
        self._require_envelope_ok(chat_payload, endpoint="/chat/sessions/{id}/messages")
        chat_data = chat_payload.get("data", {})
        chat_meta = chat_payload.get("meta", {})
        llm_provider = chat_meta.get("llm_provider") if isinstance(chat_meta, dict) else None
        verification = chat_data.get("verification") if isinstance(chat_data, dict) else None
        citations = chat_data.get("citations") if isinstance(chat_data, dict) else None
        if chat_status != 200:
            raise RuntimeError("/chat/sessions/{id}/messages: expected 200 response")

        if isinstance(llm_provider, dict) and llm_provider.get("degradation_reason"):
            if chat_data.get("mode") != "retrieval_only":
                raise RuntimeError("cloud fallback smoke: degraded provider must return retrieval_only")
            if not isinstance(citations, list) or not citations:
                raise RuntimeError("cloud fallback smoke: degraded provider answer must include citations")
            if not isinstance(verification, dict) or verification.get("status") != "fallback_verified":
                raise RuntimeError("cloud fallback smoke: expected fallback_verified verification status")
            return (
                "cloud provider fallback smoke passed: "
                f"provider={llm_provider.get('provider')}, "
                f"degradation_reason={llm_provider.get('degradation_reason')}"
            )

        if chat_data.get("mode") != "cloud_llm":
            raise RuntimeError("cloud provider fallback smoke: expected cloud_llm or controlled fallback")
        return "cloud provider fallback smoke passed: cloud provider answered without degradation"

    def _refresh_news(self) -> str:
        output = self._run_news_refresh_command()
        payload = self._extract_last_json_payload(output)
        result = payload.get("result", payload)
        if not isinstance(result, dict):
            raise RuntimeError("news refresh returned an invalid payload")
        manifest_path = result.get("manifest_path")
        coverage_ratio = result.get("coverage_ratio")
        written_news_count = result.get("written_news_count")
        created_digests = result.get("created_digests")
        provider_mode = result.get("provider_mode")
        if not isinstance(manifest_path, str) or not manifest_path:
            raise RuntimeError("news refresh payload does not contain manifest_path")
        if not isinstance(written_news_count, int):
            raise RuntimeError("news refresh payload has invalid written_news_count")
        if not isinstance(created_digests, int):
            raise RuntimeError("news refresh payload has invalid created_digests")
        if created_digests <= 0 and written_news_count > 0:
            output = self._run_news_refresh_command()
            payload = self._extract_last_json_payload(output)
            result = payload.get("result", payload)
            manifest_path = result.get("manifest_path")
            coverage_ratio = result.get("coverage_ratio")
            written_news_count = result.get("written_news_count")
            created_digests = result.get("created_digests")
            provider_mode = result.get("provider_mode")
        if not isinstance(created_digests, int) or created_digests <= 0:
            raise RuntimeError("news refresh payload has invalid created_digests")
        if not isinstance(coverage_ratio, (int, float)):
            raise RuntimeError("news refresh payload has invalid coverage_ratio")
        self._run_command(self.compose_cmd + ["exec", "-T", "backend", "test", "-f", manifest_path])
        return (
            "news refresh passed: "
            f"manifest={manifest_path}, written_news_count={written_news_count}, "
            f"created_digests={created_digests}, provider_mode={provider_mode}, "
            f"coverage_ratio={coverage_ratio:.4f}"
        )

    def _run_news_refresh_command(self) -> str:
        provider = "manual_snapshot" if self.profile == "offline-safe" else "auto"
        lookback_days = "30" if self.profile == "offline-safe" else "14"
        return self._run_command(
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
                "refresh-news-daily",
                "--provider",
                provider,
                "--lookback-days",
                lookback_days,
            ]
        )

    def _refresh_rag_index(self) -> str:
        output = self._run_command(
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
                "refresh-rag-index-daily",
            ]
        )
        payload = self._extract_last_json_payload(output)
        result = payload.get("result", payload)
        manifest_path = result.get("manifest_path")
        written_chunks = result.get("written_chunks")
        if not isinstance(manifest_path, str) or not manifest_path:
            raise RuntimeError("rag index refresh payload does not contain manifest_path")
        if not isinstance(written_chunks, int) or written_chunks <= 0:
            raise RuntimeError("rag index refresh payload has invalid written_chunks")
        self._run_command(self.compose_cmd + ["exec", "-T", "backend", "test", "-f", manifest_path])
        return f"rag index refresh passed: manifest={manifest_path}, written_chunks={written_chunks}"

    def _refresh_external_indicators(self) -> str:
        provider = "manual_snapshot" if self.profile == "offline-safe" else "auto"
        output = self._run_command(
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
                "--provider",
                provider,
            ]
        )
        payload = self._extract_last_json_payload(output)
        result = payload.get("result", payload)
        if not isinstance(result, dict):
            raise RuntimeError("external indicators refresh returned an invalid payload")

        manifest_path = result.get("manifest_path")
        expected_points = result.get("expected_points")
        written_points = result.get("written_points")
        fallback_ratio = result.get("fallback_ratio")
        coverage_ratio = result.get("coverage_ratio")
        if not isinstance(manifest_path, str) or not manifest_path:
            raise RuntimeError("external indicators refresh payload does not contain manifest_path")
        if not isinstance(expected_points, int) or expected_points <= 0:
            raise RuntimeError("external indicators refresh payload has invalid expected_points")
        if not isinstance(written_points, int) or written_points <= 0:
            raise RuntimeError("external indicators refresh payload has invalid written_points")
        if not isinstance(fallback_ratio, (int, float)):
            raise RuntimeError("external indicators refresh payload has invalid fallback_ratio")
        if not isinstance(coverage_ratio, (int, float)):
            raise RuntimeError("external indicators refresh payload has invalid coverage_ratio")

        self._run_command(
            self.compose_cmd + ["exec", "-T", "backend", "test", "-f", manifest_path]
        )
        return (
            "external indicators refresh passed: "
            f"manifest={manifest_path}, coverage_ratio={coverage_ratio:.4f}, "
            f"fallback_ratio={fallback_ratio:.4f}"
        )

    def _build_feature_store_refresh(self) -> str:
        output = self._run_command(
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
        )
        payload = self._extract_last_json_payload(output)
        result = payload.get("result", payload)
        manifest_path = result.get("manifest_path")
        coverage_ratio = result.get("coverage_ratio")
        fallback_ratio = result.get("fallback_ratio")
        provider_mode_counts = result.get("provider_mode_counts")
        if not isinstance(manifest_path, str) or not manifest_path:
            raise RuntimeError("feature store refresh payload does not contain manifest_path")
        if not isinstance(coverage_ratio, (int, float)):
            raise RuntimeError("feature store refresh payload has invalid coverage_ratio")
        if not isinstance(fallback_ratio, (int, float)):
            raise RuntimeError("feature store refresh payload has invalid fallback_ratio")
        if not isinstance(provider_mode_counts, dict):
            raise RuntimeError("feature store refresh payload has invalid provider_mode_counts")
        self._run_command(
            self.compose_cmd + ["exec", "-T", "backend", "test", "-f", manifest_path]
        )
        return (
            "feature store refresh passed: "
            f"manifest={manifest_path}, coverage_ratio={coverage_ratio:.4f}, "
            f"fallback_ratio={fallback_ratio:.4f}"
        )

    def _train_models_weekly(self) -> str:
        output = self._run_command(
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
        )
        payload = self._extract_last_json_payload(output)
        result = payload.get("result", payload)
        train_manifest_path = result.get("train_backtest_manifest_path")
        freshness_manifest_path = result.get("model_freshness_manifest_path")
        feature_status = result.get("feature_refresh_status")
        if not isinstance(train_manifest_path, str) or not train_manifest_path:
            raise RuntimeError("train models payload does not contain train_backtest_manifest_path")
        if not isinstance(freshness_manifest_path, str) or not freshness_manifest_path:
            raise RuntimeError("train models payload does not contain model_freshness_manifest_path")
        if feature_status not in {"fresh", "warning", "degraded"}:
            raise RuntimeError("train models payload has invalid feature_refresh_status")
        self._run_command(
            self.compose_cmd + ["exec", "-T", "backend", "test", "-f", train_manifest_path]
        )
        self._run_command(
            self.compose_cmd + ["exec", "-T", "backend", "test", "-f", freshness_manifest_path]
        )
        return (
            "weekly train/backtest passed: "
            f"status={result.get('status')}, feature_refresh_status={feature_status}, "
            f"train_manifest={train_manifest_path}"
        )

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

    def _run_frontend_mobile_e2e(self) -> str:
        corepack_bin = shutil.which("corepack") or shutil.which("corepack.cmd")
        pnpm_bin = shutil.which("pnpm") or shutil.which("pnpm.cmd")
        if corepack_bin:
            command = [corepack_bin, "pnpm", "--filter", "frontend", "test:e2e:mobile"]
        elif pnpm_bin:
            command = [pnpm_bin, "--filter", "frontend", "test:e2e:mobile"]
        else:
            raise RuntimeError(
                "Neither corepack nor pnpm is available in PATH for frontend_e2e_mobile_smoke"
            )

        output = self._run_command(command)
        return output or "frontend playwright mobile smoke passed"

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
            "refresh_news_daily",
            "build_defense_report",
        }
        missing = sorted(expected - dag_ids)
        if missing:
            raise RuntimeError(f"Missing DAG ids: {', '.join(missing)}")
        return "all Phase 9 DAG ids are registered"

    def _build_defense_report(self) -> StepOutcome:
        output = self._run_command(
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
                "build-defense-report",
                "--profile",
                self.profile,
            ]
        )
        payload = self._extract_last_json_payload(output)
        result = payload.get("result", payload)
        if not isinstance(result, dict):
            raise RuntimeError("defense report returned an invalid payload")
        artifacts = result.get("artifacts")
        if not isinstance(artifacts, dict) or not artifacts.get("json") or not artifacts.get("pdf"):
            raise RuntimeError("defense report did not return json/pdf artifacts")
        for artifact_path in (artifacts["json"], artifacts["pdf"]):
            self._run_command(self.compose_cmd + ["exec", "-T", "backend", "test", "-f", artifact_path])
        DEFENSE_RESULT_PATH.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        status = str(result.get("overall_status") or "warning")
        return StepOutcome(
            status=status if status in {"ok", "warning", "degraded", "failed"} else "warning",
            details=(
                "defense report built: "
                f"overall_status={result.get('overall_status')}, "
                f"json={artifacts['json']}, pdf={artifacts['pdf']}"
            ),
        )

    @staticmethod
    def _run_command(args: list[str]) -> str:
        process = subprocess.run(
            args,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if process.returncode != 0:
            stderr = (process.stderr or "").strip()
            stdout = (process.stdout or "").strip()
            message = stderr or stdout or f"command failed with code {process.returncode}"
            raise RuntimeError(f"{args}: {message}")
        return (process.stdout or "").strip() or "ok"

    @staticmethod
    def _extract_last_json_payload(output: str) -> dict:
        for line in reversed(output.splitlines()):
            candidate = line.strip()
            if not candidate.startswith("{"):
                continue
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        raise RuntimeError(f"Failed to parse JSON payload from command output: {output}")

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
            "profile": self.profile,
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
    parser.add_argument(
        "--profile",
        choices=sorted(DEMO_PROFILES),
        default="offline-safe",
        help="Defense demo profile to apply to compose and pipeline provider modes",
    )
    parser.add_argument("--without-airflow", action="store_true", help="Run only core stack")
    parser.add_argument("--no-build", action="store_true", help="Skip image rebuild")
    parser.add_argument("--with-e2e", action="store_true", help="Run Playwright E2E happy-path after smoke")
    parser.add_argument(
        "--with-mobile-e2e",
        action="store_true",
        help="Run Playwright mobile smoke (iPhone 13 + Pixel 7) after smoke",
    )
    args = parser.parse_args()

    runner = DemoRunner(
        with_airflow=not args.without_airflow,
        rebuild=not args.no_build,
        with_e2e=args.with_e2e,
        with_mobile_e2e=args.with_mobile_e2e,
        profile=args.profile,
    )
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
