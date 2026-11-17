"""Générateur déterministe de commandes synthétiques.

Les prix catalogue en devise locale ne sont pas des taux de change.
La conversion financière est faite plus tard avec Frankfurter.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

ORDER_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "country",
    "product",
    "quantity",
    "unit_price",
    "currency",
    "data_origin",
]

DATA_ORIGIN = "synthetique"
SPIKE_CANDIDATES = (date(2026, 11, 10), date(2026, 10, 8))

COUNTRIES = [
    ("France", "EUR"),
    ("Italy", "EUR"),
    ("Tunisia", "TND"),
    ("Morocco", "MAD"),
    ("United States", "USD"),
]

# Prix de base en EUR. Le coefficient donne un prix catalogue local réaliste.
PRODUCTS = [
    ("Mouse", Decimal("19.90")),
    ("Keyboard", Decimal("45.00")),
    ("Headset", Decimal("59.50")),
    ("Webcam", Decimal("39.00")),
    ("Desk lamp", Decimal("29.00")),
    ("Monitor", Decimal("229.00")),
    ("Office chair", Decimal("449.00")),
]

LIST_PRICE_FACTOR = {
    "EUR": Decimal("1.00"),
    "USD": Decimal("1.08"),
    "TND": Decimal("3.30"),
    "MAD": Decimal("10.80"),
}


def spike_date(start: date, end: date) -> date | None:
    """Choisit le jour du pic synthétique s'il tombe dans la période."""
    for candidate in SPIKE_CANDIDATES:
        if start <= candidate <= end:
            return candidate
    return None


def customer_id_for(day: date, index: int) -> str:
    """Trois comportements : deux clients très actifs, des clients du mois, des achats uniques."""
    slot = index % 10
    if slot <= 1:
        return f"C00{slot + 1}"
    if slot <= 5:
        return f"C{slot:02d}{day.month:02d}"
    return f"C{day:%m%d}{index:02d}"


def local_price(base_eur: Decimal, currency: str) -> str:
    amount = (base_eur * LIST_PRICE_FACTOR[currency]).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{amount:.2f}"


def _days(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def generate_orders(start: date, end: date, per_day: int, seed: int) -> pd.DataFrame:
    """Construit un historique stable : le même seed redonne exactement les mêmes lignes."""
    if end < start:
        raise ValueError("La date de fin doit être après la date de début.")
    if not 1 <= per_day <= 500:
        raise ValueError("per_day doit être compris entre 1 et 500.")

    rows: list[dict[str, str]] = []
    planted = spike_date(start, end)
    for day in _days(start, end):
        for index in range(per_day):
            country, currency = COUNTRIES[index % len(COUNTRIES)]
            product, base_eur = PRODUCTS[(index + seed) % len(PRODUCTS)]
            rows.append(
                {
                    "order_id": f"{day:%Y%m%d}{index + 1:03d}",
                    "order_date": day.isoformat(),
                    "customer_id": customer_id_for(day, index),
                    "country": country,
                    "product": product,
                    "quantity": str((index % 3) + 1),
                    "unit_price": local_price(base_eur, currency),
                    "currency": currency,
                    "data_origin": DATA_ORIGIN,
                }
            )
        if day == planted:
            chair_price = local_price(Decimal("449.00"), "TND")
            for extra in range(15):
                rows.append(
                    {
                        "order_id": f"{day:%Y%m%d}{800 + extra:03d}",
                        "order_date": day.isoformat(),
                        "customer_id": "C900",
                        "country": "Tunisia",
                        "product": "Office chair",
                        "quantity": "4",
                        "unit_price": chair_price,
                        "currency": "TND",
                        "data_origin": DATA_ORIGIN,
                    }
                )

    frame = pd.DataFrame(rows, columns=ORDER_COLUMNS)
    tunisia = frame.index[frame["country"] == "Tunisia"]
    if len(tunisia):
        # Exemple volontaire : le staging remettra la casse au propre, le brut est conservé.
        frame.loc[tunisia[0], "country"] = "tunisia"

    frame = _append_known_bad_rows(frame, start)
    return frame.reset_index(drop=True)


def _append_known_bad_rows(frame: pd.DataFrame, start: date) -> pd.DataFrame:
    """Ajoute quelques lignes fausses pour la quarantaine, et un doublon d'order_id."""
    prefix = f"{start:%Y%m%d}"
    bad_rows = [
        {
            "order_id": f"{prefix}901",
            "order_date": start.isoformat(),
            "customer_id": "C901",
            "country": "France",
            "product": "Mouse",
            "quantity": "-2",
            "unit_price": "19.90",
            "currency": "EUR",
            "data_origin": DATA_ORIGIN,
        },
        {
            "order_id": f"{prefix}902",
            "order_date": start.isoformat(),
            "customer_id": "C902",
            "country": "Italy",
            "product": "Keyboard",
            "quantity": "1",
            "unit_price": "0",
            "currency": "EUR",
            "data_origin": DATA_ORIGIN,
        },
        {
            "order_id": f"{prefix}903",
            "order_date": "2026-13-45",
            "customer_id": "C903",
            "country": "France",
            "product": "Webcam",
            "quantity": "1",
            "unit_price": "39.00",
            "currency": "EUR",
            "data_origin": DATA_ORIGIN,
        },
        {
            "order_id": f"{prefix}904",
            "order_date": start.isoformat(),
            "customer_id": "C904",
            "country": "France",
            "product": "Headset",
            "quantity": "1",
            "unit_price": "59.50",
            "currency": "XXX",
            "data_origin": DATA_ORIGIN,
        },
        {
            "order_id": f"{prefix}905",
            "order_date": start.isoformat(),
            "customer_id": "",
            "country": "France",
            "product": "Mouse",
            "quantity": "1",
            "unit_price": "19.90",
            "currency": "EUR",
            "data_origin": DATA_ORIGIN,
        },
    ]
    duplicate = frame.iloc[0].to_dict()
    extra = pd.DataFrame([*bad_rows, duplicate], columns=ORDER_COLUMNS)
    return pd.concat([frame, extra], ignore_index=True)
