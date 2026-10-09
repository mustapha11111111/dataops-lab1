
REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "country",
    "product",
    "quantity",
    "unit_price",
]

MAX_REJECT_RATE = 0.20


class DataQualityError(Exception):
    """Raised when the data is not good enough to continue."""


def check_schema(df):
    """Stop if a required column is missing or if the file is empty."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing:
        raise DataQualityError(
            f"Missing required columns: {', '.join(missing)}"
        )

    if df.empty:
        raise DataQualityError("Input file is empty.")


def check_reject_rate(n_total, n_rejected, max_rate=MAX_REJECT_RATE):
    """Stop if too large a share of the rows was rejected."""
    if n_total == 0:
        raise DataQualityError("Cannot calculate reject rate: no rows.")

    reject_rate = n_rejected / n_total

    if reject_rate > max_rate:
        raise DataQualityError(
            f"Reject rate {reject_rate:.1%} exceeds maximum "
            f"of {max_rate:.1%}."
        )