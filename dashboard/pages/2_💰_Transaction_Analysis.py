"""
Page 2 — Transaction Analysis
================================
Amount distributions, descriptive statistics, box plots, outlier review.
Architecture §9 — Dashboard Page 2.
"""

import os
import sys
import streamlit as st
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from src.metrics.metrics import amount_statistics, iqr_outliers, category_breakdown
from src.visualization.charts import amount_histogram, amount_box_plot, status_pie_chart

st.set_page_config(page_title="Transaction Analysis", page_icon="💰", layout="wide")

st.markdown("## 💰 Transaction Analysis")
st.markdown("---")

if "filtered_df" not in st.session_state:
    st.warning("Please navigate to the main dashboard first to load data.")
    st.stop()

df = st.session_state["filtered_df"]

# ── Amount Distribution Histogram ──────────────────────────────────
st.markdown("### 📊 Amount Distribution")
fig = amount_histogram(df)
st.plotly_chart(fig, use_container_width=True)

# ── Descriptive Statistics Table ───────────────────────────────────
st.markdown("### 📋 Descriptive Statistics")
stats = amount_statistics(df)

if stats:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**Central Tendency**")
        st.markdown(f"- Mean: **₹{stats['mean']:,.2f}**")
        st.markdown(f"- Median: **₹{stats['median']:,.2f}**")
        st.markdown(f"- Mode: **₹{stats.get('mode', 'N/A')}**" if stats.get('mode') else "- Mode: N/A")

    with col2:
        st.markdown("**Dispersion**")
        st.markdown(f"- Std Dev: **₹{stats['std']:,.2f}**")
        st.markdown(f"- Variance: **₹{stats['variance']:,.2f}**")
        st.markdown(f"- IQR: **₹{stats['iqr']:,.2f}**")
        st.markdown(f"- Range: **₹{stats['range']:,.2f}**")

    with col3:
        st.markdown("**Quartiles**")
        st.markdown(f"- Q1 (25th): **₹{stats['q1']:,.2f}**")
        st.markdown(f"- Q2 (50th): **₹{stats['q2']:,.2f}**")
        st.markdown(f"- Q3 (75th): **₹{stats['q3']:,.2f}**")

    with col4:
        st.markdown("**Percentiles**")
        st.markdown(f"- P90: **₹{stats['p90']:,.2f}**")
        st.markdown(f"- P95: **₹{stats['p95']:,.2f}**")
        st.markdown(f"- P99: **₹{stats['p99']:,.2f}**")

    st.markdown("---")

    # Distribution shape
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Skewness", f"{stats['skewness']:.4f}")
    with col2:
        st.metric("Kurtosis", f"{stats['kurtosis']:.4f}")
    with col3:
        cv = stats.get('coefficient_of_variation')
        st.metric("CV (%)", f"{cv:.2f}%" if cv else "N/A")

st.markdown("---")

# ── Box Plot by Transaction Type ───────────────────────────────────
st.markdown("### 📦 Amount Distribution by Group")

group_col = st.selectbox(
    "Group by",
    ["transaction_type", "category", "channel", "status", "payment_method"],
    index=0,
    help="Select the grouping dimension for the box plot"
)

fig = amount_box_plot(df, group_col=group_col)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ── Transaction Type Breakdown Table ───────────────────────────────
st.markdown("### 📊 Transaction Type Breakdown")
breakdown = category_breakdown(df)
if not breakdown["transaction_type"].empty:
    st.dataframe(
        breakdown["transaction_type"].style.format({
            "total_amount": "₹{:,.2f}",
            "avg_amount": "₹{:,.2f}",
            "median_amount": "₹{:,.2f}",
            "pct_of_total_count": "{:.1f}%",
        }),
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# ── Outlier Review ─────────────────────────────────────────────────
st.markdown("### 🔍 Outlier Review (IQR Method)")
st.caption("⚠️ These are statistical outliers flagged for **analytical review only**. "
           "They are **not** evidence of fraud or suspicious behavior.")

outlier_group = st.selectbox(
    "Compute outliers within groups of",
    [None, "transaction_type", "category", "channel"],
    index=0,
    format_func=lambda x: "Overall" if x is None else x.replace("_", " ").title(),
)

outliers = iqr_outliers(df, group_by=outlier_group)

if not outliers.empty:
    st.info(f"Found **{len(outliers):,}** statistical outliers ({len(outliers)/len(df)*100:.2f}% of transactions)")
    st.dataframe(
        outliers.head(100),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success("No statistical outliers detected with current settings.")
