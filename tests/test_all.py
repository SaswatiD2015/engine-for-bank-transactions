"""
Test Suite — Schema Validation, Data Quality, Metrics, KPI Reconciliation
==========================================================================
Architecture — Testing (Phase 10)
PRD §23 — Success Criteria
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.ingestion.schema_validator import validate_schema, coerce_types
from src.cleaning.dedupe import remove_duplicates
from src.cleaning.null_handler import handle_null_and_invalid
from src.cleaning.normalizer import normalize_data
from src.analytics.derived_fields import add_derived_fields
from src.metrics.metrics import (
    amount_statistics, kpi_summary, iqr_outliers,
    frequency_by, customer_activity, category_breakdown,
)


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def sample_df():
    """Create a small, known test dataset."""
    return pd.DataFrame({
        "transaction_id": ["TXN-001", "TXN-002", "TXN-003", "TXN-004", "TXN-005"],
        "customer_id": ["CUST-01", "CUST-01", "CUST-02", "CUST-02", "CUST-03"],
        "transaction_date": pd.to_datetime([
            "2024-01-15 10:00:00", "2024-01-16 14:00:00",
            "2024-02-01 09:00:00", "2024-02-15 16:00:00",
            "2024-03-01 11:00:00",
        ]),
        "amount": [1000.0, 2000.0, 500.0, 1500.0, 3000.0],
        "transaction_type": ["Deposit", "Payment", "Withdrawal", "Transfer", "Deposit"],
        "status": ["Completed", "Completed", "Completed", "Failed", "Completed"],
        "category": ["Salary", "Shopping", "Food & Dining", "Rent", "Salary"],
        "channel": ["Mobile", "Web", "ATM", "Branch", "Mobile"],
        "payment_method": ["UPI", "Card", "Cash", "Bank Transfer", "UPI"],
        "currency": ["INR", "INR", "INR", "INR", "INR"],
    })


@pytest.fixture
def processed_df(sample_df):
    """Sample df with derived fields added."""
    return add_derived_fields(sample_df)


# ══════════════════════════════════════════════════════════════════
# TEST: Schema Validation
# ══════════════════════════════════════════════════════════════════

class TestSchemaValidation:
    """Tests for src/ingestion/schema_validator.py"""

    def test_valid_schema(self, sample_df):
        """Valid dataset should pass validation."""
        report = validate_schema(sample_df)
        assert report.is_valid is True
        assert report.total_rows == 5
        assert len(report.missing_required) == 0

    def test_missing_required_column(self, sample_df):
        """Missing required column should fail validation."""
        df = sample_df.drop(columns=["amount"])
        report = validate_schema(df)
        assert report.is_valid is False
        assert "amount" in report.missing_required

    def test_empty_dataset(self):
        """Empty dataset should fail validation."""
        df = pd.DataFrame()
        report = validate_schema(df)
        assert report.is_valid is False

    def test_missing_recommended_column(self, sample_df):
        """Missing recommended column should warn but not fail."""
        df = sample_df.drop(columns=["transaction_type"])
        report = validate_schema(df)
        assert report.is_valid is True
        assert "transaction_type" in report.missing_recommended

    def test_null_transaction_id_warning(self, sample_df):
        """Null transaction_id should generate a warning."""
        df = sample_df.copy()
        df.loc[0, "transaction_id"] = None
        report = validate_schema(df)
        assert report.null_counts.get("transaction_id", 0) == 1


# ══════════════════════════════════════════════════════════════════
# TEST: Data Quality (Deduplication)
# ══════════════════════════════════════════════════════════════════

class TestDedupe:
    """Tests for src/cleaning/dedupe.py"""

    def test_no_duplicates(self, sample_df):
        """Clean data should have no duplicates removed."""
        result = remove_duplicates(sample_df)
        assert result.total_removed == 0
        assert len(result.data) == 5

    def test_duplicate_transaction_id(self, sample_df):
        """Duplicate transaction_id should be removed."""
        df = sample_df.copy()
        df.loc[4, "transaction_id"] = "TXN-001"  # Duplicate
        result = remove_duplicates(df)
        assert result.duplicate_id_count == 1
        assert len(result.data) == 4

    def test_exact_duplicate_row(self, sample_df):
        """Exact duplicate rows should be removed."""
        df = pd.concat([sample_df, sample_df.iloc[[0]]], ignore_index=True)
        result = remove_duplicates(df)
        assert result.exact_duplicate_count == 1


# ══════════════════════════════════════════════════════════════════
# TEST: Data Quality (Null Handling)
# ══════════════════════════════════════════════════════════════════

class TestNullHandler:
    """Tests for src/cleaning/null_handler.py"""

    def test_null_amount_quarantined(self, sample_df):
        """Null amounts should be quarantined."""
        df = sample_df.copy()
        df.loc[0, "amount"] = np.nan
        result = handle_null_and_invalid(df)
        assert result.cleaning_summary["null_amount"] == 1
        assert len(result.quarantined) == 1

    def test_future_date_flagged(self, sample_df):
        """Future dates should be flagged."""
        df = sample_df.copy()
        df.loc[0, "transaction_date"] = pd.Timestamp("2030-01-01")
        result = handle_null_and_invalid(df, max_valid_date="2025-12-31")
        assert result.cleaning_summary["future_date"] == 1

    def test_null_customer_id_kept(self, sample_df):
        """Null customer_id rows should be kept but flagged."""
        df = sample_df.copy()
        df.loc[0, "customer_id"] = np.nan
        result = handle_null_and_invalid(df)
        assert result.cleaning_summary["null_customer_id"] == 1
        assert len(result.data) == 5  # Row is kept


# ══════════════════════════════════════════════════════════════════
# TEST: Normalizer
# ══════════════════════════════════════════════════════════════════

class TestNormalizer:
    """Tests for src/cleaning/normalizer.py"""

    def test_category_normalization(self, sample_df):
        """Category typos should be normalized."""
        df = sample_df.copy()
        df.loc[0, "category"] = "  salary  "
        df.loc[1, "category"] = "SHOPPING"
        result = normalize_data(df)
        assert result.data.loc[0, "category"] == "Salary"
        assert result.data.loc[1, "category"] == "Shopping"


# ══════════════════════════════════════════════════════════════════
# TEST: Metrics Accuracy
# ══════════════════════════════════════════════════════════════════

class TestMetrics:
    """Tests for src/metrics/metrics.py — manually verified calculations."""

    def test_amount_statistics(self, processed_df):
        """Amount statistics should match manual calculations."""
        stats = amount_statistics(processed_df)
        amounts = processed_df["absolute_amount"].dropna()

        assert stats["count"] == 5
        assert stats["sum"] == pytest.approx(amounts.sum(), rel=1e-2)
        assert stats["mean"] == pytest.approx(amounts.mean(), rel=1e-2)
        assert stats["median"] == pytest.approx(amounts.median(), rel=1e-2)
        assert stats["min"] == pytest.approx(amounts.min(), rel=1e-2)
        assert stats["max"] == pytest.approx(amounts.max(), rel=1e-2)

    def test_kpi_summary(self, processed_df):
        """KPI summary values should match direct calculations."""
        kpis = kpi_summary(processed_df)

        assert kpis["total_transactions"] == 5
        assert kpis["active_customers"] == 3
        assert kpis["txn_per_customer"] == pytest.approx(5 / 3, rel=1e-2)

    def test_customer_activity(self, processed_df):
        """Customer activity should correctly group by customer."""
        customers = customer_activity(processed_df)
        assert len(customers) == 3  # 3 unique customers

        cust_01 = customers[customers["customer_id"] == "CUST-01"]
        assert cust_01["transaction_count"].iloc[0] == 2

    def test_iqr_outliers_no_crash(self, processed_df):
        """IQR outlier detection should not crash on small data."""
        outliers = iqr_outliers(processed_df)
        assert isinstance(outliers, pd.DataFrame)

    def test_frequency_by(self, processed_df):
        """Frequency grouping should work for valid dimensions."""
        result = frequency_by(processed_df, "transaction_type")
        assert len(result) > 0
        assert "txn_count" in result.columns

    def test_category_breakdown(self, processed_df):
        """Category breakdown should return all sub-breakdowns."""
        breakdown = category_breakdown(processed_df)
        assert "category" in breakdown
        assert "channel" in breakdown
        assert "transaction_type" in breakdown


# ══════════════════════════════════════════════════════════════════
# TEST: KPI Reconciliation (PRD §23)
# ══════════════════════════════════════════════════════════════════

class TestKPIReconciliation:
    """Verify dashboard KPIs match underlying analytical functions."""

    def test_kpi_matches_amount_stats(self, processed_df):
        """KPI avg/median should match amount_statistics."""
        kpis = kpi_summary(processed_df)
        stats = amount_statistics(processed_df)

        assert kpis["avg_value"] == pytest.approx(stats["mean"], rel=1e-2)
        assert kpis["median_value"] == pytest.approx(stats["median"], rel=1e-2)
        assert kpis["p95_amount"] == pytest.approx(stats["p95"], rel=1e-2)

    def test_total_transactions_consistent(self, processed_df):
        """Total transactions should be consistent across functions."""
        kpis = kpi_summary(processed_df)
        stats = amount_statistics(processed_df)

        assert kpis["total_transactions"] == stats["count"]

    def test_reproducibility(self, processed_df):
        """Same input should produce identical results."""
        kpis_1 = kpi_summary(processed_df)
        kpis_2 = kpi_summary(processed_df)

        for key in kpis_1:
            assert kpis_1[key] == kpis_2[key], f"KPI '{key}' differs between runs"


# ══════════════════════════════════════════════════════════════════
# TEST: Edge Cases
# ══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test edge cases: empty data, single row, etc."""

    def test_single_row(self):
        """Single row should not crash any function."""
        df = pd.DataFrame({
            "transaction_id": ["TXN-001"],
            "customer_id": ["CUST-01"],
            "transaction_date": [pd.Timestamp("2024-01-15 10:00:00")],
            "amount": [1000.0],
        })
        df = add_derived_fields(df)
        kpis = kpi_summary(df)
        assert kpis["total_transactions"] == 1

    def test_all_same_amount(self):
        """All identical amounts should give zero std dev."""
        df = pd.DataFrame({
            "transaction_id": [f"TXN-{i}" for i in range(10)],
            "customer_id": ["CUST-01"] * 10,
            "transaction_date": pd.date_range("2024-01-01", periods=10, freq="D"),
            "amount": [500.0] * 10,
        })
        df = add_derived_fields(df)
        stats = amount_statistics(df)
        assert stats["std"] == 0.0
        assert stats["iqr"] == 0.0
