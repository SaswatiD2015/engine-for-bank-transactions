"""
FastAPI Metrics API
====================
REST API serving pre-computed metrics from the centralized metrics library.
Architecture §8 — API Design (Metrics Service)
All endpoints are read-only and return pre-computed, filtered aggregates.
"""

import os
import sys
from typing import Optional, List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from src.pipeline import run_pipeline
from src.metrics.metrics import (
    kpi_summary,
    amount_statistics,
    frequency_by,
    customer_activity,
    time_patterns,
    category_breakdown,
    iqr_outliers,
    data_quality_summary,
)

# ── App Setup ──────────────────────────────────────────────────────

app = FastAPI(
    title="Bank Transaction Analytics API",
    description="REST API for Bank Transaction Descriptive Analytics. "
                "Serves pre-computed metrics from the centralized metrics library.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Data Loading ───────────────────────────────────────────────────

_pipeline_result = None
_df = None
_quarantined = None


def get_data():
    """Load and cache the processed data."""
    global _pipeline_result, _df, _quarantined

    if _df is None:
        data_path = os.path.join(PROJECT_ROOT, "data", "sample", "transactions.csv")
        if not os.path.exists(data_path):
            raise HTTPException(
                status_code=404,
                detail="No data file found. Run `python src/generate_dataset.py` first."
            )
        _pipeline_result = run_pipeline(data_path)
        if not _pipeline_result.success:
            raise HTTPException(status_code=500, detail=_pipeline_result.error_message)
        _df = _pipeline_result.data
        _quarantined = _pipeline_result.quarantined

    return _df, _quarantined


def apply_filters(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[List[str]] = None,
    category: Optional[List[str]] = None,
    status: Optional[List[str]] = None,
    channel: Optional[List[str]] = None,
    payment_method: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Apply query parameter filters to DataFrame."""
    filtered = df.copy()

    if start_date and "transaction_date" in filtered.columns:
        filtered = filtered[filtered["transaction_date"] >= pd.Timestamp(start_date)]
    if end_date and "transaction_date" in filtered.columns:
        filtered = filtered[filtered["transaction_date"] <= pd.Timestamp(end_date)]
    if transaction_type and "transaction_type" in filtered.columns:
        filtered = filtered[filtered["transaction_type"].isin(transaction_type)]
    if category and "category" in filtered.columns:
        filtered = filtered[filtered["category"].isin(category)]
    if status and "status" in filtered.columns:
        filtered = filtered[filtered["status"].isin(status)]
    if channel and "channel" in filtered.columns:
        filtered = filtered[filtered["channel"].isin(channel)]
    if payment_method and "payment_method" in filtered.columns:
        filtered = filtered[filtered["payment_method"].isin(payment_method)]

    return filtered


# ── Endpoints (Architecture §8) ───────────────────────────────────

@app.get("/api/v1/kpis")
def get_kpis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[List[str]] = Query(None),
    category: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    channel: Optional[List[str]] = Query(None),
    payment_method: Optional[List[str]] = Query(None),
):
    """Executive KPI summary (PRD §19)."""
    df, _ = get_data()
    filtered = apply_filters(df, start_date, end_date, transaction_type,
                             category, status, channel, payment_method)
    return kpi_summary(filtered)


@app.get("/api/v1/amount-stats")
def get_amount_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    transaction_type: Optional[List[str]] = Query(None),
    category: Optional[List[str]] = Query(None),
):
    """Full amount statistics + percentiles + IQR."""
    df, _ = get_data()
    filtered = apply_filters(df, start_date, end_date, transaction_type, category)
    return amount_statistics(filtered)


@app.get("/api/v1/frequency")
def get_frequency(
    dimension: str = Query("transaction_month", description="Grouping dimension"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Transaction frequency by dimension."""
    df, _ = get_data()
    filtered = apply_filters(df, start_date, end_date)
    result = frequency_by(filtered, dimension)
    return result.to_dict(orient="records")


@app.get("/api/v1/customers")
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("transaction_count", description="Sort field"),
    sort_order: str = Query("desc", description="asc or desc"),
):
    """Paged customer_metrics (anonymous IDs only)."""
    df, _ = get_data()
    customers = customer_activity(df)

    if sort_by in customers.columns:
        ascending = sort_order.lower() == "asc"
        customers = customers.sort_values(sort_by, ascending=ascending)

    total = len(customers)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = customers.iloc[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": page_data.to_dict(orient="records"),
    }


@app.get("/api/v1/time-patterns")
def get_time_patterns(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Weekday/hour distribution for heatmap."""
    df, _ = get_data()
    filtered = apply_filters(df, start_date, end_date)
    tp = time_patterns(filtered)
    return {
        k: v.to_dict(orient="records") if isinstance(v, pd.DataFrame) and not v.empty else []
        for k, v in tp.items()
    }


@app.get("/api/v1/categories")
def get_categories(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Category/channel/payment-method breakdown."""
    df, _ = get_data()
    filtered = apply_filters(df, start_date, end_date)
    breakdown = category_breakdown(filtered)
    return {
        k: v.to_dict(orient="records") if isinstance(v, pd.DataFrame) and not v.empty else []
        for k, v in breakdown.items()
    }


@app.get("/api/v1/outliers")
def get_outliers(
    group_by: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """IQR-flagged transactions for analytical review."""
    df, _ = get_data()
    filtered = apply_filters(df, start_date, end_date)
    outliers = iqr_outliers(filtered, group_by=group_by)
    return outliers.to_dict(orient="records") if not outliers.empty else []


@app.get("/api/v1/data-quality")
def get_data_quality():
    """Missing/duplicate/invalid/excluded record counts and reasons."""
    df, quarantined = get_data()
    return data_quality_summary(df, quarantined)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}
