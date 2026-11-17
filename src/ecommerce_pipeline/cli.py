"""Point d'entrée : une exécution, ou le rendez-vous quotidien."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from ecommerce_pipeline.config import OFFLINE_END, OFFLINE_START, load_settings
from ecommerce_pipeline.pipeline import run_pipeline


def _parse_day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"Date invalide : {value}. Format attendu : AAAA-MM-JJ.") from exc


def main(argv: list[str] | None = None) -> None:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Pipeline DataOps des ventes multi-devises.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Ingère, transforme, teste et écrit l'alerte.")
    run.add_argument("--offline", action="store_true", help="Utilise le fichier de taux local.")
    run.add_argument("--start", help="Date de début AAAA-MM-JJ.")
    run.add_argument("--end", help="Date de fin AAAA-MM-JJ.")
    run.add_argument("--per-day", type=int, help="Nombre de commandes générées par jour.")
    run.add_argument("--seed", type=int, help="Graine du générateur.")
    run.add_argument("--db", help="Chemin du fichier DuckDB.")
    run.add_argument("--skip-dbt", action="store_true", help="Charge seulement le brut.")

    sub.add_parser("schedule", help="Relance le flow Prefect tous les jours à 06:00.")
    args = parser.parse_args(argv)

    if args.command == "schedule":
        from ecommerce_pipeline.flow import serve

        serve()
        return

    offline = args.offline or settings.offline
    if args.start:
        start = _parse_day(args.start)
    elif args.offline:
        start = OFFLINE_START
    else:
        start = settings.start
    if args.end:
        end = _parse_day(args.end)
    elif args.offline:
        end = OFFLINE_END
    else:
        end = settings.end

    result = run_pipeline(
        start=start,
        end=end,
        per_day=args.per_day or settings.per_day,
        seed=args.seed if args.seed is not None else settings.seed,
        offline=offline,
        api_url=settings.api_url,
        timeout=settings.timeout_seconds,
        duckdb_path=Path(args.db) if args.db else settings.duckdb_path,
        root=settings.root,
        webhook_url=settings.webhook_url,
        build_dbt=not args.skip_dbt,
    )
    if result["status"] != "success":
        sys.exit(1)
