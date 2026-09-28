"""
Centralized Metrics Library — SINGLE SOURCE OF TRUTH
======================================================
Every KPI in PRD §19 and every statistic in PRD §11 is implemented
EXACTLY ONCE here. The dashboard, API, and report all import from
this module — never recalculated inline.

Architecture §4.4 — src/metrics/metrics.py
Architecture §7 — Statistical Methods Implementation Mapping

IMPORTANT: This module is the heart of the architecture. Dashboard KPI
cards, API endpoints, and report numbers must all originate from these
functions. Any chart or display that shows a number must trace back here.
"""

import pandas as pd
import numpy as np
from scipy import stats as scipy_stats


# ────────────────────────────────────────────────────────────────────────
# 5.1  Amount Statistics (PRD §10.1, §11)
# ────────────────────────────────────────────────────────────────────────

def amount_statistics(df: pd.DataFrame, amount_col: str = "absolute_amount") -> dict:
    """
    Compute comprehensive descriptive statistics for transaction amounts.

    Architecture §7 — maps each method to specific Pandas/SciPy implementation.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.
    amount_col : str
        Column to compute statistics on. Defaults to absolute_amount.

    Returns
    -------
    dict
        Complete amount statistics including count, sum, mean, median,
        min, max, std, variance, quartiles, percentiles, and IQR.
    """
    if amount_col not in df.columns:
        amount_col = "amount"

    amounts = df[amount_col].dropna()

    if len(amounts) == 0:
        return {}

    q1 = float(amounts.quantile(0.25))
    q2 = float(amounts.quantile(0.50))
    q3 = float(amounts.quantile(0.75))
    iqr = q3 - q1

    return {
        "count": int(amounts.count()),
        "sum": round(float(amounts.sum()), 2),
        "mean": round(float(amounts.mean()), 2),
        "median": round(float(amounts.median()), 2),
        "mode": round(float(amounts.mode().iloc[0]), 2) if len(amounts.mode()) > 0 else None,
        "min": round(float(amounts.min()), 2),
        "max": round(float(amounts.max()), 2),
        "std": round(float(amounts.std()), 2),
        "variance": round(float(amounts.var()), 2),
        "q1": round(q1, 2),
        "q2": round(q2, 2),
        "q3": round(q3, 2),
        "iqr": round(iqr, 2),
        "p5": round(float(amounts.quantile(0.05)), 2),
        "p10": round(float(amounts.quantile(0.10)), 2),
        "p25": round(q1, 2),
        "p50": round(q2, 2),
        "p75": round(q3, 2),
        "p90": round(float(amounts.quantile(0.90)), 2),
        "p95": round(float(amounts.quantile(0.95)), 2),
        "p99": round(float(amounts.quantile(0.99)), 2),
        "skewness": round(float(amounts.skew()), 4),
        "kurtosis": round(float(amounts.kurtosis()), 4),
        "range": round(float(amounts.max() - amounts.min()), 2),
        "coefficient_of_variation": round(float(amounts.std() / amounts.mean() * 100), 2) if amounts.mean() != 0 else None,
    }


# ────────────────────────────────────────────────────────────────────────
# 5.2  Frequency Breakdown (PRD §10.2)
# ────────────────────────────────────────────────────────────────────────

