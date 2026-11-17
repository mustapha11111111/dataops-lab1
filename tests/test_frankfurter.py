import json
import os
from datetime import date

import pytest
import requests

from ecommerce_pipeline.frankfurter import FrankfurterError, fetch_rates, load_fixture, parse_rates


def test_fixture_contains_tnd_and_mad():
    rows = load_fixture()
    quotes = {row["quote_currency"] for row in rows}
    assert {"USD", "TND", "MAD"} <= quotes
    assert all(row["base_currency"] == "EUR" for row in rows)


def test_empty_payload_is_an_error():
    with pytest.raises(FrankfurterError):
        parse_rates([])


def test_http_error_is_not_silent(monkeypatch):
    class Response:
        status_code = 503
        text = "indisponible"

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: Response())
    with pytest.raises(FrankfurterError, match="503"):
        fetch_rates(
            date(2026, 10, 1),
            date(2026, 10, 2),
            api_url="https://api.frankfurter.dev/v2/rates",
            retries=0,
        )


def test_invalid_json_is_not_silent(monkeypatch):
    class Response:
        status_code = 200
        text = "pas du json"

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: Response())
    with pytest.raises(FrankfurterError, match="illisible"):
        fetch_rates(
            date(2026, 10, 1),
            date(2026, 10, 2),
            api_url="https://api.frankfurter.dev/v2/rates",
            retries=0,
        )


@pytest.mark.skipif(os.environ.get("RUN_NETWORK") != "1", reason="appel API réel, hors CI")
def test_live_api_returns_tnd_and_mad():
    rows = fetch_rates(
        date(2026, 10, 1),
        date(2026, 10, 2),
        api_url="https://api.frankfurter.dev/v2/rates",
        retries=1,
    )
    quotes = {row["quote_currency"] for row in rows}
    assert {"USD", "TND", "MAD"} <= quotes
    json.dumps(rows)
