"""
Page 3 — Customer Activity
=============================
Customer distributions, top customers, concentration analysis.
Architecture §9 — Dashboard Page 3.
"""

import os
import sys
import streamlit as st
import pandas as pd
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.metrics.metrics import customer_activity, kpi_summary
from src.visualization.charts import customer_distribution

st.set_page_config(page_title="Customer Activity", page_icon="👥", layout="wide")

st.markdown("## 👥 Customer Activity Analysis")
st.markdown("---")

if "filtered_df" not in st.session_state:
    st.warning("Please navigate to the main dashboard first to load data.")
    st.stop()

df = st.session_state["filtered_df"]

# ── Customer KPIs ──────────────────────────────────────────────────
kpis = kpi_summary(df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Active Customers", f"{kpis['active_customers']:,}")
with col2:
    st.metric("Avg Txn/Customer", f"{kpis['txn_per_customer']:.1f}")
with col3:
    st.metric("Avg Customer Value", f"₹{kpis['avg_customer_value']:,.0f}")
with col4:
    st.metric("Total Transactions", f"{kpis['total_transactions']:,}")

st.markdown("---")

# ── Customer Metrics Table ─────────────────────────────────────────
customer_df = customer_activity(df)

if customer_df.empty:
    st.warning("No customer data available for analysis.")
    st.stop()

# ── Distribution Charts ────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📊 Transactions per Customer Distribution")
    fig = customer_distribution(customer_df, col="transaction_count")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("### 💰 Total Value per Customer Distribution")
    fig = customer_distribution(customer_df, col="total_value")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Additional Distributions ──────────────────────────────────────
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.markdown("### 📅 Active Days per Customer")
    if "active_days" in customer_df.columns:
        fig = customer_distribution(customer_df, col="active_days")
        st.plotly_chart(fig, use_container_width=True)

with col_right2:
    st.markdown("### 📈 Average Value per Customer")
    if "avg_value" in customer_df.columns:
        fig = customer_distribution(customer_df, col="avg_value")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Top 20 Most Active Customers ──────────────────────────────────
st.markdown("### 🏆 Top 20 Most Active Customers")
st.caption("Customer IDs are pseudonymous as per privacy policy.")

top_customers = customer_df.nlargest(20, "transaction_count")
display_cols = [c for c in [
    "customer_id", "transaction_count", "total_value", "avg_value",
    "median_value", "active_days", "first_transaction", "last_transaction",
] if c in top_customers.columns]

st.dataframe(
    top_customers[display_cols],
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

# ── Customer Concentration Analysis ───────────────────────────────
st.markdown("### 📊 Customer Concentration Analysis")
st.caption("Shows what percentage of total transaction value is driven by the top N% of customers.")

if "total_value" in customer_df.columns:
    sorted_customers = customer_df.sort_values("total_value", ascending=False)
    sorted_customers["cumulative_value"] = sorted_customers["total_value"].cumsum()
    total = sorted_customers["total_value"].sum()
    sorted_customers["cumulative_pct"] = (sorted_customers["cumulative_value"] / total * 100)
    sorted_customers["customer_pct"] = np.arange(1, len(sorted_customers) + 1) / len(sorted_customers) * 100

    # Key concentration stats
    col1, col2, col3 = st.columns(3)

    top_10_pct = sorted_customers.iloc[:int(len(sorted_customers) * 0.10)]["total_value"].sum() / total * 100
    top_20_pct = sorted_customers.iloc[:int(len(sorted_customers) * 0.20)]["total_value"].sum() / total * 100
    top_50_pct = sorted_customers.iloc[:int(len(sorted_customers) * 0.50)]["total_value"].sum() / total * 100

    with col1:
        st.metric("Top 10% Customers", f"{top_10_pct:.1f}% of Value")
    with col2:
        st.metric("Top 20% Customers", f"{top_20_pct:.1f}% of Value")
    with col3:
        st.metric("Top 50% Customers", f"{top_50_pct:.1f}% of Value")

st.markdown("---")

# ── Customer Summary Statistics ───────────────────────────────────
st.markdown("### 📋 Customer Activity Summary Statistics")

summary_cols = ["transaction_count", "total_value", "avg_value", "active_days"]
summary_cols = [c for c in summary_cols if c in customer_df.columns]

if summary_cols:
    summary = customer_df[summary_cols].describe().round(2)
    st.dataframe(summary, use_container_width=True)
