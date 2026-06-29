"""
app/pages/ai_insights.py
AI-powered personalised financial insights via Gemini.
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
from dataclasses import asdict

from app.components.ui import section_header, info_banner
from app.services.gemini_service import GeminiService
from app.utils.analytics import compute_summary, category_spending, top_expenses


def render(df: pd.DataFrame, gemini: GeminiService) -> None:
    section_header(
        "🤖 AI Financial Insights",
        "Personalised analysis and savings recommendations powered by Google Gemini",
    )

    summary = compute_summary(df)
    cat_df = category_spending(df)
    top_df = top_expenses(df, n=10)

    # ── Quick health panel ─────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        score = summary.health_score
        color = "#10B981" if score >= 70 else "#F59E0B" if score >= 45 else "#EF4444"
        st.markdown(
            f"""<div style="text-align:center;padding:1rem;background:rgba(255,255,255,0.04);
            border-radius:12px;border:1px solid {color}">
            <p style="color:#94A3B8;margin:0;font-size:0.8rem">HEALTH SCORE</p>
            <p style="color:{color};font-size:2.5rem;font-weight:800;margin:0">{score:.0f}</p>
            <p style="color:#94A3B8;margin:0;font-size:0.8rem">out of 100</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        sr = summary.savings_rate
        color2 = "#10B981" if sr >= 20 else "#F59E0B" if sr >= 10 else "#EF4444"
        st.markdown(
            f"""<div style="text-align:center;padding:1rem;background:rgba(255,255,255,0.04);
            border-radius:12px;border:1px solid {color2}">
            <p style="color:#94A3B8;margin:0;font-size:0.8rem">SAVINGS RATE</p>
            <p style="color:{color2};font-size:2.5rem;font-weight:800;margin:0">{sr:.1f}%</p>
            <p style="color:#94A3B8;margin:0;font-size:0.8rem">of income saved</p>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        top_cat = summary.top_category
        st.markdown(
            f"""<div style="text-align:center;padding:1rem;background:rgba(255,255,255,0.04);
            border-radius:12px;border:1px solid #8B5CF6">
            <p style="color:#94A3B8;margin:0;font-size:0.8rem">TOP SPEND CATEGORY</p>
            <p style="color:#8B5CF6;font-size:1.8rem;font-weight:800;margin:0">{top_cat}</p>
            <p style="color:#94A3B8;margin:0;font-size:0.8rem">highest expense area</p>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Generate button ────────────────────────────────────────────────
    if not gemini.is_available:
        info_banner(
            "Gemini API key not configured. Add GEMINI_API_KEY to your .env file.",
            "warning",
        )

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        generate = st.button(
            "✨ Generate AI Insights",
            use_container_width=True,
            type="primary",
            disabled=not gemini.is_available,
        )

    # Cache insights in session so re-renders don't re-call API
    if "ai_insights_text" not in st.session_state:
        st.session_state.ai_insights_text = None

    if generate:
        with st.spinner("🧠 Analysing your finances with Gemini…"):
            summary_dict = {
                "total_income": summary.total_income,
                "total_expense": summary.total_expense,
                "net_savings": summary.net_savings,
                "savings_rate": summary.savings_rate,
                "health_score": summary.health_score,
                "num_anomalies": summary.num_anomalies,
                "date_range": summary.date_range,
            }
            text = gemini.generate_insights(summary_dict, cat_df, top_df)
            st.session_state.ai_insights_text = text

    if st.session_state.ai_insights_text:
        st.markdown("---")
        st.markdown(
            """<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.3);
            border-radius:12px;padding:1.5rem;line-height:1.8">""",
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state.ai_insights_text)
        st.markdown("</div>", unsafe_allow_html=True)

        col_dl, _ = st.columns([1, 4])
        with col_dl:
            st.download_button(
                "📥 Download Insights",
                data=st.session_state.ai_insights_text,
                file_name="financial_insights.md",
                mime="text/markdown",
            )
