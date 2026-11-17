"""Suit chaque exécution et écrit une alerte lisible, même sans webhook."""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import duckdb
import requests

from ecommerce_pipeline.warehouse import connect


def alert_level(status: str, anomalies: int) -> str:
    if status != "success":
        return "critical"
    if anomalies > 0:
        return "warning"
    return "ok"


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def deliver_alert(payload: dict, webhook_url: str, alert_dir: Path) -> str:
    """Écrit toujours le fichier. Le webhook est optionnel et son échec reste visible."""
    alert_dir.mkdir(parents=True, exist_ok=True)
    path = alert_dir / "latest_alert.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if not webhook_url:
        return "fichier"
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
    except requests.RequestException as exc:
        payload["webhook_error"] = str(exc)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Alerte non délivrée au webhook : {exc}")
        return "webhook_erreur"
    if response.status_code >= 300:
        payload["webhook_error"] = f"HTTP {response.status_code}"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Alerte refusée par le webhook : HTTP {response.status_code}")
        return "webhook_erreur"
    return "webhook"


def record_run(duckdb_path: Path, payload: dict) -> None:
    if not duckdb_path.exists():
        return
    connection = connect(duckdb_path)
    try:
        connection.execute(
            """
            INSERT INTO ops.pipeline_runs VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            [
                payload.get("run_id"),
                payload.get("started_at"),
                payload.get("finished_at"),
                payload.get("status"),
                payload.get("alert_level"),
                payload.get("offline"),
                payload.get("orders_read"),
                payload.get("orders_in_raw"),
                payload.get("rates_in_raw"),
                payload.get("orders_rejected"),
                payload.get("orders_published"),
                payload.get("anomalies"),
                payload.get("max_order_date"),
                payload.get("max_rate_date"),
                payload.get("duration_seconds"),
                payload.get("message"),
            ],
        )
    finally:
        connection.close()


def read_metrics(duckdb_path: Path) -> dict:
    """Lit les volumes après dbt. Une table absente ne fait pas planter le bilan."""
    metrics = {
        "orders_in_raw": None,
        "rates_in_raw": None,
        "orders_rejected": None,
        "orders_published": None,
        "anomalies": 0,
        "max_order_date": None,
        "max_rate_date": None,
    }
    if not duckdb_path.exists():
        return metrics
    queries = {
        "orders_in_raw": "SELECT count(*) FROM raw.orders",
        "rates_in_raw": "SELECT count(*) FROM raw.exchange_rates",
        "orders_rejected": "SELECT count(*) FROM int_orders_rejected",
        "orders_published": "SELECT count(*) FROM fct_sales",
        "anomalies": (
            "SELECT count(*) FROM mart_sales_anomalies "
            "WHERE anomaly_type IN ('hausse_anormale', 'baisse_anormale')"
        ),
        "max_order_date": "SELECT max(order_date) FROM fct_sales",
        "max_rate_date": "SELECT max(rate_date) FROM stg_exchange_rates",
    }
    connection = duckdb.connect(str(duckdb_path), read_only=True)
    try:
        for key, sql in queries.items():
            try:
                value = connection.execute(sql).fetchone()[0]
            except duckdb.Error:
                value = metrics[key]
            metrics[key] = _json_ready(value)
    finally:
        connection.close()
    if metrics["anomalies"] is None:
        metrics["anomalies"] = 0
    return metrics
