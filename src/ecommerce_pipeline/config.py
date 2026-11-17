"""Réglages lus depuis l'environnement. Aucun secret n'a de valeur par défaut."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_START = date(2026, 9, 1)
DEFAULT_END = date(2026, 11, 16)
OFFLINE_START = date(2026, 10, 1)
OFFLINE_END = date(2026, 10, 12)
DEFAULT_API_URL = "https://api.frankfurter.dev/v2/rates"
QUOTES = ("USD", "TND", "MAD")


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _as_bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "oui"}


def _as_date(value: str | None, fallback: date) -> date:
    if not value:
        return fallback
    return date.fromisoformat(value)


@dataclass(frozen=True)
class Settings:
    root: Path
    duckdb_path: Path
    start: date
    end: date
    per_day: int
    seed: int
    offline: bool
    api_url: str
    webhook_url: str
    timeout_seconds: int


def load_settings() -> Settings:
    root = project_root()
    load_dotenv(root / ".env")
    offline = _as_bool(os.getenv("OFFLINE"))
    default_start = OFFLINE_START if offline else DEFAULT_START
    default_end = OFFLINE_END if offline else DEFAULT_END
    duckdb_value = os.getenv("DUCKDB_PATH", "data/warehouse.duckdb")
    duckdb_path = Path(duckdb_value)
    if not duckdb_path.is_absolute():
        duckdb_path = root / duckdb_path
    return Settings(
        root=root,
        duckdb_path=duckdb_path,
        start=_as_date(os.getenv("ORDERS_START"), default_start),
        end=_as_date(os.getenv("ORDERS_END"), default_end),
        per_day=int(os.getenv("ORDERS_PER_DAY", "20")),
        seed=int(os.getenv("RANDOM_SEED", "42")),
        offline=offline,
        api_url=os.getenv("FRANKFURTER_BASE_URL", DEFAULT_API_URL),
        webhook_url=os.getenv("ALERT_WEBHOOK_URL", ""),
        timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
    )
