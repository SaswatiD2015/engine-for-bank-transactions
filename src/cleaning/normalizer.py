"""
Data Normalizer
================
Standardizes categorical values (category, type, channel, status)
using controlled vocabulary maps. Normalizes currency and amounts.
Architecture §4.2 — src/cleaning/normalizer.py
"""

from dataclasses import dataclass, field

import pandas as pd
import numpy as np


# --- Controlled Vocabulary Maps ---
# Maps common typos/variants to canonical values

CATEGORY_MAP = {
    # Canonical values
    "salary": "Salary",
    "food & dining": "Food & Dining",
    "food and dining": "Food & Dining",
    "food": "Food & Dining",
    "dining": "Food & Dining",
    "shopping": "Shopping",
    "utilities": "Utilities",
    "utility": "Utilities",
    "travel": "Travel",
    "trvel": "Travel",
    "entertainment": "Entertainment",
    "entertainmnet": "Entertainment",
    "healthcare": "Healthcare",
    "health": "Healthcare",
    "education": "Education",
    "rent": "Rent",
    "insurance": "Insurance",
    "investment": "Investment",
    "groceries": "Groceries",
    "grocery": "Groceries",
    "fuel": "Fuel",
    "petrol": "Fuel",
    "subscriptions": "Subscriptions",
    "subscription": "Subscriptions",
    "other": "Other",
}

TRANSACTION_TYPE_MAP = {
    "deposit": "Deposit",
    "withdrawal": "Withdrawal",
    "withdraw": "Withdrawal",
    "transfer": "Transfer",
    "payment": "Payment",
    "pay": "Payment",
    "refund": "Refund",
}

CHANNEL_MAP = {
    "atm": "ATM",
    "branch": "Branch",
    "mobile": "Mobile",
    "mobile app": "Mobile",
    "web": "Web",
    "online": "Web",
    "internet banking": "Web",
    "pos": "POS",
    "point of sale": "POS",
}

STATUS_MAP = {
    "completed": "Completed",
    "complete": "Completed",
    "success": "Completed",
    "successful": "Completed",
    "failed": "Failed",
    "fail": "Failed",
    "failure": "Failed",
    "reversed": "Reversed",
    "reverse": "Reversed",
    "pending": "Pending",
    "in progress": "Pending",
    "processing": "Pending",
}

PAYMENT_METHOD_MAP = {
    "card": "Card",
    "credit card": "Card",
    "debit card": "Card",
    "upi": "UPI",
    "bank transfer": "Bank Transfer",
    "neft": "Bank Transfer",
    "rtgs": "Bank Transfer",
    "imps": "Bank Transfer",
    "cash": "Cash",
    "net banking": "Net Banking",
    "netbanking": "Net Banking",
    "internet banking": "Net Banking",
}


@dataclass
class NormalizationResult:
    """Result of normalization operation."""
    data: pd.DataFrame
    normalization_summary: dict = field(default_factory=dict)
    unmapped_values: dict = field(default_factory=dict)


def _normalize_column(
    series: pd.Series,
    vocab_map: dict,
    column_name: str,
) -> tuple:
    """
    Normalize a single categorical column using a vocabulary map.

    Returns
    -------
    tuple
        (normalized_series, n_normalized, n_unmapped, unmapped_values)
    """
    original = series.copy()
    # Strip whitespace and lowercase for matching
    cleaned = series.astype(str).str.strip().str.lower()

    # Map using vocabulary
    normalized = cleaned.map(vocab_map)

    # Track unmapped values
    unmapped_mask = normalized.isna() & series.notna() & (series.astype(str).str.strip() != "")
    unmapped_values = cleaned[unmapped_mask].unique().tolist()
    n_unmapped = unmapped_mask.sum()

    # For unmapped values, label as 'Unknown' if truly unrecognizable,
    # otherwise title-case the original
    normalized = normalized.fillna(
        series.astype(str).str.strip().str.title()
    )

    # Preserve NaN from original
    normalized[series.isna()] = np.nan

    n_changed = (original.astype(str) != normalized.astype(str)).sum()

    return normalized, n_changed, n_unmapped, unmapped_values


def normalize_data(df: pd.DataFrame) -> NormalizationResult:
    """
    Normalize all categorical columns and amounts.

    Normalizations applied:
    1. Category → controlled vocabulary (CATEGORY_MAP)
    2. Transaction type → controlled vocabulary (TRANSACTION_TYPE_MAP)
    3. Channel → controlled vocabulary (CHANNEL_MAP)
    4. Status → controlled vocabulary (STATUS_MAP)
    5. Payment method → controlled vocabulary (PAYMENT_METHOD_MAP)
    6. Amount rounding to 2 decimal places

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame after null handling.

    Returns
    -------
    NormalizationResult
        Normalized DataFrame with summary.
    """
    df = df.copy()
    summary = {}
    unmapped = {}

    # --- Normalize categorical columns ---
    column_maps = {
        "category": CATEGORY_MAP,
        "transaction_type": TRANSACTION_TYPE_MAP,
        "channel": CHANNEL_MAP,
        "status": STATUS_MAP,
        "payment_method": PAYMENT_METHOD_MAP,
    }

    for col, vocab in column_maps.items():
        if col in df.columns:
            normalized, n_changed, n_unmapped, unmapped_vals = _normalize_column(
                df[col], vocab, col
            )
            df[col] = normalized
            summary[f"{col}_normalized"] = n_changed
            summary[f"{col}_unmapped"] = n_unmapped
            if unmapped_vals:
                unmapped[col] = unmapped_vals

    # --- Normalize amounts ---
    if "amount" in df.columns:
        df["amount"] = df["amount"].round(2)

    # --- Normalize currency ---
    if "currency" in df.columns:
        df["currency"] = df["currency"].astype(str).str.strip().str.upper()
        n_currencies = df["currency"].nunique()
        summary["unique_currencies"] = n_currencies
        if n_currencies > 1:
            summary["currency_warning"] = "Multiple currencies detected. Segment by currency recommended."

    return NormalizationResult(
        data=df,
        normalization_summary=summary,
        unmapped_values=unmapped,
    )
