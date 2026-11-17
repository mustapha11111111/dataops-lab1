"""Tableau de bord. Il ne lit que les marts, et seulement si le dernier run est vert."""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "warehouse.duckdb"


def warehouse_path() -> Path:
    configured = os.getenv("DUCKDB_PATH", str(DEFAULT_DB))
    path = Path(configured)
    if not path.is_absolute():
        path = ROOT / path
    return path


def read_sql(path: Path, sql: str) -> pd.DataFrame:
    connection = duckdb.connect(str(path), read_only=True)
    try:
        return connection.execute(sql).df()
    finally:
        connection.close()


def main() -> None:
    st.set_page_config(page_title="Ventes multi-devises", layout="wide")
    st.title("Ventes e-commerce multi-devises")
    st.caption("Données synthétiques. Les montants affichés sont en euros, après contrôle.")

    path = warehouse_path()
    if not path.exists():
        st.error("Entrepôt introuvable. Lance d'abord : python -m ecommerce_pipeline run")
        return

    try:
        runs = read_sql(
            path,
            "SELECT * FROM ops.pipeline_runs ORDER BY started_at DESC LIMIT 5",
        )
    except duckdb.Error as exc:
        st.error(f"Impossible de lire la santé du pipeline : {exc}")
        return

    if runs.empty:
        st.warning("Aucune exécution enregistrée.")
        return

    latest = runs.iloc[0]
    columns = st.columns(4)
    columns[0].metric("Dernier statut", latest["status"])
    columns[1].metric("Alerte", latest["alert_level"])
    columns[2].metric("Commandes publiées", int(latest["orders_published"] or 0))
    columns[3].metric("Anomalies", int(latest["anomalies"] or 0))
    st.write(latest["message"])

    if latest["status"] != "success":
        st.error(
            "Le dernier pipeline n'est pas vert. Les chiffres ci-dessous ne sont pas affichés."
        )
        st.dataframe(runs, width="stretch")
        return

    revenue = read_sql(
        path,
        """
        SELECT country, round(sum(revenue_eur), 2) AS revenue_eur
        FROM mart_revenue_by_country_day
        GROUP BY country
        ORDER BY revenue_eur DESC
        """,
    )
    daily = read_sql(
        path,
        """
        SELECT order_date, country, revenue_eur
        FROM mart_revenue_by_country_day
        ORDER BY order_date, country
        """,
    )
    products = read_sql(
        path,
        """
        SELECT product, revenue_recent_eur, revenue_previous_eur, variation_pct
        FROM mart_product_performance
        ORDER BY revenue_recent_eur DESC
        """,
    )
    segments = read_sql(
        path,
        """
        SELECT segment, customers, revenue_eur
        FROM mart_customer_segments
        ORDER BY revenue_eur DESC
        """,
    )
    anomalies = read_sql(
        path,
        """
        SELECT order_date, country, revenue_eur, median_revenue_eur, orders_count, anomaly_type
        FROM mart_sales_anomalies
        WHERE anomaly_type IN ('hausse_anormale', 'baisse_anormale')
        ORDER BY order_date, country
        """,
    )

    tab_revenue, tab_products, tab_anomalies = st.tabs(
        ["Chiffre d'affaires", "Produits et clients", "Anomalies"]
    )
    with tab_revenue:
        st.subheader("Chiffre d'affaires en EUR par pays")
        st.bar_chart(revenue, x="country", y="revenue_eur")
        pivot = daily.pivot(index="order_date", columns="country", values="revenue_eur")
        st.line_chart(pivot)
        monthly = read_sql(
            path,
            """
            SELECT year_month, country, revenue_eur
            FROM mart_revenue_by_country_month
            ORDER BY year_month, country
            """,
        )
        st.dataframe(monthly, width="stretch")
    with tab_products:
        st.subheader("Produits : 30 derniers jours contre les 30 jours d'avant")
        st.dataframe(products, width="stretch")
        st.subheader("Segments de clients")
        st.bar_chart(segments, x="segment", y="revenue_eur")
    with tab_anomalies:
        st.subheader("Journées à vérifier")
        if anomalies.empty:
            st.success("Aucune hausse ou baisse anormale sur la période publiée.")
        else:
            st.warning(
                "Ces journées s'écartent de la médiane du pays. "
                "Le pic tunisien est planté dans le générateur."
            )
            st.dataframe(anomalies, width="stretch")


if __name__ == "__main__":
    main()
