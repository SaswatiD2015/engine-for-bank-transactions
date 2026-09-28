"""
Page 4 — Time & Behavior
===========================
Heatmaps, weekday/weekend comparison, hourly patterns, monthly trends.
Architecture §9 — Dashboard Page 4.
"""

import os
import sys
import streamlit as st
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.metrics.metrics import time_patterns
from src.visualization.charts import (
    time_heatmap, weekday_weekend_chart, monthly_trend,
    hourly_bar_chart, day_of_week_chart,
)

st.set_page_config(page_title="Time & Behavior", page_icon="🕐", layout="wide")

st.markdown("## 🕐 Time & Behavior Analysis")
st.markdown("---")

if "filtered_df" not in st.session_state:
    st.warning("Please navigate to the main dashboard first to load data.")
    st.stop()

df = st.session_state["filtered_df"]

# ── Compute Time Patterns ─────────────────────────────────────────
tp = time_patterns(df)

# ── Heatmap: Day × Hour ──────────────────────────────────────────
st.markdown("### 🗓️ Transaction Activity Heatmap")
st.caption("Shows transaction volume across day-of-week and hour-of-day combinations.")

if not tp["heatmap"].empty:
    fig = time_heatmap(tp["heatmap"])
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Monthly Trend ─────────────────────────────────────────────────
st.markdown("### 📈 Monthly Transaction Trend")

if not tp["monthly"].empty:
    fig = monthly_trend(tp["monthly"])
    st.plotly_chart(fig, use_container_width=True)

    # Monthly data table
    with st.expander("📋 View Monthly Data Table"):
        display_cols = [c for c in [
            "year_month", "txn_count", "txn_value", "avg_value",
            "distinct_customers", "transaction_month_name"
        ] if c in tp["monthly"].columns]
        st.dataframe(
            tp["monthly"][display_cols],
            use_container_width=True,
            hide_index=True,
        )

st.markdown("---")

# ── Day of Week and Hourly ────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 📅 Transactions by Day of Week")
    fig = day_of_week_chart(df)
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.markdown("### ⏰ Transactions by Hour of Day")
    if not tp["hourly"].empty:
        fig = hourly_bar_chart(tp["hourly"])
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Weekday vs Weekend ────────────────────────────────────────────
st.markdown("### 📊 Weekday vs Weekend Comparison")

if not tp["weekday_weekend"].empty:
    ww = tp["weekday_weekend"]

    col1, col2, col3, col4 = st.columns(4)

    weekday_data = ww[ww["day_type"] == "Weekday"]
    weekend_data = ww[ww["day_type"] == "Weekend"]

    if not weekday_data.empty and not weekend_data.empty:
        with col1:
            st.metric("Weekday Transactions", f"{int(weekday_data['txn_count'].iloc[0]):,}")
        with col2:
            st.metric("Weekend Transactions", f"{int(weekend_data['txn_count'].iloc[0]):,}")
        with col3:
            st.metric("Weekday Avg Value", f"₹{weekday_data['avg_value'].iloc[0]:,.0f}")
        with col4:
            st.metric("Weekend Avg Value", f"₹{weekend_data['avg_value'].iloc[0]:,.0f}")

    fig = weekday_weekend_chart(ww)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Daily Metrics Table ───────────────────────────────────────────
st.markdown("### 📋 Daily Transaction Summary")

if not tp["daily"].empty:
    with st.expander("View daily metrics (click to expand)"):
        st.dataframe(
            tp["daily"].sort_values("date", ascending=False).head(60),
            use_container_width=True,
            hide_index=True,
        )
