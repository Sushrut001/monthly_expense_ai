"""
app/utils/charts.py
All Plotly chart factories. Returns go.Figure objects; Streamlit renders them.
"""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ── Palette ────────────────────────────────────────────────────────────────
PALETTE = [
    "#6366F1", "#F59E0B", "#10B981", "#EF4444",
    "#8B5CF6", "#14B8A6", "#F97316", "#EC4899",
]

TEMPLATE = "plotly_dark"

_LAYOUT = dict(
    template=TEMPLATE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#E2E8F0"),
    margin=dict(l=20, r=20, t=40, b=20),
)


def monthly_trend_chart(df: pd.DataFrame) -> go.Figure:
    """Grouped bar — Income vs Expense per month."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["month"], y=df.get("Income", 0),
        name="Income", marker_color="#10B981",
    ))
    fig.add_trace(go.Bar(
        x=df["month"], y=df.get("Expense", 0),
        name="Expense", marker_color="#EF4444",
    ))
    fig.update_layout(
        **_LAYOUT,
        title="Monthly Income vs Expense",
        barmode="group",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
    )
    return fig


def category_pie_chart(df: pd.DataFrame) -> go.Figure:
    """Donut chart for category-wise spending."""
    fig = px.pie(
        df, names="Category", values="Amount",
        hole=0.5, color_discrete_sequence=PALETTE,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    fig.update_layout(**_LAYOUT, title="Category-wise Spending")
    return fig


def category_bar_chart(df: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        df, x="Amount", y="Category", orientation="h",
        color="Amount", color_continuous_scale="Viridis",
    )
    fig.update_layout(
        **_LAYOUT,
        title="Spending by Category",
        yaxis={"categoryorder": "total ascending"},
    )
    return fig


def top_expenses_chart(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    df["label"] = df["description"].str[:30] + "…"
    fig = px.bar(
        df, x="amount", y="label", orientation="h",
        color="category", color_discrete_sequence=PALETTE,
        labels={"amount": "Amount (₹)", "label": "Transaction", "category": "Category"},
    )
    fig.update_layout(
        **_LAYOUT,
        title="Top 10 Expenses",
        yaxis={"categoryorder": "total ascending"},
        showlegend=True,
    )
    return fig


def anomaly_scatter(df: pd.DataFrame) -> go.Figure:
    """Scatter plot highlighting anomalous transactions."""
    normal = df[df["is_anomaly"] == False]
    anomaly = df[df["is_anomaly"] == True]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=normal["date"], y=normal["amount"],
        mode="markers",
        name="Normal",
        marker=dict(color="#6366F1", size=5, opacity=0.6),
        text=normal["description"],
    ))
    fig.add_trace(go.Scatter(
        x=anomaly["date"], y=anomaly["amount"],
        mode="markers",
        name="Anomaly 🚨",
        marker=dict(color="#EF4444", size=10, symbol="x", opacity=0.9),
        text=anomaly["description"],
    ))
    fig.update_layout(
        **_LAYOUT,
        title="Transaction Anomaly Detection",
        xaxis_title="Date",
        yaxis_title="Amount (₹)",
    )
    return fig


def savings_gauge(score: float) -> go.Figure:
    """Gauge chart for Financial Health Score."""
    color = "#10B981" if score >= 70 else "#F59E0B" if score >= 45 else "#EF4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Financial Health Score", "font": {"size": 18, "color": "#E2E8F0"}},
        number={"suffix": "/100", "font": {"color": "#E2E8F0"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#94A3B8"},
            "bar": {"color": color},
            "bgcolor": "rgba(0,0,0,0)",
            "steps": [
                {"range": [0, 40], "color": "rgba(239,68,68,0.2)"},
                {"range": [40, 70], "color": "rgba(245,158,11,0.2)"},
                {"range": [70, 100], "color": "rgba(16,185,129,0.2)"},
            ],
            "threshold": {
                "line": {"color": "#FFFFFF", "width": 3},
                "thickness": 0.75,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        **_LAYOUT,
        height=280,
    )
    return fig


def expense_trend_line(df: pd.DataFrame) -> go.Figure:
    """Line chart with moving average for expense trend."""
    expense = df[df["transaction_type"] == "debit"].copy()
    expense = expense.sort_values("date")
    expense["rolling_avg"] = expense["amount"].rolling(7, min_periods=1).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=expense["date"], y=expense["amount"],
        mode="markers", name="Transactions",
        marker=dict(color="#6366F1", size=4, opacity=0.5),
    ))
    fig.add_trace(go.Scatter(
        x=expense["date"], y=expense["rolling_avg"],
        mode="lines", name="7-day MA",
        line=dict(color="#F59E0B", width=2),
    ))
    fig.update_layout(
        **_LAYOUT,
        title="Expense Trend with 7-day Moving Average",
        xaxis_title="Date",
        yaxis_title="Amount (₹)",
    )
    return fig
