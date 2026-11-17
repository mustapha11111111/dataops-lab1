"""Contrôles de forme à l'entrée. Les règles métier sont appliquées ensuite dans dbt."""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd
import pandera.pandas as pa
from pandera.errors import SchemaError

from ecommerce_pipeline.frankfurter import RATE_COLUMNS
from ecommerce_pipeline.orders import ORDER_COLUMNS

ACCEPTED_CURRENCIES = ["EUR", "USD", "TND", "MAD"]


class DataQualityError(Exception):
    """Le lot reçu ne respecte pas le contrat de colonnes."""


def _string_frame(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise DataQualityError(f"Colonnes manquantes : {missing}")
    framed = df.loc[:, columns].copy()
    for column in columns:
        framed[column] = framed[column].map(lambda value: "" if pd.isna(value) else str(value))
    if framed.empty:
        raise DataQualityError("Le lot ne contient aucune ligne.")
    return framed


ORDERS_SCHEMA = pa.DataFrameSchema(
    {
        "order_id": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False),
        "order_date": pa.Column(str, nullable=False),
        "customer_id": pa.Column(str, nullable=True),
        "country": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False),
        "product": pa.Column(str, pa.Check.str_length(min_value=1), nullable=False),
        "quantity": pa.Column(str, nullable=False),
        "unit_price": pa.Column(str, nullable=False),
        "currency": pa.Column(str, pa.Check.str_length(min_value=3, max_value=3), nullable=False),
        "data_origin": pa.Column(str, pa.Check.isin(["synthetique"]), nullable=False),
    },
    strict=True,
    coerce=True,
)

RATES_SCHEMA = pa.DataFrameSchema(
    {
        "rate_date": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$"), nullable=False),
        "base_currency": pa.Column(str, pa.Check.isin(["EUR"]), nullable=False),
        "quote_currency": pa.Column(str, pa.Check.isin(ACCEPTED_CURRENCIES), nullable=False),
        "rate": pa.Column(str, pa.Check.str_matches(r"^\d+(\.\d+)?$"), nullable=False),
    },
    strict=True,
    coerce=True,
)


def _validate(df: pd.DataFrame, schema: pa.DataFrameSchema, label: str) -> pd.DataFrame:
    try:
        return schema.validate(df, lazy=False)
    except SchemaError as exc:
        raise DataQualityError(f"Contrat {label} refusé : {exc}") from exc


def validate_orders(df: pd.DataFrame) -> pd.DataFrame:
    return _validate(_string_frame(df, ORDER_COLUMNS), ORDERS_SCHEMA, "commandes")


def validate_rates(df: pd.DataFrame) -> pd.DataFrame:
    checked = _validate(_string_frame(df, RATE_COLUMNS), RATES_SCHEMA, "taux")
    if "_source" in df.columns:
        checked = checked.copy()
        checked["_source"] = df["_source"].astype(str).values
    return checked


def orders_without_rate(orders: pd.DataFrame, rates: pd.DataFrame) -> list[str]:
    """Repère les commandes étrangères valides qui n'ont aucun taux à leur date ou avant."""
    known: dict[str, list[date]] = {}
    for row in rates.itertuples(index=False):
        known.setdefault(row.quote_currency, []).append(date.fromisoformat(row.rate_date))

    problems: list[str] = []
    for row in orders.itertuples(index=False):
        currency = row.currency
        if currency not in {"USD", "TND", "MAD"}:
            continue
        try:
            order_day = date.fromisoformat(row.order_date)
            quantity = int(row.quantity)
            price = Decimal(row.unit_price)
        except (ValueError, InvalidOperation):
            continue
        if quantity <= 0 or price <= 0:
            continue
        earlier = known.get(currency, [])
        if not any(rate_day <= order_day for rate_day in earlier):
            problems.append(f"{row.order_id} {currency} {row.order_date}")
    return problems
