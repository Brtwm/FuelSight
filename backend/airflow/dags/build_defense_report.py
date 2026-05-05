from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pendulum
from _runner import run_pipeline_command
from airflow.decorators import dag, task

MOSCOW_TZ = pendulum.timezone("Europe/Moscow")
DEFAULT_ARGS = {
    "owner": "fuelsight",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="build_defense_report",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz=MOSCOW_TZ),
    catchup=False,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    is_paused_upon_creation=True,
    tags=["fuelsight", "phase-j", "defense"],
)
def build_defense_report_dag():
    @task(execution_timeout=timedelta(minutes=5))
    def heartbeat() -> dict[str, str]:
        return {
            "dag_id": "build_defense_report",
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "started",
        }

    @task(execution_timeout=timedelta(minutes=10))
    def build_report(_: dict[str, str]) -> dict:
        return run_pipeline_command("build-defense-report")

    build_report(heartbeat())


dag_instance = build_defense_report_dag()
