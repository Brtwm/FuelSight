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
    dag_id="ingest_internal_sales_daily",
    schedule="15 1 * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz=MOSCOW_TZ),
    catchup=False,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    is_paused_upon_creation=True,
    tags=["fuelsight", "phase7", "ingest"],
)
def ingest_internal_sales_daily_dag():
    @task(execution_timeout=timedelta(minutes=5))
    def heartbeat() -> dict[str, str]:
        return {
            "dag_id": "ingest_internal_sales_daily",
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "started",
        }

    @task(execution_timeout=timedelta(minutes=20))
    def ingest_files(_: dict[str, str]) -> dict:
        return run_pipeline_command("ingest-sales-daily")

    ingest_files(heartbeat())


dag_instance = ingest_internal_sales_daily_dag()
