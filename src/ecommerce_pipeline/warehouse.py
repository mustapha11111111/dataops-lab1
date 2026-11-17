"""Chargement brut dans DuckDB. Une deuxième exécution remplace les mêmes clés."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def connect(path: Path) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(path))
    connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
    connection.execute("CREATE SCHEMA IF NOT EXISTS ops")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.orders (
            order_id VARCHAR,
            order_date VARCHAR,
            customer_id VARCHAR,
            country VARCHAR,
            product VARCHAR,
            quantity VARCHAR,
            unit_price VARCHAR,
            currency VARCHAR,
            data_origin VARCHAR,
            _loaded_at TIMESTAMP,
            _source VARCHAR,
            _batch_id VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.exchange_rates (
            rate_date VARCHAR,
            base_currency VARCHAR,
            quote_currency VARCHAR,
            rate VARCHAR,
            _loaded_at TIMESTAMP,
            _source VARCHAR,
            _batch_id VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS ops.pipeline_runs (
            run_id VARCHAR,
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            status VARCHAR,
            alert_level VARCHAR,
            offline BOOLEAN,
            orders_read INTEGER,
            orders_in_raw INTEGER,
            rates_in_raw INTEGER,
            orders_rejected INTEGER,
            orders_published INTEGER,
            anomalies INTEGER,
            max_order_date VARCHAR,
            max_rate_date VARCHAR,
            duration_seconds DOUBLE,
            message VARCHAR
        )
        """
    )
    return connection


def _insert(
    connection: duckdb.DuckDBPyConnection,
    table: str,
    frame: pd.DataFrame,
    columns: list[str],
) -> None:
    connection.register("incoming_batch", frame)
    try:
        column_list = ", ".join(columns)
        select_list = ", ".join(
            "current_timestamp" if column == "_loaded_at" else column for column in columns
        )
        connection.execute("BEGIN")
        try:
            if table == "raw.orders":
                connection.execute(
                    "DELETE FROM raw.orders WHERE order_id IN (SELECT order_id FROM incoming_batch)"
                )
            else:
                connection.execute(
                    """
                    DELETE FROM raw.exchange_rates
                    WHERE (rate_date, base_currency, quote_currency) IN (
                        SELECT rate_date, base_currency, quote_currency FROM incoming_batch
                    )
                    """
                )
            connection.execute(
                f"INSERT INTO {table} ({column_list}) SELECT {select_list} FROM incoming_batch"
            )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
    finally:
        connection.unregister("incoming_batch")


def replace_orders(
    connection: duckdb.DuckDBPyConnection, orders: pd.DataFrame, batch_id: str
) -> None:
    frame = orders.copy()
    frame["_source"] = "generateur_synthetique"
    frame["_batch_id"] = batch_id
    frame["_loaded_at"] = None
    _insert(
        connection,
        "raw.orders",
        frame,
        [
            "order_id",
            "order_date",
            "customer_id",
            "country",
            "product",
            "quantity",
            "unit_price",
            "currency",
            "data_origin",
            "_loaded_at",
            "_source",
            "_batch_id",
        ],
    )


def replace_rates(
    connection: duckdb.DuckDBPyConnection, rates: pd.DataFrame, batch_id: str
) -> None:
    frame = rates.copy()
    if "_source" not in frame.columns:
        frame["_source"] = "inconnu"
    frame["_batch_id"] = batch_id
    frame["_loaded_at"] = None
    _insert(
        connection,
        "raw.exchange_rates",
        frame,
        [
            "rate_date",
            "base_currency",
            "quote_currency",
            "rate",
            "_loaded_at",
            "_source",
            "_batch_id",
        ],
    )
