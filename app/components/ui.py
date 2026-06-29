"""
app/components/ui.py
Reusable Streamlit UI building blocks.
"""
from __future__ import annotations

import streamlit as st


def metric_card(label: str, value: str, delta: str = "", color: str = "#6366F1") -> None:
    """Render a styled metric card."""
    delta_html = f'<p style="color:#94A3B8;font-size:0.78rem;margin:0">{delta}</p>' if delta else ""
    st.markdown(
        f"""
        <div style="
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-left: 4px solid {color};
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.5rem;
        ">
            <p style="color:#94A3B8;font-size:0.78rem;margin:0;text-transform:uppercase;letter-spacing:0.05em">{label}</p>
            <p style="color:#F1F5F9;font-size:1.6rem;font-weight:700;margin:0.2rem 0">{value}</p>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div style="margin: 1.5rem 0 1rem 0;">
            <h2 style="color:#F1F5F9;font-weight:700;margin:0">{title}</h2>
            {"<p style='color:#94A3B8;margin:0.2rem 0 0 0'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_banner(message: str, kind: str = "info") -> None:
    colors = {
        "info": ("#6366F1", "rgba(99,102,241,0.12)"),
        "success": ("#10B981", "rgba(16,185,129,0.12)"),
        "warning": ("#F59E0B", "rgba(245,158,11,0.12)"),
        "error": ("#EF4444", "rgba(239,68,68,0.12)"),
    }
    border_color, bg_color = colors.get(kind, colors["info"])
    icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
    icon = icons.get(kind, "ℹ️")
    st.markdown(
        f"""
        <div style="
            background:{bg_color};
            border:1px solid {border_color};
            border-radius:10px;
            padding:0.75rem 1rem;
            color:#E2E8F0;
            margin-bottom:1rem;
        ">{icon} {message}</div>
        """,
        unsafe_allow_html=True,
    )


def health_score_badge(score: float) -> None:
    if score >= 70:
        color, label = "#10B981", "Healthy"
    elif score >= 45:
        color, label = "#F59E0B", "Moderate"
    else:
        color, label = "#EF4444", "Needs Attention"

    st.markdown(
        f"""
        <div style="
            display:inline-block;
            background:rgba(0,0,0,0.3);
            border:2px solid {color};
            border-radius:50px;
            padding:0.3rem 1rem;
            color:{color};
            font-weight:700;
            font-size:0.9rem;
        ">● {label}</div>
        """,
        unsafe_allow_html=True,
    )
