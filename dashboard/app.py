"""
Bank Transaction Analytics Dashboard
======================================
Main Streamlit application with global filters and multi-page navigation.
Architecture §9 — Dashboard Architecture
"""

import os
import sys
import streamlit as st
import pandas as pd

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.pipeline import run_pipeline
from src.metrics.metrics import kpi_summary

# ── Page Configuration ──────────────────────────────────────────────
st.set_page_config(
    page_title="Bank Transaction Analytics",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Premium Dark Theme ────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        background-color: #0F1923;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background-color: #1A2332;
        border-right: 1px solid #2A3A4A;
    }

    .stMetric {
        background: linear-gradient(135deg, #1A2332 0%, #243447 100%);
        border: 1px solid #2A3A4A;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }

    .stMetric label {
        color: #8899AA !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #E8E8E8 !important;
        font-weight: 600 !important;
    }

    h1, h2, h3 {
        color: #E8E8E8 !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #1A2332;
        border-radius: 8px;
        padding: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #8899AA;
        border-radius: 6px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2E86AB !important;
        color: white !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #2A3A4A;
        border-radius: 8px;
    }

    .dashboard-title {
        background: linear-gradient(90deg, #2E86AB, #F6511D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        color: #8899AA;
        font-size: 0.95rem;
        margin-top: -8px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading and processing data...")
def load_and_process_data(file_path: str):
    """Load and process the transaction data through the pipeline."""
    result = run_pipeline(file_path)
    return result


def get_default_data_path():
    """Get the default sample data path."""
    return os.path.join(PROJECT_ROOT, "data", "sample", "transactions.csv")


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply global filters to the DataFrame."""
    filtered = df.copy()

    if filters.get("date_range") and "transaction_date" in filtered.columns:
        start, end = filters["date_range"]
        filtered = filtered[
            (filtered["transaction_date"] >= pd.Timestamp(start)) &
            (filtered["transaction_date"] <= pd.Timestamp(end))
        ]

    if filters.get("transaction_type") and "transaction_type" in filtered.columns:
        filtered = filtered[filtered["transaction_type"].isin(filters["transaction_type"])]

    if filters.get("category") and "category" in filtered.columns:
        filtered = filtered[filtered["category"].isin(filters["category"])]

    if filters.get("status") and "status" in filtered.columns:
        filtered = filtered[filtered["status"].isin(filters["status"])]

    if filters.get("channel") and "channel" in filtered.columns:
        filtered = filtered[filtered["channel"].isin(filters["channel"])]

    if filters.get("payment_method") and "payment_method" in filtered.columns:
        filtered = filtered[filtered["payment_method"].isin(filters["payment_method"])]

    return filtered


def main():
    """Main dashboard application."""

    # ── Header ──────────────────────────────────────────────────────
    st.markdown('<p class="dashboard-title">🏦 Bank Transaction Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Descriptive Analytics Dashboard — Amount, Frequency & Customer Activity Analysis</p>', unsafe_allow_html=True)
    st.markdown("---")

    # ── Data Loading ────────────────────────────────────────────────
    default_path = get_default_data_path()

    with st.sidebar:
        st.markdown("### 📂 Data Source")

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload transaction file",
            type=["csv", "xlsx", "xls"],
            help="Upload a CSV or Excel file with transaction data",
        )

        if uploaded_file:
            # Save uploaded file temporarily
            temp_path = os.path.join(PROJECT_ROOT, "data", "raw", uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            data_path = temp_path
        elif os.path.exists(default_path):
            data_path = default_path
        else:
            st.error("No data file found. Please upload a file or generate sample data.")
            st.code("python src/generate_dataset.py", language="bash")
            st.stop()

    # Load data
    pipeline_result = load_and_process_data(data_path)

    if not pipeline_result.success:
        st.error(f"Pipeline failed: {pipeline_result.error_message}")
        st.stop()

    df = pipeline_result.data

    # ── Sidebar Filters (Architecture §9 — Global Filter Shell) ────
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔍 Global Filters")

        filters = {}

        # Date range
        if "transaction_date" in df.columns:
            min_date = df["transaction_date"].min().date()
            max_date = df["transaction_date"].max().date()
            date_range = st.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
            if len(date_range) == 2:
                filters["date_range"] = date_range

        # Transaction type
        if "transaction_type" in df.columns:
            types = sorted(df["transaction_type"].dropna().unique())
            selected_types = st.multiselect("Transaction Type", types, default=None)
            if selected_types:
                filters["transaction_type"] = selected_types

        # Category
        if "category" in df.columns:
            categories = sorted(df["category"].dropna().unique())
            selected_cats = st.multiselect("Category", categories, default=None)
            if selected_cats:
                filters["category"] = selected_cats

        # Status
        if "status" in df.columns:
            statuses = sorted(df["status"].dropna().unique())
            selected_status = st.multiselect("Status", statuses, default=None)
            if selected_status:
                filters["status"] = selected_status

        # Channel
        if "channel" in df.columns:
            channels = sorted(df["channel"].dropna().unique())
            selected_channels = st.multiselect("Channel", channels, default=None)
            if selected_channels:
                filters["channel"] = selected_channels

        # Payment method
        if "payment_method" in df.columns:
            methods = sorted(df["payment_method"].dropna().unique())
            selected_methods = st.multiselect("Payment Method", methods, default=None)
            if selected_methods:
                filters["payment_method"] = selected_methods

        st.markdown("---")
        st.markdown(f"**Active Filters:** {len(filters)}")
        if st.button("🔄 Clear All Filters"):
            filters = {}
            st.rerun()

    # Apply filters
    filtered_df = apply_filters(df, filters)

    if len(filtered_df) == 0:
        st.warning("No data matches the current filters. Try adjusting your filters.")
        st.stop()

    # Store in session state for pages
    st.session_state["df"] = df
    st.session_state["filtered_df"] = filtered_df
    st.session_state["pipeline_result"] = pipeline_result
    st.session_state["filters"] = filters

    # Show filter status
    if filters:
        st.info(f"📊 Showing {len(filtered_df):,} of {len(df):,} transactions ({len(filtered_df)/len(df)*100:.1f}%)")

    # ── Quick KPI Summary on Main Page ──────────────────────────────
    kpis = kpi_summary(filtered_df)

    cols = st.columns(6)
    with cols[0]:
        st.metric("Total Transactions", f"{kpis['total_transactions']:,}")
    with cols[1]:
        st.metric("Total Value", f"₹{kpis['total_value']:,.0f}")
    with cols[2]:
        st.metric("Avg Value", f"₹{kpis['avg_value']:,.0f}")
    with cols[3]:
        st.metric("Median Value", f"₹{kpis['median_value']:,.0f}")
    with cols[4]:
        st.metric("Active Customers", f"{kpis['active_customers']:,}")
    with cols[5]:
        st.metric("Txn/Customer", f"{kpis['txn_per_customer']:.1f}")

    st.markdown("---")
    st.markdown("👈 **Navigate** to analysis pages using the sidebar menu.")
    st.markdown("""
    | Page | Description |
    |---|---|
    | 📊 **Executive Overview** | KPI cards, monthly trends, top categories |
    | 💰 **Transaction Analysis** | Amount distributions, box plots, outliers |
    | 👥 **Customer Activity** | Customer distributions, top customers |
    | 🕐 **Time & Behavior** | Heatmaps, weekday/weekend, hourly patterns |
    """)


if __name__ == "__main__":
    main()
