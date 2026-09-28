"""
Category Aggregates
====================
Computes count/amount by category, channel, payment method,
and cross-tabulations.
Architecture §4.3 — src/analytics/category_aggregates.py
Architecture §6.3 — Pre-aggregated table: category_metrics
"""

import pandas as pd
import numpy as np


def compute_category_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute transaction metrics grouped by category.

    Architecture §6.3 — category_metrics table.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    pd.DataFrame
        One row per category with count, total, avg, and percentage.
    """
    if "category" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    category = df.groupby("category").agg(
        txn_count=(amount_col, "count"),
        total_amount=(amount_col, "sum"),
        avg_amount=(amount_col, "mean"),
        median_amount=(amount_col, "median"),
    ).round(2).reset_index()

    # Add percentage of total
    total_count = category["txn_count"].sum()
    total_value = category["total_amount"].sum()
    category["pct_of_total_count"] = (category["txn_count"] / total_count * 100).round(2)
    category["pct_of_total_value"] = (category["total_amount"] / total_value * 100).round(2)

    category = category.sort_values("txn_count", ascending=False).reset_index(drop=True)

    return category


def compute_channel_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute transaction metrics grouped by channel.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    pd.DataFrame
        Channel-level metrics.
    """
    if "channel" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    channel = df.groupby("channel").agg(
        txn_count=(amount_col, "count"),
        total_amount=(amount_col, "sum"),
        avg_amount=(amount_col, "mean"),
    ).round(2).reset_index()

    total_count = channel["txn_count"].sum()
    total_value = channel["total_amount"].sum()
    channel["pct_of_total_count"] = (channel["txn_count"] / total_count * 100).round(2)
    channel["pct_of_total_value"] = (channel["total_amount"] / total_value * 100).round(2)

    channel = channel.sort_values("txn_count", ascending=False).reset_index(drop=True)

    return channel


def compute_payment_method_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute transaction metrics grouped by payment method.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    pd.DataFrame
        Payment method metrics.
    """
    if "payment_method" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    pm = df.groupby("payment_method").agg(
        txn_count=(amount_col, "count"),
        total_amount=(amount_col, "sum"),
        avg_amount=(amount_col, "mean"),
    ).round(2).reset_index()

    total_count = pm["txn_count"].sum()
    pm["pct_of_total_count"] = (pm["txn_count"] / total_count * 100).round(2)

    pm = pm.sort_values("txn_count", ascending=False).reset_index(drop=True)

    return pm


def compute_type_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute transaction metrics grouped by transaction type.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    pd.DataFrame
        Transaction type metrics.
    """
    if "transaction_type" not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    type_metrics = df.groupby("transaction_type").agg(
        txn_count=(amount_col, "count"),
        total_amount=(amount_col, "sum"),
        avg_amount=(amount_col, "mean"),
        median_amount=(amount_col, "median"),
    ).round(2).reset_index()

    total_count = type_metrics["txn_count"].sum()
    type_metrics["pct_of_total_count"] = (type_metrics["txn_count"] / total_count * 100).round(2)

    type_metrics = type_metrics.sort_values("txn_count", ascending=False).reset_index(drop=True)

    return type_metrics


def compute_cross_tab(
    df: pd.DataFrame,
    row_col: str = "channel",
    col_col: str = "transaction_type",
) -> pd.DataFrame:
    """
    Compute a cross-tabulation of two categorical columns.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.
    row_col : str
        Column for rows.
    col_col : str
        Column for columns.

    Returns
    -------
    pd.DataFrame
        Cross-tabulation table (counts).
    """
    if row_col not in df.columns or col_col not in df.columns:
        return pd.DataFrame()

    return pd.crosstab(df[row_col], df[col_col], margins=True, margins_name="Total")
