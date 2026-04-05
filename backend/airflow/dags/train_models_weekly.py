from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pendulum
from _runner import run_pipeline_command
from airflow.decorators import dag, task

MOSCOW_TZ = pendulum.timezone("Europe/Moscow")
DEFAULT_ARGS = {
    "owner": "fuelsight",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


@dag(
    dag_id="train_models_weekly",
    schedule="0 3 * * 1",
    start_date=pendulum.datetime(2026, 1, 1, tz=MOSCOW_TZ),
    catchup=False,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    is_paused_upon_creation=True,
    tags=["fuelsight", "phase7", "ml"],
)
def train_models_weekly_dag():
    @task(execution_timeout=timedelta(minutes=5))
    def heartbeat() -> dict[str, str]:
        return {
            "dag_id": "train_models_weekly",
            "generated_at": datetime.now(UTC).isoformat(),
            "status": "started",
        }

    @task(execution_timeout=timedelta(minutes=90))
    def train_models(_: dict[str, str]) -> dict:
        return run_pipeline_command("train-models-weekly", "--window-type", "rolling")

    train_models(heartbeat())


dag_instance = train_models_weekly_dag()
