"""
app/pages/overview.py
Dashboard Overview — KPI cards, health score, monthly trend.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from app.components.ui import metric_card, section_header, health_score_badge
from app.utils.analytics import (
    compute_summary,
    monthly_spending_trend,
    category_spending,
)
from app.utils.charts import (
    monthly_trend_chart,
    category_pie_chart,
    savings_gauge,
)


def render(df: pd.DataFrame) -> None:
    summary = compute_summary(df)

    # ── Header ─────────────────────────────────────────────────────────
    section_header(
        "📊 Financial Overview",
        f"Analysis period: {summary.date_range[0]} → {summary.date_range[1]}",
    )
    health_score_badge(summary.health_score)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI Row 1 ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Income", f"₹{summary.total_income:,.0f}", color="#10B981")
    with c2:
        metric_card("Total Expense", f"₹{summary.total_expense:,.0f}", color="#EF4444")
    with c3:
        sign = "+" if summary.net_savings >= 0 else ""
        color = "#10B981" if summary.net_savings >= 0 else "#EF4444"
        metric_card("Net Savings", f"{sign}₹{summary.net_savings:,.0f}", color=color)
    with c4:
        metric_card("Savings Rate", f"{summary.savings_rate:.1f}%", color="#6366F1")

    # ── KPI Row 2 ──────────────────────────────────────────────────────
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Transactions", str(summary.num_transactions), color="#8B5CF6")
    with c6:
        metric_card("Anomalies", str(summary.num_anomalies), color="#F97316")
    with c7:
        metric_card("Avg Monthly Expense", f"₹{summary.avg_monthly_expense:,.0f}", color="#14B8A6")
    with c8:
        metric_card("Top Spend Category", summary.top_category, color="#EC4899")

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        trend_df = monthly_spending_trend(df)
        st.plotly_chart(monthly_trend_chart(trend_df), use_container_width=True)

    with col_right:
        st.plotly_chart(savings_gauge(summary.health_score), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cat_df = category_spending(df)
        st.plotly_chart(category_pie_chart(cat_df), use_container_width=True)
