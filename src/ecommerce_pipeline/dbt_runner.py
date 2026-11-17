"""Lance dbt build. Un test en échec empêche de considérer les marts comme publiés."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def dbt_executable() -> str:
    scripts = Path(sys.executable).parent
    for name in ("dbt.exe", "dbt"):
        candidate = scripts / name
        if candidate.exists():
            return str(candidate)
    return "dbt"


def _run_dbt(root: Path, duckdb_path: Path, arguments: list[str], failure: str) -> None:
    env = os.environ.copy()
    env["DUCKDB_PATH"] = duckdb_path.resolve().as_posix()
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    command = [
        dbt_executable(),
        *arguments,
        "--project-dir",
        str(root / "dbt"),
        "--profiles-dir",
        str(root / "dbt"),
        "--no-use-colors",
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        details = f"{completed.stdout}\n{completed.stderr}"[-4000:]
        raise RuntimeError(f"{failure}\n{details}")


def run_dbt(root: Path, duckdb_path: Path) -> None:
    _run_dbt(
        root,
        duckdb_path,
        ["build"],
        "dbt build a échoué. Les marts ne doivent pas être utilisés.",
    )


def run_freshness(root: Path, duckdb_path: Path) -> None:
    """Échoue si une source dépasse le délai d'erreur déclaré dans sources.yml."""
    _run_dbt(
        root,
        duckdb_path,
        ["source", "freshness"],
        "Les sources ne sont pas assez fraîches. Les marts ne doivent pas être utilisés.",
    )
