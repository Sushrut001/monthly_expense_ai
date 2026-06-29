"""
app/pages/expense_analysis.py
Deep-dive into expenses: category bars, top transactions, anomaly detection.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from app.components.ui import section_header, info_banner
from app.utils.analytics import category_spending, top_expenses, anomaly_transactions
from app.utils.charts import (
    category_bar_chart,
    top_expenses_chart,
    anomaly_scatter,
    expense_trend_line,
)


def render(df: pd.DataFrame) -> None:
    section_header(
        "🔍 Expense Analysis",
        "Category breakdown, top transactions, and anomaly detection",
    )

    # ── Tab layout ─────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs([
        "📂 By Category",
        "🏆 Top Expenses",
        "📈 Trend",
        "🚨 Anomalies",
    ])

    # ── Category breakdown ─────────────────────────────────────────────
    with tab1:
        cat_df = category_spending(df)
        if cat_df.empty:
            info_banner("No expense data found.", "warning")
        else:
            col1, col2 = st.columns([3, 2])
            with col1:
                st.plotly_chart(category_bar_chart(cat_df), use_container_width=True)
            with col2:
                st.markdown("#### Category Summary")
                cat_display = cat_df.copy()
                cat_display["Amount"] = cat_display["Amount"].apply(
                    lambda x: f"₹{x:,.2f}"
                )
                cat_display["Share"] = (
                    cat_df["Amount"] / cat_df["Amount"].sum() * 100
                ).apply(lambda x: f"{x:.1f}%")
                st.dataframe(
                    cat_display,
                    hide_index=True,
                    use_container_width=True,
                )

    # ── Top 10 expenses ────────────────────────────────────────────────
    with tab2:
        top_df = top_expenses(df, n=10)
        if top_df.empty:
            info_banner("No expense data found.", "warning")
        else:
            st.plotly_chart(top_expenses_chart(top_df), use_container_width=True)
            st.markdown("#### Transaction Detail")
            display_df = top_df.copy()
            display_df["amount"] = display_df["amount"].apply(lambda x: f"₹{x:,.2f}")
            display_df["date"] = display_df["date"].dt.strftime("%d %b %Y")
            display_df.columns = ["Date", "Description", "Amount", "Category"]
            st.dataframe(display_df, hide_index=True, use_container_width=True)

    # ── Trend line ─────────────────────────────────────────────────────
    with tab3:
        expense_df = df[df["transaction_type"] == "debit"]
        if expense_df.empty:
            info_banner("No expense data found.", "warning")
        else:
            st.plotly_chart(expense_trend_line(df), use_container_width=True)

            # Category filter
            st.markdown("#### Filter by Category")
            categories = sorted(expense_df["category"].unique().tolist())
            selected_cats = st.multiselect(
                "Select categories",
                categories,
                default=categories[:3] if len(categories) >= 3 else categories,
            )
            if selected_cats:
                filtered = expense_df[expense_df["category"].isin(selected_cats)]
                pivot = (
                    filtered
                    .groupby([filtered["date"].dt.to_period("M").astype(str), "category"])["amount"]
                    .sum()
                    .unstack(fill_value=0)
                    .reset_index()
                )
                pivot.columns.name = None
                import plotly.express as px
                fig = px.line(
                    pivot,
                    x="date",
                    y=[c for c in pivot.columns if c != "date"],
                    template="plotly_dark",
                    title="Monthly Spend by Category",
                    labels={"value": "Amount (₹)", "date": "Month"},
                )
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E2E8F0"),
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Anomaly detection ──────────────────────────────────────────────
    with tab4:
        n_anomalies = int(df.get("is_anomaly", pd.Series(False)).sum())
        if n_anomalies == 0:
            info_banner("No anomalies detected in your transactions. 🎉", "success")
        else:
            info_banner(
                f"{n_anomalies} anomalous transaction(s) detected — review them below.",
                "warning",
            )

        st.plotly_chart(anomaly_scatter(df), use_container_width=True)

        anomaly_df = anomaly_transactions(df)
        if not anomaly_df.empty:
            st.markdown("#### Flagged Transactions")
            disp = anomaly_df[["date", "description", "amount", "category", "anomaly_score"]].copy()
            disp["amount"] = disp["amount"].apply(lambda x: f"₹{x:,.2f}")
            disp["anomaly_score"] = disp["anomaly_score"].apply(lambda x: f"{x:.3f}")
            disp["date"] = disp["date"].dt.strftime("%d %b %Y")
            disp.columns = ["Date", "Description", "Amount", "Category", "Anomaly Score"]
            st.dataframe(disp, hide_index=True, use_container_width=True)
