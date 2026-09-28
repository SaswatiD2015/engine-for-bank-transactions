"""
Time Aggregates
================
Computes daily/weekly/monthly counts and values, weekday/weekend
and hourly distributions.
Architecture §4.3 — src/analytics/time_aggregates.py
Architecture §6.3 — Pre-aggregated tables: daily_metrics, time_pattern_metrics
"""

import pandas as pd
import numpy as np


def compute_daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute one row per calendar date with transaction metrics.

    Architecture §6.3 — daily_metrics table.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame with transaction_date column.

    Returns
    -------
    pd.DataFrame
        Daily metrics: txn_count, txn_value, distinct_active_customers
    """
    if "transaction_date_only" not in df.columns:
        if "transaction_date" in df.columns:
            df = df.copy()
            df["transaction_date_only"] = df["transaction_date"].dt.date
        else:
            return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    daily = df.groupby("transaction_date_only").agg(
        txn_count=(amount_col, "count"),
        txn_value=(amount_col, "sum"),
        avg_value=(amount_col, "mean"),
    )

    if "customer_id" in df.columns:
        cust_daily = df[df["customer_id"].notna()].groupby("transaction_date_only").agg(
            distinct_active_customers=("customer_id", "nunique"),
        )
        daily = daily.join(cust_daily)

    daily = daily.round(2).reset_index()
    daily = daily.rename(columns={"transaction_date_only": "date"})

    return daily


def compute_monthly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly aggregated transaction metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    pd.DataFrame
        Monthly metrics.
    """
    if "transaction_year" not in df.columns or "transaction_month" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    monthly = df.groupby(["transaction_year", "transaction_month"]).agg(
        txn_count=(amount_col, "count"),
        txn_value=(amount_col, "sum"),
        avg_value=(amount_col, "mean"),
    )

    if "transaction_month_name" in df.columns:
        month_names = df.groupby(["transaction_year", "transaction_month"])[
            "transaction_month_name"
        ].first()
        monthly = monthly.join(month_names)

    if "customer_id" in df.columns:
        cust_monthly = df[df["customer_id"].notna()].groupby(
            ["transaction_year", "transaction_month"]
        ).agg(
            distinct_customers=("customer_id", "nunique"),
        )
        monthly = monthly.join(cust_monthly)

    monthly = monthly.round(2).reset_index()

    # Create a proper year-month label
    monthly["year_month"] = (
        monthly["transaction_year"].astype(str) + "-" +
        monthly["transaction_month"].astype(str).str.zfill(2)
    )

    return monthly


def compute_time_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute day-of-week × hour-of-day transaction pattern matrix.

    Architecture §6.3 — time_pattern_metrics table.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame with day_of_week and hour columns.

    Returns
    -------
    pd.DataFrame
        One row per day_of_week × hour combination.
    """
    if "day_of_week" not in df.columns or "hour" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    patterns = df.groupby(["day_of_week", "day_of_week_num", "hour"]).agg(
        txn_count=(amount_col, "count"),
        txn_value=(amount_col, "sum"),
    ).round(2).reset_index()

    return patterns


def compute_weekday_weekend(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare weekday vs weekend transaction metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame with is_weekend column.

    Returns
    -------
    pd.DataFrame
        Weekday vs weekend comparison.
    """
    if "is_weekend" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    comparison = df.groupby("is_weekend").agg(
        txn_count=(amount_col, "count"),
        txn_value=(amount_col, "sum"),
        avg_value=(amount_col, "mean"),
        median_value=(amount_col, "median"),
    ).round(2).reset_index()

    comparison["day_type"] = comparison["is_weekend"].map({0: "Weekday", 1: "Weekend"})

    return comparison


def compute_hourly_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute hourly transaction distribution.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame with hour column.

    Returns
    -------
    pd.DataFrame
        Hourly distribution.
    """
    if "hour" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    hourly = df.groupby("hour").agg(
        txn_count=(amount_col, "count"),
        txn_value=(amount_col, "sum"),
        avg_value=(amount_col, "mean"),
    ).round(2).reset_index()

    return hourly
