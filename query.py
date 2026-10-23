import sys
import duckdb

DATABASE = "warehouse.duckdb"

if len(sys.argv) != 2:
    print('Usage: python query.py "SELECT * FROM raw.orders LIMIT 5"')
    sys.exit(1)

con = duckdb.connect(DATABASE)

try:
    result = con.execute(sys.argv[1])
    print(result.df().to_string(index=False))
finally:
    con.close()
