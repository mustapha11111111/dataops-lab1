
import pandas as pd
import pytest

from pipeline.transform import clean_orders
from pipeline.validate import DataQualityError, check_schema


def sample_orders():
    return pd.DataFrame([
        {
            "order_id": 1,
            "order_date": "2026-10-01",
            "customer_id": "C001",
            "country": "Tunisia",
            "product": "Book",
            "quantity": 2,
            "unit_price": 10.0,
        },
        {
            "order_id": 2,
            "order_date": "2026-10-02",
            "customer_id": "C002",
            "country": "France",
            "product": "Pen",
            "quantity": 3,
            "unit_price": 5.0,
        },
    ])


def test_invalid_quantity_is_rejected():
    orders = sample_orders()
    orders.loc[0, "quantity"] = -1

    clean, rejected = clean_orders(orders)

    assert len(clean) == 1
    assert len(rejected) == 1
    assert rejected.iloc[0]["reject_reason"] == "invalid_quantity"


def test_duplicate_order_is_rejected():
    orders = pd.concat(
        [sample_orders(), sample_orders().iloc[[0]]],
        ignore_index=True,
    )

    clean, rejected = clean_orders(orders)

    assert len(clean) == 2
    assert len(rejected) == 1
    assert rejected.iloc[0]["reject_reason"] == "duplicate_order_id"


def test_country_is_normalised():
    orders = sample_orders()
    orders["country"] = [" france", "FRANCE "]

    clean, rejected = clean_orders(orders)

    assert clean["country"].tolist() == ["France", "France"]
    assert len(rejected) == 0


def test_check_schema_stops_on_missing_column():
    orders = sample_orders().rename(
        columns={"unit_price": "price"}
    )

    with pytest.raises(DataQualityError):
        check_schema(orders)


def test_missing_customer_is_rejected():
    orders = sample_orders()
    orders.loc[0, "customer_id"] = None

    clean, rejected = clean_orders(orders)

    assert len(clean) == 1
    assert rejected.iloc[0]["reject_reason"] == "missing_customer_id"