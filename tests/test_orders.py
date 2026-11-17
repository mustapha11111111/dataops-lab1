from datetime import date

import pandas as pd
import pytest

from ecommerce_pipeline.orders import generate_orders, spike_date
from ecommerce_pipeline.quality import DataQualityError, validate_orders


def test_spike_date_prefers_the_latest_planted_day():
    assert spike_date(date(2026, 10, 1), date(2026, 10, 12)) == date(2026, 10, 8)
    assert spike_date(date(2026, 9, 1), date(2026, 11, 16)) == date(2026, 11, 10)
    assert spike_date(date(2026, 1, 1), date(2026, 1, 10)) is None


def test_generator_is_deterministic():
    start, end = date(2026, 10, 1), date(2026, 10, 3)
    first = generate_orders(start, end, per_day=5, seed=42)
    second = generate_orders(start, end, per_day=5, seed=42)
    pd.testing.assert_frame_equal(first, second)


def test_generator_marks_rows_as_synthetic_and_plants_one_duplicate():
    frame = generate_orders(date(2026, 10, 1), date(2026, 10, 2), per_day=5, seed=1)
    assert set(frame["data_origin"]) == {"synthetique"}
    assert frame["order_id"].duplicated().sum() == 1
    assert (frame["quantity"] == "-2").any()
    assert (frame["country"] == "tunisia").any()


def test_missing_column_is_rejected():
    frame = generate_orders(date(2026, 10, 1), date(2026, 10, 1), per_day=2, seed=1)
    broken = frame.drop(columns=["currency"])
    with pytest.raises(DataQualityError):
        validate_orders(broken)
