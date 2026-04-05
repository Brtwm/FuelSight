from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pendulum
from _runner import run_pipeline_command
from airflow.decorators import dag, task

MOSCOW_TZ = pendulum.timezone("Europe/Moscow")
DEFAULT_ARGS = {
    "owner": "fuelsight",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="build_feature_store_daily",
    schedule="0 2 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz=MOSCOW_TZ),
    catchup=False,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    is_paused_upon_creation=True,
    tags=["fuelsight", "phase7", "features"],
)
def build_feature_store_daily_dag():
    @task(execution_timeout=timedelta(minutes=5))
    def heartbeat() -> dict[str, str]:
        return {
            "dag_id": "build_feature_store_daily",
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "started",
        }

    @task(execution_timeout=timedelta(minutes=30))
    def build_store(_: dict[str, str]) -> dict:
        return run_pipeline_command("build-feature-store-daily")

    build_store(heartbeat())


dag_instance = build_feature_store_daily_dag()
