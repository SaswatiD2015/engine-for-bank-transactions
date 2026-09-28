"""
Visualization Charts Module
=============================
Chart-building functions using Plotly that accept outputs of
src/metrics functions directly. A chart can never disagree with
a KPI card number.
Architecture §4.5 — src/visualization/charts.py
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ── Color Palette ────────────────────────────────────────────────────
COLORS = {
    "primary": "#1B2A4A",
    "secondary": "#2E86AB",
    "accent": "#F6511D",
    "success": "#00B894",
    "warning": "#FDCB6E",
    "danger": "#E74C3C",
    "info": "#74B9FF",
    "background": "#0F1923",
    "card_bg": "#1A2332",
    "text": "#E8E8E8",
    "text_secondary": "#8899AA",
    "grid": "#2A3A4A",
}

PALETTE = [
    "#2E86AB", "#F6511D", "#00B894", "#FDCB6E", "#74B9FF",
    "#E74C3C", "#A29BFE", "#FD79A8", "#00CEC9", "#636E72",
    "#D63031", "#6C5CE7", "#00B894", "#E17055", "#81ECEC",
]

CHART_TEMPLATE = "plotly_dark"


def _apply_layout(fig, title: str, height: int = 450):
    """Apply consistent dark theme styling to a figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=COLORS["text"])),
        template=CHART_TEMPLATE,
        plot_bgcolor=COLORS["background"],
        paper_bgcolor=COLORS["card_bg"],
        font=dict(color=COLORS["text"], size=12),
        height=height,
        margin=dict(l=60, r=30, t=60, b=50),
        legend=dict(
            bgcolor="rgba(0,0,0,0.3)",
            bordercolor=COLORS["grid"],
            borderwidth=1,
        ),
    )
    fig.update_xaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"])
    fig.update_yaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"])
    return fig


# ── 6.2  Amount Histogram ────────────────────────────────────────────

def amount_histogram(df: pd.DataFrame, amount_col: str = "absolute_amount") -> go.Figure:
    """Create an amount distribution histogram with percentile markers."""
    if amount_col not in df.columns:
        amount_col = "amount"

    amounts = df[amount_col].dropna()

    fig = px.histogram(
        amounts,
        nbins=50,
        color_discrete_sequence=[COLORS["secondary"]],
        labels={"value": "Transaction Amount (₹)", "count": "Frequency"},
    )

    # Add percentile lines
    for pct, color, label in [
        (0.50, COLORS["success"], "Median (P50)"),
        (0.95, COLORS["accent"], "P95"),
        (0.99, COLORS["danger"], "P99"),
    ]:
        val = float(amounts.quantile(pct))
        fig.add_vline(
            x=val, line_dash="dash", line_color=color,
            annotation_text=f"{label}: ₹{val:,.0f}",
            annotation_position="top",
            annotation_font_color=color,
        )

    fig = _apply_layout(fig, "Transaction Amount Distribution")
    fig.update_xaxes(title_text="Transaction Amount (₹)")
    fig.update_yaxes(title_text="Number of Transactions")

    return fig


# ── 6.3  Box Plot ────────────────────────────────────────────────────

def amount_box_plot(
    df: pd.DataFrame,
    group_col: str = "transaction_type",
    amount_col: str = "absolute_amount",
) -> go.Figure:
    """Create a box plot showing amount distribution by group."""
    if amount_col not in df.columns:
        amount_col = "amount"

    if group_col not in df.columns:
        fig = px.box(
            df, y=amount_col,
            color_discrete_sequence=[COLORS["secondary"]],
        )
    else:
        fig = px.box(
            df, x=group_col, y=amount_col,
            color=group_col,
            color_discrete_sequence=PALETTE,
        )

    fig = _apply_layout(fig, f"Amount Distribution by {group_col.replace('_', ' ').title()}")
    fig.update_yaxes(title_text="Amount (₹)")

    return fig


# ── 6.4  Monthly Trend Line ──────────────────────────────────────────

def monthly_trend(monthly_df: pd.DataFrame) -> go.Figure:
    """Create a dual-axis monthly trend chart showing volume and value."""
    if monthly_df.empty:
        return go.Figure()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=monthly_df["year_month"],
            y=monthly_df["txn_count"],
            name="Transaction Count",
            marker_color=COLORS["secondary"],
            opacity=0.7,
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=monthly_df["year_month"],
            y=monthly_df["txn_value"],
            name="Transaction Value (₹)",
            line=dict(color=COLORS["accent"], width=3),
            mode="lines+markers",
        ),
        secondary_y=True,
    )

    fig = _apply_layout(fig, "Monthly Transaction Trend")
    fig.update_xaxes(title_text="Month", tickangle=45)
    fig.update_yaxes(title_text="Transaction Count", secondary_y=False)
    fig.update_yaxes(title_text="Transaction Value (₹)", secondary_y=True)

    return fig


# ── 6.5  Heatmap ─────────────────────────────────────────────────────

def time_heatmap(heatmap_df: pd.DataFrame) -> go.Figure:
    """Create a day-of-week × hour-of-day heatmap."""
    if heatmap_df.empty:
        return go.Figure()

    # Pivot for heatmap
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    pivot = heatmap_df.pivot_table(
        index="day_of_week",
        columns="hour",
        values="txn_count",
        aggfunc="sum",
        fill_value=0,
    )

    # Reorder days
    pivot = pivot.reindex([d for d in day_order if d in pivot.index])

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[f"{h:02d}:00" for h in pivot.columns],
        y=pivot.index,
        colorscale="Viridis",
        hoverongaps=False,
        colorbar=dict(title="Txn Count"),
    ))

    fig = _apply_layout(fig, "Transaction Activity Heatmap (Day × Hour)", height=400)
    fig.update_xaxes(title_text="Hour of Day")
    fig.update_yaxes(title_text="Day of Week")

    return fig


