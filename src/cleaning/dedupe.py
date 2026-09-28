"""
Deduplication Module
=====================
Flags and removes duplicate transaction_id and exact duplicate rows,
with an audit count.
Architecture §4.2 — src/cleaning/dedupe.py
PRD §9 — Data Quality Rules
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class DedupeResult:
    """Result of deduplication operation."""
    data: pd.DataFrame
    duplicate_id_count: int
    exact_duplicate_count: int
    total_removed: int
    duplicate_ids: pd.DataFrame  # The duplicated rows for audit


def remove_duplicates(df: pd.DataFrame) -> DedupeResult:
    """
    Identify and remove duplicate transactions.

    Two types of duplicates are checked:
    1. Duplicate transaction_id — keeps first occurrence, quarantines rest.
    2. Exact duplicate rows — identical across all columns.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame with potential duplicates.

    Returns
    -------
    DedupeResult
        Cleaned DataFrame and audit information.
    """
    initial_count = len(df)

    # --- Step 1: Exact duplicate rows ---
    exact_dup_mask = df.duplicated(keep="first")
    exact_dup_count = exact_dup_mask.sum()
    exact_dups = df[exact_dup_mask].copy()
    exact_dups["_exclusion_reason"] = "exact_duplicate_row"

    df_no_exact = df[~exact_dup_mask].copy()

    # --- Step 2: Duplicate transaction_id (after removing exact dupes) ---
    if "transaction_id" in df_no_exact.columns:
        id_dup_mask = df_no_exact["transaction_id"].duplicated(keep="first")
        id_dup_count = id_dup_mask.sum()
        id_dups = df_no_exact[id_dup_mask].copy()
        id_dups["_exclusion_reason"] = "duplicate_transaction_id"

        df_clean = df_no_exact[~id_dup_mask].copy()
    else:
        id_dup_count = 0
        id_dups = pd.DataFrame()
        df_clean = df_no_exact

    # Combine quarantined records
    all_dups = pd.concat([exact_dups, id_dups], ignore_index=True)
    total_removed = exact_dup_count + id_dup_count

    return DedupeResult(
        data=df_clean,
        duplicate_id_count=id_dup_count,
        exact_duplicate_count=exact_dup_count,
        total_removed=total_removed,
        duplicate_ids=all_dups,
    )
