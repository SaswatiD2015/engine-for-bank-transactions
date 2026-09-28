"""
Customer Aggregates
====================
Computes per-customer transaction metrics.
Architecture §4.3 — src/analytics/customer_aggregates.py
Architecture §6.3 — Pre-aggregated table: customer_metrics
"""

import pandas as pd
import numpy as np


def compute_customer_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-customer aggregated metrics.

    Metrics per customer:
    - transaction_count: total number of transactions
    - total_value: sum of amounts
    - avg_value: mean transaction amount
    - median_value: median transaction amount
    - min_value: minimum transaction amount
    - max_value: maximum transaction amount
    - active_days: count of distinct transaction dates
    - first_transaction: earliest transaction date
    - last_transaction: latest transaction date
    - active_period_days: days between first and last transaction

    Rows with missing customer_id are excluded (Architecture §14).

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame with customer_id and amount columns.

    Returns
    -------
    pd.DataFrame
        Customer-level metrics table (customer_metrics).
    """
    # Exclude rows without customer_id
    valid_df = df[df["customer_id"].notna()].copy()

    if len(valid_df) == 0:
        return pd.DataFrame()

    # Use absolute_amount if available, else amount
    amount_col = "absolute_amount" if "absolute_amount" in valid_df.columns else "amount"

    agg_dict = {
        amount_col: ["count", "sum", "mean", "median", "min", "max", "std"],
    }

    # Date metrics
    if "transaction_date" in valid_df.columns:
        agg_dict["transaction_date"] = ["min", "max"]

    if "transaction_date_only" in valid_df.columns:
        agg_dict["transaction_date_only"] = "nunique"

    customer_metrics = valid_df.groupby("customer_id").agg(agg_dict)

    # Flatten multi-level columns
    customer_metrics.columns = [
        "_".join(col).strip("_") for col in customer_metrics.columns
    ]

    # Rename for clarity
    rename_map = {
        f"{amount_col}_count": "transaction_count",
        f"{amount_col}_sum": "total_value",
        f"{amount_col}_mean": "avg_value",
        f"{amount_col}_median": "median_value",
        f"{amount_col}_min": "min_value",
        f"{amount_col}_max": "max_value",
        f"{amount_col}_std": "std_value",
        "transaction_date_min": "first_transaction",
        "transaction_date_max": "last_transaction",
        "transaction_date_only_nunique": "active_days",
    }

    customer_metrics = customer_metrics.rename(
        columns={k: v for k, v in rename_map.items() if k in customer_metrics.columns}
    )

    # Compute active period
    if "first_transaction" in customer_metrics.columns and "last_transaction" in customer_metrics.columns:
        customer_metrics["active_period_days"] = (
            customer_metrics["last_transaction"] - customer_metrics["first_transaction"]
        ).dt.days

    # Round numeric columns
    numeric_cols = ["total_value", "avg_value", "median_value", "min_value", "max_value", "std_value"]
    for col in numeric_cols:
        if col in customer_metrics.columns:
            customer_metrics[col] = customer_metrics[col].round(2)

    customer_metrics = customer_metrics.reset_index()

    return customer_metrics
