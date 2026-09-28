"""
Derived Fields
===============
Adds analytical derived columns to the cleaned transaction dataset.
Architecture §4.3 — src/analytics/derived_fields.py
Architecture §6.2 — Derived Fields specification
"""

import pandas as pd
import numpy as np


def add_derived_fields(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all derived analytical fields to the DataFrame.

    Derived fields (Architecture §6.2):
    - transaction_year, transaction_quarter, transaction_month, transaction_week
    - day_of_week, hour, is_weekend
    - amount_band
    - absolute_amount

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned DataFrame with transaction_date and amount columns.

    Returns
    -------
    pd.DataFrame
        DataFrame with derived fields added.
    """
    df = df.copy()

    # --- Date-derived fields ---
    if "transaction_date" in df.columns:
        dt = df["transaction_date"]

        df["transaction_year"] = dt.dt.year
        df["transaction_quarter"] = dt.dt.quarter
        df["transaction_month"] = dt.dt.month
        df["transaction_month_name"] = dt.dt.month_name()
        df["transaction_week"] = dt.dt.isocalendar().week.astype(int)
        df["day_of_week"] = dt.dt.day_name()
        df["day_of_week_num"] = dt.dt.dayofweek  # 0=Monday, 6=Sunday
        df["hour"] = dt.dt.hour
        df["is_weekend"] = dt.dt.dayofweek.isin([5, 6]).astype(int)
        df["transaction_date_only"] = dt.dt.date

    # --- Amount-derived fields ---
    if "amount" in df.columns:
        df["absolute_amount"] = df["amount"].abs()

        # Amount bands for distribution analysis
        df["amount_band"] = pd.cut(
            df["absolute_amount"],
            bins=[0, 100, 500, 1000, 5000, 10000, 50000, 100000, float("inf")],
            labels=[
                "0-100", "100-500", "500-1K", "1K-5K",
                "5K-10K", "10K-50K", "50K-100K", "100K+"
            ],
            right=True,
            include_lowest=True,
        )

    return df
