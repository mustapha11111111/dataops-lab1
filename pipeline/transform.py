import pandas as pd

MAX_UNIT_PRICE = 1000


def _flag(df, mask, reason):
    """Mark the rows selected by mask as rejected, unless already rejected."""
    df.loc[mask & df["reject_reason"].isna(), "reject_reason"] = reason


def clean_orders(df):
    """Apply the quality rules. Returns two tables: clean and rejected."""
    df = df.copy()
    df["reject_reason"] = None

    
    # Normalize country names.
    df["country"] = df["country"].str.strip().str.title()

    # Rule 1: customer ID is required.
    _flag(df, df["customer_id"].isna(), "missing_customer_id")

    # Rule 2: order date must be valid.
    df["order_date"] = pd.to_datetime(
        df["order_date"],
        format="%Y-%m-%d",
        errors="coerce",
    )
    _flag(df, df["order_date"].isna(), "invalid_date")

    # Rule 3: quantity must be positive.
    _flag(df, ~(df["quantity"] > 0), "invalid_quantity")

    # Rule 4: unit price must be between 0.01 and MAX_UNIT_PRICE.
    _flag(
        df,
        ~df["unit_price"].between(0.01, MAX_UNIT_PRICE),
        "invalid_unit_price",
    )

    # Rule 5: reject duplicate order IDs, keeping the first.
    _flag(
        df,
        df.duplicated("order_id", keep="first"),
        "duplicate_order_id",
    )

    rejected = df[df["reject_reason"].notna()]
    clean = df[df["reject_reason"].isna()].drop(columns="reject_reason")
    return clean, rejected


def revenue_by_country(clean):
    """Transform: total revenue per country."""
    out = clean.assign(revenue=clean["quantity"] * clean["unit_price"])
    out = out.groupby("country", as_index=False)["revenue"].sum()
    out["revenue"] = out["revenue"].round(2)
    return out