"""Flow Prefect quotidien. Le process reste ouvert et réveille le pipeline à 06:00."""

from __future__ import annotations

from datetime import datetime, timedelta
from time import sleep

from prefect import flow, task

from ecommerce_pipeline.pipeline import run_pipeline


@task(name="executer-pipeline", retries=2, retry_delay_seconds=15)
def run_pipeline_task() -> dict:
    """Relance tout le pipeline si une étape technique échoue."""
    from ecommerce_pipeline.config import load_settings

    settings = load_settings()
    result = run_pipeline(
        start=settings.start,
        end=settings.end,
        per_day=settings.per_day,
        seed=settings.seed,
        offline=settings.offline,
        api_url=settings.api_url,
        timeout=settings.timeout_seconds,
        duckdb_path=settings.duckdb_path,
        root=settings.root,
        webhook_url=settings.webhook_url,
    )
    if result["status"] != "success":
        raise RuntimeError(result["message"])
    return result


@flow(name="ventes-quotidiennes")
def daily_sales_flow() -> dict:
    return run_pipeline_task()


def seconds_until_hour(hour: int) -> float:
    now = datetime.now()
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def serve(hour: int = 6) -> None:
    print(f"Orchestration Prefect démarrée. Exécution quotidienne à {hour:02d}:00, heure locale.")
    while True:
        waiting = seconds_until_hour(hour)
        print(f"Prochaine exécution dans {int(waiting)} secondes.")
        sleep(waiting)
        daily_sales_flow()


if __name__ == "__main__":
    serve()
