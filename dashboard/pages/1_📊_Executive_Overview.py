"""
Page 1 — Executive Overview
=============================
KPI cards, monthly trend chart, top categories, channel distribution.
Architecture §9 — Dashboard Page 1.
"""

import os
import sys
import streamlit as st
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.metrics.metrics import kpi_summary, amount_statistics, category_breakdown, time_patterns
from src.visualization.charts import (
    monthly_trend, category_bar_chart, donut_chart, status_pie_chart,
)

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")

st.markdown("## 📊 Executive Overview")
st.markdown("---")

# Get filtered data from session state
if "filtered_df" not in st.session_state:
    st.warning("Please navigate to the main dashboard first to load data.")
    st.stop()

df = st.session_state["filtered_df"]

# ── KPI Cards ──────────────────────────────────────────────────────
kpis = kpi_summary(df)

col1, col2, col3, col4, col5, col6 = st.columns(6)
with col1:
    st.metric("Total Transactions", f"{kpis['total_transactions']:,}")
with col2:
    st.metric("Total Value", f"₹{kpis['total_value']:,.0f}")
with col3:
    st.metric("Average Value", f"₹{kpis['avg_value']:,.0f}")
with col4:
    st.metric("Median Value", f"₹{kpis['median_value']:,.0f}")
with col5:
    st.metric("Active Customers", f"{kpis['active_customers']:,}")
with col6:
    st.metric("Txn / Customer", f"{kpis['txn_per_customer']:.1f}")

st.markdown("---")

# ── Additional KPIs Row ────────────────────────────────────────────
stats = amount_statistics(df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("95th Percentile", f"₹{kpis['p95_amount']:,.0f}")
with col2:
    st.metric("Std Deviation", f"₹{stats.get('std', 0):,.0f}")
with col3:
    if kpis['date_range_start']:
        st.metric("Date Range Start", kpis['date_range_start'])
with col4:
    if kpis['date_range_end']:
        st.metric("Date Range End", kpis['date_range_end'])

st.markdown("---")

# ── Monthly Trend Chart ────────────────────────────────────────────
st.markdown("### 📈 Monthly Transaction Trend")
tp = time_patterns(df)
if not tp["monthly"].empty:
    fig = monthly_trend(tp["monthly"])
    st.plotly_chart(fig, use_container_width=True)

# ── Category and Channel Analysis ──────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 🏷️ Top Categories by Volume")
    breakdown = category_breakdown(df)
    if not breakdown["category"].empty:
        fig = category_bar_chart(
            breakdown["category"],
            value_col="txn_count",
            title="Top 10 Categories by Transaction Count",
        )
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("### 📡 Channel Distribution")
    if not breakdown["channel"].empty:
        fig = donut_chart(
            breakdown["channel"],
            names_col="channel",
            values_col="txn_count",
            title="Transaction Channel Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Status and Payment Method ──────────────────────────────────────
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.markdown("### 🔄 Transaction Status")
    fig = status_pie_chart(df)
    st.plotly_chart(fig, use_container_width=True)

with col_right2:
    st.markdown("### 💳 Payment Methods")
    if not breakdown["payment_method"].empty:
        fig = donut_chart(
            breakdown["payment_method"],
            names_col="payment_method",
            values_col="txn_count",
            title="Payment Method Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)
