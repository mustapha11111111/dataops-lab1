import duckdb

connection = duckdb.connect("data/warehouse.duckdb", read_only=True)
print("CA_PAYS")
print(
    connection.execute(
        """
        SELECT country, round(sum(revenue_eur), 2) AS revenue_eur
        FROM mart_revenue_by_country_day
        GROUP BY country
        ORDER BY revenue_eur DESC
        """
    ).fetchall()
)
print("ANOMALIES")
print(
    connection.execute(
        """
        SELECT order_date, country, anomaly_type, revenue_eur
        FROM mart_sales_anomalies
        WHERE anomaly_type IN ('hausse_anormale', 'baisse_anormale')
        """
    ).fetchall()
)
print("SEGMENTS")
print(connection.execute("SELECT * FROM mart_customer_segments").fetchall())
print("PRODUITS")
print(
    connection.execute(
        """
        SELECT product, round(variation_pct, 3)
        FROM mart_product_performance
        ORDER BY variation_pct DESC NULLS LAST
        """
    ).fetchall()
)
connection.close()
