"""
Schema Validator
=================
Validates that the loaded DataFrame conforms to the expected transaction
schema before any processing begins.
Architecture §4.1 — src/ingestion/schema_validator.py
PRD §7 — Dataset Requirements, §9 — Data Quality Rules
"""

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import numpy as np


# Required columns that MUST be present (PRD §7)
REQUIRED_COLUMNS = ["transaction_id", "customer_id", "transaction_date", "amount"]

# Recommended columns (should warn if missing)
RECOMMENDED_COLUMNS = ["transaction_type", "status", "currency"]

# Optional columns (informational only)
OPTIONAL_COLUMNS = [
    "category", "channel", "payment_method", "merchant", "location"
]

# Expected data types after conversion
EXPECTED_TYPES = {
    "transaction_id": "object",
    "customer_id": "object",
    "transaction_date": "datetime64[ns]",
    "amount": "float64",
    "transaction_type": "object",
    "status": "object",
    "category": "object",
    "channel": "object",
    "payment_method": "object",
    "merchant": "object",
    "location": "object",
    "currency": "object",
}


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: str  # "ERROR", "WARNING", "INFO"
    field: str
    message: str


@dataclass
class ValidationReport:
    """Structured validation report for the dataset."""
    is_valid: bool
    total_rows: int
    total_columns: int
    issues: list = field(default_factory=list)
    missing_required: list = field(default_factory=list)
    missing_recommended: list = field(default_factory=list)
    type_conversion_errors: dict = field(default_factory=dict)
    null_counts: dict = field(default_factory=dict)

    def summary(self) -> str:
        """Return a human-readable summary of validation results."""
        lines = [
            f"Validation Result: {'PASSED' if self.is_valid else 'FAILED'}",
            f"Total Rows: {self.total_rows:,}",
            f"Total Columns: {self.total_columns}",
            f"Issues Found: {len(self.issues)}",
        ]

        if self.missing_required:
            lines.append(f"Missing Required Columns: {', '.join(self.missing_required)}")
        if self.missing_recommended:
            lines.append(f"Missing Recommended Columns: {', '.join(self.missing_recommended)}")

        errors = [i for i in self.issues if i.severity == "ERROR"]
        warnings = [i for i in self.issues if i.severity == "WARNING"]

        if errors:
            lines.append(f"\nErrors ({len(errors)}):")
            for e in errors:
                lines.append(f"  [{e.field}] {e.message}")
        if warnings:
            lines.append(f"\nWarnings ({len(warnings)}):")
            for w in warnings:
                lines.append(f"  [{w.field}] {w.message}")

        return "\n".join(lines)


def validate_schema(df: pd.DataFrame) -> ValidationReport:
    """
    Validate the DataFrame against the expected transaction schema.

    Checks:
    1. Required columns are present
    2. Recommended columns (warns if missing)
    3. Data types can be converted
    4. Non-empty dataset
    5. Null counts for required fields

    Parameters
    ----------
    df : pd.DataFrame
        The raw loaded DataFrame.

    Returns
    -------
    ValidationReport
        Structured report with validation results.
    """
    issues = []
    missing_required = []
    missing_recommended = []
    type_errors = {}
    is_valid = True

    # --- Check: non-empty dataset ---
    if len(df) == 0:
        issues.append(ValidationIssue(
            severity="ERROR", field="dataset",
            message="Dataset is empty (0 rows)."
        ))
        return ValidationReport(
            is_valid=False,
            total_rows=0,
            total_columns=len(df.columns),
            issues=issues,
        )

    # --- Check: required columns ---
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            missing_required.append(col)
            issues.append(ValidationIssue(
                severity="ERROR", field=col,
                message=f"Required column '{col}' is missing."
            ))
            is_valid = False

    # --- Check: recommended columns ---
    for col in RECOMMENDED_COLUMNS:
        if col not in df.columns:
            missing_recommended.append(col)
            issues.append(ValidationIssue(
                severity="WARNING", field=col,
                message=f"Recommended column '{col}' is missing. Some analyses may be limited."
            ))

    # --- Check: data types for present columns ---
    if "amount" in df.columns:
        try:
            pd.to_numeric(df["amount"], errors="raise")
        except (ValueError, TypeError):
            non_numeric = pd.to_numeric(df["amount"], errors="coerce").isna() & df["amount"].notna()
            n_bad = non_numeric.sum()
            type_errors["amount"] = n_bad
            issues.append(ValidationIssue(
                severity="ERROR" if n_bad > len(df) * 0.5 else "WARNING",
                field="amount",
                message=f"{n_bad:,} rows have non-numeric amount values."
            ))
            if n_bad > len(df) * 0.5:
                is_valid = False

    if "transaction_date" in df.columns:
        try:
            pd.to_datetime(df["transaction_date"], errors="raise")
        except (ValueError, TypeError):
            bad_dates = pd.to_datetime(df["transaction_date"], errors="coerce").isna() & df["transaction_date"].notna()
            n_bad = bad_dates.sum()
            type_errors["transaction_date"] = n_bad
            issues.append(ValidationIssue(
                severity="ERROR" if n_bad > len(df) * 0.5 else "WARNING",
                field="transaction_date",
                message=f"{n_bad:,} rows have unparseable date values."
            ))
            if n_bad > len(df) * 0.5:
                is_valid = False

    # --- Check: null counts for required fields ---
    null_counts = {}
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            n_null = df[col].isna().sum()
            null_counts[col] = n_null
            if n_null > 0:
                pct = n_null / len(df) * 100
                severity = "ERROR" if col in ("transaction_id", "amount") and pct > 10 else "WARNING"
                issues.append(ValidationIssue(
                    severity=severity, field=col,
                    message=f"{n_null:,} null values ({pct:.1f}%) in required column '{col}'."
                ))

    # --- Check: duplicate transaction IDs ---
    if "transaction_id" in df.columns:
        n_dup = df["transaction_id"].duplicated().sum()
        if n_dup > 0:
            issues.append(ValidationIssue(
                severity="WARNING", field="transaction_id",
                message=f"{n_dup:,} duplicate transaction_id values found."
            ))

    return ValidationReport(
        is_valid=is_valid,
        total_rows=len(df),
        total_columns=len(df.columns),
        issues=issues,
        missing_required=missing_required,
        missing_recommended=missing_recommended,
        type_conversion_errors=type_errors,
        null_counts=null_counts,
    )


def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Coerce DataFrame columns to expected types after validation.

    Parameters
    ----------
    df : pd.DataFrame
        Validated DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with corrected types.
    """
    df = df.copy()

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

    if "transaction_date" in df.columns:
        df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

    # Ensure string columns are string type
    string_cols = ["transaction_id", "customer_id", "transaction_type", "status",
                   "category", "channel", "payment_method", "merchant", "location", "currency"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype("object")

    return df