def frequency_by(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    """
    Compute transaction frequency grouped by a given dimension.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.
    dimension : str
        Column to group by (e.g., 'day_of_week', 'transaction_month',
        'customer_id', 'category', 'channel', 'transaction_type').

    Returns
    -------
    pd.DataFrame
        Transaction counts and values by the specified dimension.
    """
    if dimension not in df.columns:
        return pd.DataFrame()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    result = df.groupby(dimension).agg(
        txn_count=(amount_col, "count"),
        txn_value=(amount_col, "sum"),
        avg_value=(amount_col, "mean"),
    ).round(2).reset_index()

    result = result.sort_values("txn_count", ascending=False).reset_index(drop=True)

    return result


# ────────────────────────────────────────────────────────────────────────
# 5.3  Customer Activity (PRD §10.3, §19)
# ────────────────────────────────────────────────────────────────────────

def customer_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-customer activity metrics.

    This wraps customer_aggregates.compute_customer_metrics() to maintain
    the single-source-of-truth pattern — all metric consumers go through
    this module.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    pd.DataFrame
        Customer-level metrics table.
    """
    from src.analytics.customer_aggregates import compute_customer_metrics
    return compute_customer_metrics(df)


# ────────────────────────────────────────────────────────────────────────
# 5.4  Time Patterns (PRD §10.4)
# ────────────────────────────────────────────────────────────────────────

def time_patterns(df: pd.DataFrame) -> dict:
    """
    Compute all time-related pattern metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame with derived date fields.

    Returns
    -------
    dict
        Dictionary containing:
        - daily: daily metrics DataFrame
        - monthly: monthly metrics DataFrame
        - hourly: hourly distribution DataFrame
        - weekday_weekend: weekday vs weekend comparison
        - heatmap: day_of_week × hour pattern matrix
    """
    from src.analytics.time_aggregates import (
        compute_daily_metrics,
        compute_monthly_metrics,
        compute_time_patterns,
        compute_weekday_weekend,
        compute_hourly_distribution,
    )

    return {
        "daily": compute_daily_metrics(df),
        "monthly": compute_monthly_metrics(df),
        "hourly": compute_hourly_distribution(df),
        "weekday_weekend": compute_weekday_weekend(df),
        "heatmap": compute_time_patterns(df),
    }


# ────────────────────────────────────────────────────────────────────────
# 5.5  Category Breakdown (PRD §10.5)
# ────────────────────────────────────────────────────────────────────────

def category_breakdown(df: pd.DataFrame) -> dict:
    """
    Compute all category/channel/payment breakdown metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    dict
        Dictionary containing DataFrames for category, channel,
        payment_method, and transaction_type breakdowns.
    """
    from src.analytics.category_aggregates import (
        compute_category_metrics,
        compute_channel_metrics,
        compute_payment_method_metrics,
        compute_type_metrics,
    )

    return {
        "category": compute_category_metrics(df),
        "channel": compute_channel_metrics(df),
        "payment_method": compute_payment_method_metrics(df),
        "transaction_type": compute_type_metrics(df),
    }


# ────────────────────────────────────────────────────────────────────────
# 5.6  KPI Summary (PRD §19)
# ────────────────────────────────────────────────────────────────────────

def kpi_summary(df: pd.DataFrame) -> dict:
    """
    Compute executive-level KPI summary.

    All KPIs defined in PRD §19, computed in one place.

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.

    Returns
    -------
    dict
        Dictionary of KPI name → value pairs.
    """
    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"
    amounts = df[amount_col].dropna()

    # Total Transactions
    total_transactions = int(len(df))

    # Total Transaction Value
    total_value = round(float(amounts.sum()), 2)

    # Average Transaction Value
    avg_value = round(float(amounts.mean()), 2) if len(amounts) > 0 else 0.0

    # Median Transaction Value
    median_value = round(float(amounts.median()), 2) if len(amounts) > 0 else 0.0

    # Active Customers
    if "customer_id" in df.columns:
        active_customers = int(df["customer_id"].dropna().nunique())
    else:
        active_customers = 0

    # Transactions per Customer
    txn_per_customer = round(total_transactions / active_customers, 2) if active_customers > 0 else 0.0

    # Average Customer Value
    avg_customer_value = round(total_value / active_customers, 2) if active_customers > 0 else 0.0

    # 95th Percentile Amount
    p95_amount = round(float(amounts.quantile(0.95)), 2) if len(amounts) > 0 else 0.0

    # Date range
    date_range_start = None
    date_range_end = None
    if "transaction_date" in df.columns:
        valid_dates = df["transaction_date"].dropna()
        if len(valid_dates) > 0:
            date_range_start = str(valid_dates.min().date())
            date_range_end = str(valid_dates.max().date())

    return {
        "total_transactions": total_transactions,
        "total_value": total_value,
        "avg_value": avg_value,
        "median_value": median_value,
        "active_customers": active_customers,
        "txn_per_customer": txn_per_customer,
        "avg_customer_value": avg_customer_value,
        "p95_amount": p95_amount,
        "date_range_start": date_range_start,
        "date_range_end": date_range_end,
    }


# ────────────────────────────────────────────────────────────────────────
# 5.7  IQR Outliers (PRD §22)
# ────────────────────────────────────────────────────────────────────────

def iqr_outliers(
    df: pd.DataFrame,
    group_by: str = None,
    multiplier: float = 1.5,
) -> pd.DataFrame:
    """
    Flag transactions as statistical outliers using the IQR method.

    IMPORTANT: This is for descriptive/analytical review ONLY.
    Outlier flags must NOT be described as evidence of fraud or
    suspicious behavior (PRD §22).

    Parameters
    ----------
    df : pd.DataFrame
        Transaction DataFrame.
    group_by : str, optional
        Column to compute IQR within groups (e.g., 'category', 'transaction_type').
    multiplier : float
        IQR multiplier for threshold. Default 1.5.

    Returns
    -------
    pd.DataFrame
        Flagged outlier records with Q1, Q3, IQR, and threshold values.
        Columns: transaction_id, amount, group, Q1, Q3, IQR, upper_threshold,
                 lower_threshold, outlier_type
    """
    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"
    amounts = df[amount_col].dropna()

    if len(amounts) == 0:
        return pd.DataFrame()

    results = []

    if group_by and group_by in df.columns:
        groups = df.groupby(group_by)
    else:
        groups = [("All", df)]

    for group_name, group_df in groups:
        group_amounts = group_df[amount_col].dropna()
        if len(group_amounts) < 4:  # Need minimum data for IQR
            continue

        q1 = float(group_amounts.quantile(0.25))
        q3 = float(group_amounts.quantile(0.75))
        iqr = q3 - q1
        upper_threshold = q3 + multiplier * iqr
        lower_threshold = q1 - multiplier * iqr

        # Upper outliers
        upper_mask = group_df[amount_col] > upper_threshold
        upper_outliers = group_df[upper_mask].copy()
        upper_outliers["outlier_type"] = "upper"

        # Lower outliers
        lower_mask = group_df[amount_col] < lower_threshold
        lower_outliers = group_df[lower_mask].copy()
        lower_outliers["outlier_type"] = "lower"

        outliers = pd.concat([upper_outliers, lower_outliers])

        if len(outliers) > 0:
            outliers["group"] = str(group_name)
            outliers["Q1"] = round(q1, 2)
            outliers["Q3"] = round(q3, 2)
            outliers["IQR"] = round(iqr, 2)
            outliers["upper_threshold"] = round(upper_threshold, 2)
            outliers["lower_threshold"] = round(lower_threshold, 2)
            results.append(outliers)

    if results:
        result_df = pd.concat(results, ignore_index=True)
        # Select relevant columns
        cols = ["transaction_id", amount_col, "group", "Q1", "Q3", "IQR",
                "upper_threshold", "lower_threshold", "outlier_type"]
        cols = [c for c in cols if c in result_df.columns]
        return result_df[cols]
    else:
        return pd.DataFrame()


# ────────────────────────────────────────────────────────────────────────
# Data Quality Summary
# ────────────────────────────────────────────────────────────────────────

def data_quality_summary(df: pd.DataFrame, quarantined: pd.DataFrame = None) -> dict:
    """
    Compute data quality summary metrics.

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned transaction DataFrame.
    quarantined : pd.DataFrame, optional
        Quarantined rows from cleaning.

    Returns
    -------
    dict
        Data quality metrics.
    """
    summary = {
        "total_clean_rows": len(df),
        "null_counts": df.isnull().sum().to_dict(),
        "total_null_cells": int(df.isnull().sum().sum()),
        "completeness_pct": round((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100, 2),
    }

    if quarantined is not None and len(quarantined) > 0:
        summary["quarantined_rows"] = len(quarantined)
        if "_exclusion_reason" in quarantined.columns:
            summary["exclusion_reasons"] = quarantined["_exclusion_reason"].value_counts().to_dict()

    return summary
