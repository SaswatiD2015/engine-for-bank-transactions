"""
Null and Invalid Value Handler
================================
Applies data-quality rules for missing, null, non-numeric,
and invalid values per PRD §9 and Architecture §14.
Architecture §4.2 — src/cleaning/null_handler.py
"""

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
import numpy as np


@dataclass
class CleaningResult:
    """Result of the cleaning operation."""
    data: pd.DataFrame
    quarantined: pd.DataFrame
    cleaning_summary: dict = field(default_factory=dict)


def handle_null_and_invalid(
    df: pd.DataFrame,
    max_valid_date: str = None,
) -> CleaningResult:
    """
    Handle null, missing, and invalid values in the transaction dataset.

    Rules applied (Architecture §14):
    - transaction_id: Null → quarantine (cannot analyze without ID)
    - customer_id: Missing → keep for transaction stats, flag for customer metrics
    - amount: Null / non-numeric / impossible → quarantine with reason code
    - transaction_date: Invalid / future / out-of-range → flag, exclude from time trends

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame after deduplication.
    max_valid_date : str, optional
        Maximum valid date. Defaults to today.

    Returns
    -------
    CleaningResult
        Cleaned data, quarantined rows, and summary.
    """
    if max_valid_date is None:
        max_valid_date = datetime.now().strftime("%Y-%m-%d")

    df = df.copy()
    quarantined_rows = []
    summary = {
        "input_rows": len(df),
        "null_transaction_id": 0,
        "null_amount": 0,
        "non_numeric_amount": 0,
        "impossible_amount": 0,
        "null_date": 0,
        "invalid_date": 0,
        "future_date": 0,
        "null_customer_id": 0,
    }

    # --- Rule 1: Null transaction_id → quarantine ---
    if "transaction_id" in df.columns:
        null_id_mask = df["transaction_id"].isna()
        n_null_id = null_id_mask.sum()
        summary["null_transaction_id"] = n_null_id
        if n_null_id > 0:
            quarantined = df[null_id_mask].copy()
            quarantined["_exclusion_reason"] = "null_transaction_id"
            quarantined_rows.append(quarantined)
            df = df[~null_id_mask].copy()

    # --- Rule 2: Amount — Null / non-numeric / impossible ---
    if "amount" in df.columns:
        # Convert to numeric, flag non-numeric
        original_amount = df["amount"].copy()
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        # Non-numeric amounts (were not NaN before, now are)
        non_numeric_mask = df["amount"].isna() & original_amount.notna()
        n_non_numeric = non_numeric_mask.sum()
        summary["non_numeric_amount"] = n_non_numeric
        if n_non_numeric > 0:
            quarantined = df[non_numeric_mask].copy()
            quarantined["_exclusion_reason"] = "non_numeric_amount"
            quarantined_rows.append(quarantined)
            df = df[~non_numeric_mask].copy()

        # Null amounts
        null_amt_mask = df["amount"].isna()
        n_null_amt = null_amt_mask.sum()
        summary["null_amount"] = n_null_amt
        if n_null_amt > 0:
            quarantined = df[null_amt_mask].copy()
            quarantined["_exclusion_reason"] = "null_amount"
            quarantined_rows.append(quarantined)
            df = df[~null_amt_mask].copy()

        # Impossible amounts (e.g., beyond ±10 million for typical banking)
        impossible_mask = df["amount"].abs() > 10_000_000
        n_impossible = impossible_mask.sum()
        summary["impossible_amount"] = n_impossible
        if n_impossible > 0:
            quarantined = df[impossible_mask].copy()
            quarantined["_exclusion_reason"] = "impossible_amount"
            quarantined_rows.append(quarantined)
            df = df[~impossible_mask].copy()

    # --- Rule 3: Date — Invalid / future / out-of-range ---
    if "transaction_date" in df.columns:
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

        # Null dates (unparseable)
        null_date_mask = df["transaction_date"].isna()
        n_null_date = null_date_mask.sum()
        summary["null_date"] = n_null_date
        # Don't quarantine, but flag
        df.loc[null_date_mask, "_date_flag"] = "invalid_date"
        summary["invalid_date"] = n_null_date

        # Future dates
        max_date = pd.Timestamp(max_valid_date)
        future_mask = df["transaction_date"] > max_date
        n_future = future_mask.sum()
        summary["future_date"] = n_future
        df.loc[future_mask, "_date_flag"] = "future_date"

    # --- Rule 4: Customer ID — track null count but keep rows ---
    if "customer_id" in df.columns:
        null_cust_mask = df["customer_id"].isna()
        summary["null_customer_id"] = null_cust_mask.sum()
        df.loc[null_cust_mask, "_customer_flag"] = "missing_customer_id"

    # Combine quarantined
    if quarantined_rows:
        quarantined_df = pd.concat(quarantined_rows, ignore_index=True)
    else:
        quarantined_df = pd.DataFrame()

    summary["output_rows"] = len(df)
    summary["quarantined_rows"] = len(quarantined_df)

    return CleaningResult(
        data=df,
        quarantined=quarantined_df,
        cleaning_summary=summary,
    )