# ── 6.6  Category Bar Charts ─────────────────────────────────────────

def category_bar_chart(
    category_df: pd.DataFrame,
    value_col: str = "txn_count",
    title: str = "Top Categories by Transaction Count",
    top_n: int = 10,
) -> go.Figure:
    """Create a horizontal bar chart for top categories."""
    if category_df.empty:
        return go.Figure()

    top = category_df.nlargest(top_n, value_col)

    fig = px.bar(
        top,
        x=value_col,
        y="category",
        orientation="h",
        color=value_col,
        color_continuous_scale="Viridis",
        text=value_col,
    )

    fig = _apply_layout(fig, title)
    fig.update_traces(textposition="outside", texttemplate="%{text:,.0f}")
    fig.update_yaxes(categoryorder="total ascending")

    return fig


# ── 6.7  Pie / Donut Charts ──────────────────────────────────────────

def donut_chart(
    df: pd.DataFrame,
    names_col: str = "channel",
    values_col: str = "txn_count",
    title: str = "Channel Distribution",
) -> go.Figure:
    """Create a donut chart for categorical distribution."""
    if df.empty:
        return go.Figure()

    fig = go.Figure(data=[go.Pie(
        labels=df[names_col],
        values=df[values_col],
        hole=0.5,
        marker=dict(colors=PALETTE),
        textinfo="label+percent",
        textfont_size=12,
    )])

    fig = _apply_layout(fig, title)

    return fig


# ── 6.8  Customer Distribution ───────────────────────────────────────

def customer_distribution(customer_df: pd.DataFrame, col: str = "transaction_count") -> go.Figure:
    """Create a histogram of customer-level metric distribution."""
    if customer_df.empty or col not in customer_df.columns:
        return go.Figure()

    fig = px.histogram(
        customer_df,
        x=col,
        nbins=40,
        color_discrete_sequence=[COLORS["info"]],
        labels={col: col.replace("_", " ").title()},
    )

    fig = _apply_layout(fig, f"Customer {col.replace('_', ' ').title()} Distribution")
    fig.update_xaxes(title_text=col.replace("_", " ").title())
    fig.update_yaxes(title_text="Number of Customers")

    return fig


# ── 6.9  Weekday vs Weekend ──────────────────────────────────────────

def weekday_weekend_chart(comparison_df: pd.DataFrame) -> go.Figure:
    """Create a bar chart comparing weekday vs weekend metrics."""
    if comparison_df.empty:
        return go.Figure()

    fig = px.bar(
        comparison_df,
        x="day_type",
        y=["txn_count", "avg_value"],
        barmode="group",
        color_discrete_sequence=[COLORS["secondary"], COLORS["accent"]],
        labels={"value": "Value", "variable": "Metric"},
    )

    fig = _apply_layout(fig, "Weekday vs Weekend Transaction Comparison")

    return fig


# ── Status Breakdown ──────────────────────────────────────────────────

def status_pie_chart(df: pd.DataFrame) -> go.Figure:
    """Create a pie chart of transaction statuses."""
    if "status" not in df.columns:
        return go.Figure()

    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]

    color_map = {
        "Completed": COLORS["success"],
        "Failed": COLORS["danger"],
        "Reversed": COLORS["warning"],
        "Pending": COLORS["info"],
    }

    colors = [color_map.get(s, COLORS["text_secondary"]) for s in status_counts["status"]]

    fig = go.Figure(data=[go.Pie(
        labels=status_counts["status"],
        values=status_counts["count"],
        hole=0.45,
        marker=dict(colors=colors),
        textinfo="label+percent",
    )])

    fig = _apply_layout(fig, "Transaction Status Distribution")

    return fig


# ── Hourly Distribution ──────────────────────────────────────────────

def hourly_bar_chart(hourly_df: pd.DataFrame) -> go.Figure:
    """Create a bar chart of hourly transaction distribution."""
    if hourly_df.empty:
        return go.Figure()

    fig = px.bar(
        hourly_df,
        x="hour",
        y="txn_count",
        color="txn_count",
        color_continuous_scale="Viridis",
        labels={"hour": "Hour of Day", "txn_count": "Transaction Count"},
    )

    fig = _apply_layout(fig, "Transaction Volume by Hour of Day")
    fig.update_xaxes(
        title_text="Hour of Day",
        tickvals=list(range(24)),
        ticktext=[f"{h:02d}:00" for h in range(24)],
    )
    fig.update_yaxes(title_text="Number of Transactions")

    return fig


# ── Day of Week Bar Chart ────────────────────────────────────────────

def day_of_week_chart(df: pd.DataFrame) -> go.Figure:
    """Create a bar chart of transactions by day of week."""
    if "day_of_week" not in df.columns:
        return go.Figure()

    amount_col = "absolute_amount" if "absolute_amount" in df.columns else "amount"

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_counts = df.groupby("day_of_week")[amount_col].count().reindex(day_order).reset_index()
    day_counts.columns = ["day_of_week", "txn_count"]

    colors = [COLORS["secondary"] if d not in ["Saturday", "Sunday"]
              else COLORS["accent"] for d in day_counts["day_of_week"]]

    fig = go.Figure(data=go.Bar(
        x=day_counts["day_of_week"],
        y=day_counts["txn_count"],
        marker_color=colors,
        text=day_counts["txn_count"],
        textposition="outside",
    ))

    fig = _apply_layout(fig, "Transaction Volume by Day of Week")
    fig.update_xaxes(title_text="Day of Week")
    fig.update_yaxes(title_text="Number of Transactions")

    return fig
