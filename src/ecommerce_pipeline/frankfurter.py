"""Client de l'API Frankfurter v2 et lecture du fichier de secours."""

from __future__ import annotations

import json
import time
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
import requests

from ecommerce_pipeline.config import QUOTES, project_root

RATE_COLUMNS = ["rate_date", "base_currency", "quote_currency", "rate"]
FOREIGN_QUOTES = {"USD", "TND", "MAD"}


class FrankfurterError(Exception):
    """L'API n'a pas fourni de taux utilisable. L'appelant ne doit pas continuer en silence."""


def parse_rates(payload: object) -> list[dict[str, str]]:
    """Transforme la liste JSON Frankfurter en lignes texte, sans float binaire."""
    if not isinstance(payload, list) or not payload:
        raise FrankfurterError("La réponse Frankfurter est vide ou n'est pas une liste de taux.")
    rows: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise FrankfurterError(f"Taux illisible : {item}")
        try:
            rate = item["rate"]
            if not isinstance(rate, Decimal):
                rate = Decimal(str(rate))
            rows.append(
                {
                    "rate_date": str(item["date"]),
                    "base_currency": str(item["base"]).upper(),
                    "quote_currency": str(item["quote"]).upper(),
                    "rate": f"{rate.quantize(Decimal('0.000001')):.6f}",
                }
            )
        except (KeyError, InvalidOperation, TypeError) as exc:
            raise FrankfurterError(f"Taux illisible : {item}") from exc
    return rows


def fetch_rates(
    start: date,
    end: date,
    *,
    api_url: str,
    quotes: tuple[str, ...] = QUOTES,
    timeout: int = 30,
    retries: int = 2,
) -> list[dict[str, str]]:
    """Appelle Frankfurter. HTTP, délai dépassé ou liste vide : on lève une exception."""
    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "base": "EUR",
        "quotes": ",".join(quotes),
    }
    headers = {"Accept": "application/json", "User-Agent": "dataops-ecommerce-student/1.0"}
    last_error: Exception | None = None
    attempts = retries + 1
    for attempt in range(attempts):
        try:
            response = requests.get(api_url, params=params, headers=headers, timeout=timeout)
        except requests.RequestException as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt + 1)
                continue
            break
        if response.status_code >= 500 or response.status_code == 429:
            last_error = FrankfurterError(
                f"Frankfurter HTTP {response.status_code} : {response.text[:300]}"
            )
            if attempt < retries:
                time.sleep(attempt + 1)
                continue
            break
        if response.status_code != 200:
            raise FrankfurterError(
                f"Frankfurter HTTP {response.status_code} : {response.text[:300]}"
            )
        try:
            payload = json.loads(response.text, parse_float=Decimal)
        except json.JSONDecodeError as exc:
            raise FrankfurterError("Réponse Frankfurter illisible.") from exc
        return parse_rates(payload)
    raise FrankfurterError(
        f"Frankfurter injoignable après {attempts} essai(s) : {last_error}"
    ) from last_error


def load_fixture(path: Path | None = None) -> list[dict[str, str]]:
    fixture = path or project_root() / "tests" / "fixtures" / "frankfurter_oct2026.json"
    if not fixture.exists():
        raise FrankfurterError(f"Fichier de taux introuvable : {fixture}")
    payload = json.loads(fixture.read_text(encoding="utf-8"), parse_float=Decimal)
    return parse_rates(payload)


def _days(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def assemble_rates(
    start: date,
    end: date,
    *,
    offline: bool,
    api_url: str,
    timeout: int = 30,
    retries: int = 2,
    fixture_path: Path | None = None,
) -> pd.DataFrame:
    """Taux étrangers sur la période, plus un taux 1.0 pour chaque jour en EUR.

    On demande aussi les 7 jours d'avant : si un jour n'a pas de taux, la jointure
    dbt prend le dernier taux connu à la date de commande ou avant.
    """
    window_start = start - timedelta(days=7)
    if offline:
        source_rows = load_fixture(fixture_path)
        source_name = "frankfurter_fixture"
    else:
        source_rows = fetch_rates(
            window_start,
            end,
            api_url=api_url,
            timeout=timeout,
            retries=retries,
        )
        source_name = "frankfurter_v2"

    selected: list[dict[str, str]] = []
    for row in source_rows:
        rate_day = date.fromisoformat(row["rate_date"])
        if window_start <= rate_day <= end and row["quote_currency"] in FOREIGN_QUOTES:
            selected.append({**row, "_source": source_name})
    if not selected:
        raise FrankfurterError("Aucun taux USD, TND ou MAD sur la période demandée.")

    for day in _days(start, end):
        selected.append(
            {
                "rate_date": day.isoformat(),
                "base_currency": "EUR",
                "quote_currency": "EUR",
                "rate": "1.000000",
                "_source": "interne_identite_eur",
            }
        )
    frame = pd.DataFrame(selected)
    frame = frame.drop_duplicates(
        ["rate_date", "base_currency", "quote_currency"], keep="last"
    )
    return frame.reset_index(drop=True)
