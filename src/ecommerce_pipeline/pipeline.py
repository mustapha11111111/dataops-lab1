"""Enchaîne génération, contrôle, chargement brut, dbt, puis le bilan de santé."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path
from time import perf_counter

import pandas as pd

from ecommerce_pipeline.config import project_root
from ecommerce_pipeline.dbt_runner import run_dbt, run_freshness
from ecommerce_pipeline.frankfurter import FrankfurterError, assemble_rates
from ecommerce_pipeline.health import alert_level, deliver_alert, read_metrics, record_run
from ecommerce_pipeline.orders import generate_orders
from ecommerce_pipeline.quality import (
    DataQualityError,
    orders_without_rate,
    validate_orders,
    validate_rates,
)
from ecommerce_pipeline.warehouse import connect, replace_orders, replace_rates


def run_pipeline(
    *,
    start: date,
    end: date,
    per_day: int = 20,
    seed: int = 42,
    offline: bool = False,
    api_url: str = "https://api.frankfurter.dev/v2/rates",
    timeout: int = 30,
    duckdb_path: Path | None = None,
    root: Path | None = None,
    alert_dir: Path | None = None,
    webhook_url: str = "",
    build_dbt: bool = True,
) -> dict:
    root = root or project_root()
    duckdb_path = Path(duckdb_path or root / "data" / "warehouse.duckdb")
    alert_dir = Path(alert_dir or duckdb_path.parent / "alerts")
    started = datetime.now().replace(microsecond=0)
    timer = perf_counter()
    run_id = uuid.uuid4().hex[:12]
    orders_read = 0
    message = "Pipeline interrompu avant le bilan."
    status = "failed"

    try:
        print(f"Génération des commandes synthétiques du {start} au {end}.")
        orders = generate_orders(start, end, per_day, seed)
        orders = validate_orders(orders)
        orders_read = len(orders)
        print(f"Commandes prêtes : {orders_read}. Origine : synthétique.")

        print("Récupération des taux EUR, USD, TND et MAD.")
        rates = assemble_rates(
            start,
            end,
            offline=offline,
            api_url=api_url,
            timeout=timeout,
        )
        source_column = rates["_source"].copy() if "_source" in rates.columns else None
        rates = validate_rates(rates)
        if source_column is not None:
            rates["_source"] = source_column.values
        print(f"Taux prêts : {len(rates)}.")

        raw_dir = duckdb_path.parent / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        orders.to_csv(raw_dir / "orders.csv", index=False)
        rates.to_csv(raw_dir / "exchange_rates.csv", index=False)

        batch_id = started.strftime("%Y%m%dT%H%M%S")
        connection = connect(duckdb_path)
        try:
            replace_orders(connection, orders, batch_id)
            replace_rates(connection, rates, batch_id)
        finally:
            connection.close()

        gaps = orders_without_rate(orders, rates)
        if gaps:
            preview = ", ".join(gaps[:5])
            raise FrankfurterError(
                "Aucun taux antérieur pour "
                f"{preview}. Le brut est conservé, les marts ne sont pas publiés."
            )

        if build_dbt:
            print("Transformation et tests dbt.")
            run_dbt(root, duckdb_path)
            print("Contrôle de fraîcheur des sources.")
            run_freshness(root, duckdb_path)
        status = "success"
        message = "Pipeline terminé. Les marts sont publiés."
    except (
        DataQualityError,
        FrankfurterError,
        RuntimeError,
        ValueError,
        pd.errors.ParserError,
    ) as exc:
        status = "failed"
        message = str(exc)
        print(message)

    metrics = read_metrics(duckdb_path)
    anomalies = int(metrics.get("anomalies") or 0)
    if status == "success" and anomalies:
        message = f"{anomalies} anomalie(s) de ventes à vérifier. Les marts restent publiés."
    level = alert_level(status, anomalies)
    payload = {
        "run_id": run_id,
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": datetime.now().replace(microsecond=0).isoformat(timespec="seconds"),
        "status": status,
        "alert_level": level,
        "marts_published": status == "success",
        "offline": offline,
        "orders_read": orders_read,
        "orders_in_raw": metrics.get("orders_in_raw"),
        "rates_in_raw": metrics.get("rates_in_raw"),
        "orders_rejected": metrics.get("orders_rejected"),
        "orders_published": metrics.get("orders_published"),
        "anomalies": anomalies,
        "max_order_date": metrics.get("max_order_date"),
        "max_rate_date": metrics.get("max_rate_date"),
        "duration_seconds": round(perf_counter() - timer, 2),
        "message": message,
    }
    channel = deliver_alert(payload, webhook_url, alert_dir)
    payload["alert_channel"] = channel
    record_run(duckdb_path, payload)
    print(f"Statut : {status}. Alerte : {level} ({channel}).")
    return payload
