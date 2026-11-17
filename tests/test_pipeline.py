from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pandas as pd
import yaml

from ecommerce_pipeline.dbt_runner import run_dbt
from ecommerce_pipeline.pipeline import run_pipeline
from ecommerce_pipeline.warehouse import connect, replace_orders, replace_rates

ROOT = Path(__file__).resolve().parents[1]


def test_contracts_list_the_business_columns():
    orders = yaml.safe_load((ROOT / "contracts" / "orders.yaml").read_text(encoding="utf-8"))
    rates = yaml.safe_load((ROOT / "contracts" / "exchange_rates.yaml").read_text(encoding="utf-8"))
    order_columns = [item["name"] for item in orders["schema"][0]["properties"]]
    rate_columns = [item["name"] for item in rates["schema"][0]["properties"]]
    assert "currency" in order_columns
    assert "data_origin" in order_columns
    assert {"rate_date", "base_currency", "quote_currency", "rate"} <= set(rate_columns)


def _counts(path: Path) -> tuple:
    connection = duckdb.connect(str(path), read_only=True)
    try:
        raw = connection.execute(
            "SELECT count(*), count(DISTINCT order_id) FROM raw.orders"
        ).fetchone()
        rates = connection.execute(
            """
            SELECT count(*), count(DISTINCT rate_date || base_currency || quote_currency)
            FROM raw.exchange_rates
            """
        ).fetchone()
        return raw, rates
    finally:
        connection.close()


def test_second_run_does_not_duplicate_and_flags_tunisia(tmp_path):
    database = tmp_path / "warehouse.duckdb"
    alerts = tmp_path / "alerts"
    kwargs = {
        "start": date(2026, 10, 1),
        "end": date(2026, 10, 12),
        "per_day": 5,
        "seed": 42,
        "offline": True,
        "duckdb_path": database,
        "root": ROOT,
        "alert_dir": alerts,
    }
    first = run_pipeline(**kwargs)
    counts_after_first = _counts(database)
    second = run_pipeline(**kwargs)
    counts_after_second = _counts(database)

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert counts_after_first == counts_after_second
    raw_rows, raw_ids = counts_after_second[0]
    assert raw_rows == raw_ids + 1

    connection = duckdb.connect(str(database), read_only=True)
    try:
        anomaly = connection.execute(
            """
            SELECT anomaly_type
            FROM mart_sales_anomalies
            WHERE country = 'Tunisia' AND order_date = DATE '2026-10-08'
            """
        ).fetchone()[0]
        rejected = connection.execute(
            """
            SELECT order_id FROM int_orders_rejected
            WHERE rejection_reason = 'quantite_invalide'
            """
        ).fetchone()[0]
        still_published = connection.execute(
            "SELECT count(*) FROM fct_sales WHERE order_id = ?",
            [rejected],
        ).fetchone()[0]
    finally:
        connection.close()

    assert anomaly == "hausse_anormale"
    assert still_published == 0
    alert = json_alert(alerts)
    assert alert["alert_level"] == "warning"
    assert alert["marts_published"] is True


def json_alert(alerts: Path) -> dict:
    import json

    return json.loads((alerts / "latest_alert.json").read_text(encoding="utf-8"))


def test_weekend_order_uses_the_previous_rate(tmp_path):
    database = tmp_path / "fx.duckdb"
    orders = pd.DataFrame(
        [
            {
                "order_id": "TND-SUN",
                "order_date": "2026-10-04",
                "customer_id": "C010",
                "country": "Tunisia",
                "product": "Mouse",
                "quantity": "2",
                "unit_price": "10.00",
                "currency": "TND",
                "data_origin": "synthetique",
            },
            {
                "order_id": "EUR-MON",
                "order_date": "2026-10-05",
                "customer_id": "C011",
                "country": "France",
                "product": "Mouse",
                "quantity": "1",
                "unit_price": "50.00",
                "currency": "EUR",
                "data_origin": "synthetique",
            },
        ]
    )
    rates = pd.DataFrame(
        [
            {
                "rate_date": "2026-10-02",
                "base_currency": "EUR",
                "quote_currency": "TND",
                "rate": "3.319700",
                "_source": "test",
            },
            {
                "rate_date": "2026-10-05",
                "base_currency": "EUR",
                "quote_currency": "TND",
                "rate": "4.000000",
                "_source": "test",
            },
            {
                "rate_date": "2026-10-04",
                "base_currency": "EUR",
                "quote_currency": "EUR",
                "rate": "1.000000",
                "_source": "interne_identite_eur",
            },
            {
                "rate_date": "2026-10-05",
                "base_currency": "EUR",
                "quote_currency": "EUR",
                "rate": "1.000000",
                "_source": "interne_identite_eur",
            },
        ]
    )
    connection = connect(database)
    try:
        replace_orders(connection, orders, "test")
        replace_rates(connection, rates, "test")
    finally:
        connection.close()

    run_dbt(ROOT, database)
    connection = duckdb.connect(str(database), read_only=True)
    try:
        tnd = connection.execute(
            """
            SELECT amount_eur, fx_rate_date, fx_method
            FROM fct_sales WHERE order_id = 'TND-SUN'
            """
        ).fetchone()
        eur = connection.execute(
            "SELECT amount_eur, fx_method FROM fct_sales WHERE order_id = 'EUR-MON'"
        ).fetchone()
    finally:
        connection.close()

    assert tnd[1] == date(2026, 10, 2)
    assert tnd[2] == "taux_anterieur_le_plus_recent"
    assert Decimal(str(tnd[0])) == Decimal("6.02")
    assert Decimal(str(eur[0])) == Decimal("50.00")
    assert eur[1] == "identite_eur"
