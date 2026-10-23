import sys
from pathlib import Path

import duckdb

DATABASE = "warehouse.duckdb"


def main():
    if len(sys.argv) != 2:
        print("Usage: python load_raw.py data/raw/orders_day1.csv")
        sys.exit(1)

    csv_path = Path(sys.argv[1])

    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        sys.exit(1)

    con = duckdb.connect(DATABASE)

    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    con.execute("""
        CREATE TABLE IF NOT EXISTS raw.orders (
            _row_number BIGINT,
            _source_file VARCHAR,
            _loaded_at TIMESTAMP
        )
    """)

    con.execute("DROP TABLE IF EXISTS raw.orders")

    con.execute(f"""
        CREATE TABLE raw.orders AS
        SELECT
            *,
            row_number() OVER () AS _row_number,
            '{csv_path.name}' AS _source_file,
            current_timestamp AS _loaded_at
        FROM read_csv(
            '{csv_path.resolve().as_posix()}',
            all_varchar = true,
            header = true
        )
    """)

    count = con.execute("SELECT COUNT(*) FROM raw.orders").fetchone()[0]
    print(f"Loaded {count} rows from {csv_path}")
    print("Table created: raw.orders")

    con.close()


if __name__ == "__main__":
    main()
