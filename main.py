"""
main.py
AI Personal Finance Analyzer — Streamlit entry point.
Run with: streamlit run main.py
"""
from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path

import pandas as pd
import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import APP_CONFIG
from app.services.database import DatabaseService
from app.services.gemini_service import GeminiService
from app.utils.preprocessor import clean_transactions
from app.utils.categorizer import categorise_transactions
from app.utils.anomaly_detector import detect_anomalies
from app.pages import overview, expense_analysis, ai_insights

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title=APP_CONFIG.title,
    page_icon=APP_CONFIG.page_icon,
    layout=APP_CONFIG.layout,
    initial_sidebar_state="expanded",
)

# ── Design System — Apple Metal UI ─────────────────────────────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ══════════════════════════════════════════════════════
   APPLE METAL DESIGN TOKENS
══════════════════════════════════════════════════════ */
:root {
    /* Background layers — dark aluminum */
    --bg-system:     #000000;
    --bg-base:       #0A0A0A;
    --bg-elevated-1: #141414;
    --bg-elevated-2: #1C1C1E;
    --bg-elevated-3: #2C2C2E;
    --bg-elevated-4: #3A3A3C;

    /* Glass layers */
    --glass-1:    rgba(255,255,255,0.04);
    --glass-2:    rgba(255,255,255,0.07);
    --glass-3:    rgba(255,255,255,0.10);
    --glass-hover: rgba(255,255,255,0.12);

    /* Separators */
    --sep-opaque:  #38383A;
    --sep-nonopaque: rgba(84,84,88,0.65);
    --sep-highlight: rgba(255,255,255,0.09);

    /* Apple system colors */
    --sys-blue:    #0A84FF;
    --sys-green:   #30D158;
    --sys-indigo:  #5E5CE6;
    --sys-orange:  #FF9F0A;
    --sys-pink:    #FF375F;
    --sys-purple:  #BF5AF2;
    --sys-red:     #FF453A;
    --sys-teal:    #5AC8FA;
    --sys-yellow:  #FFD60A;

    /* Tinted fills */
    --fill-blue:   rgba(10,132,255,0.18);
    --fill-green:  rgba(48,209,88,0.15);
    --fill-orange: rgba(255,159,10,0.15);
    --fill-red:    rgba(255,69,58,0.15);
    --fill-purple: rgba(191,90,242,0.15);
    --fill-indigo: rgba(94,92,230,0.15);
    --fill-teal:   rgba(90,200,250,0.12);

    /* Label hierarchy */
    --label-primary:   rgba(255,255,255,0.92);
    --label-secondary: rgba(235,235,245,0.60);
    --label-tertiary:  rgba(235,235,245,0.30);
    --label-quaternary:rgba(235,235,245,0.16);

    /* Typography */
    --font-sf: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;

    /* Radii — Apple's exact values */
    --radius-xs:  6px;
    --radius-sm:  10px;
    --radius-md:  14px;
    --radius-lg:  18px;
    --radius-xl:  22px;
    --radius-2xl: 28px;

    /* Shadows */
    --shadow-sm:  0 1px 3px rgba(0,0,0,0.6), 0 0 0 0.5px var(--sep-nonopaque);
    --shadow-md:  0 4px 16px rgba(0,0,0,0.55), 0 0 0 0.5px var(--sep-nonopaque);
    --shadow-lg:  0 12px 40px rgba(0,0,0,0.7), 0 0 0 0.5px var(--sep-nonopaque);
    --shadow-blue: 0 4px 20px rgba(10,132,255,0.28);
    --shadow-green:0 4px 18px rgba(48,209,88,0.22);
}

/* ══════════════════════════════════════════════════════
   RESET & BASE
══════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: var(--font-sf) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}

/* ── App background — pure black with subtle noise texture */
.stApp {
    background: var(--bg-system) !important;
    background-image:
        radial-gradient(ellipse 120% 80% at 20% -10%, rgba(10,132,255,0.07) 0%, transparent 50%),
        radial-gradient(ellipse 80% 60% at 80% 100%, rgba(48,209,88,0.05) 0%, transparent 50%),
        radial-gradient(ellipse 60% 50% at 50% 50%, rgba(94,92,230,0.025) 0%, transparent 65%);
    min-height: 100vh;
}

.block-container {
    padding-top: 1.8rem !important;
    padding-bottom: 5rem !important;
    max-width: 1360px !important;
}

/* ══════════════════════════════════════════════════════
   SIDEBAR — frosted aluminum panel
══════════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: rgba(18,18,18,0.85) !important;
    backdrop-filter: blur(40px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(40px) saturate(180%) !important;
    border-right: 0.5px solid var(--sep-nonopaque) !important;
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}

/* ── Brand lockup */
.brand-lockup {
    padding: 1.4rem 1.4rem 1.2rem;
    border-bottom: 0.5px solid var(--sep-nonopaque);
    background: linear-gradient(180deg, rgba(255,255,255,0.025) 0%, transparent 100%);
}

.brand-mark {
    width: 42px;
    height: 42px;
    background: linear-gradient(145deg, #0A84FF 0%, #30D158 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    margin-bottom: 10px;
    box-shadow: 0 4px 18px rgba(10,132,255,0.4), inset 0 1px 0 rgba(255,255,255,0.25);
}

.brand-name {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--label-primary);
    letter-spacing: -0.025em;
    margin: 0 0 2px;
    line-height: 1.1;
}

.brand-sub {
    font-size: 0.62rem;
    font-weight: 500;
    color: var(--label-tertiary);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin: 0;
}

/* ── Sidebar sections */
.sidebar-section {
    padding: 1rem 1.4rem 0.35rem;
}

.sidebar-label {
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--label-tertiary);
    margin-bottom: 0.6rem;
}

/* ── Sidebar divider */
.sidebar-divider {
    height: 0.5px;
    background: var(--sep-nonopaque);
    margin: 0.5rem 1.4rem;
}

/* ── Status pills */
.status-row {
    display: flex;
    flex-direction: column;
    gap: 5px;
    padding: 0.5rem 1.4rem 1.2rem;
}

.status-pill {
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 6px 11px;
    border-radius: var(--radius-sm);
    background: var(--glass-1);
    border: 0.5px solid var(--sep-nonopaque);
}

.status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}
.status-dot.green  { background: var(--sys-green);  box-shadow: 0 0 8px rgba(48,209,88,0.7);  animation: pulse-dot 2.4s ease-in-out infinite; }
.status-dot.amber  { background: var(--sys-orange); box-shadow: 0 0 6px rgba(255,159,10,0.6); }
.status-dot.red    { background: var(--sys-red);    box-shadow: 0 0 6px rgba(255,69,58,0.6);  }

@keyframes pulse-dot {
    0%, 100% { opacity: 1;    box-shadow: 0 0 8px rgba(48,209,88,0.7); }
    50%       { opacity: 0.6; box-shadow: 0 0 4px rgba(48,209,88,0.3); }
}

.status-text {
    font-size: 0.7rem;
    color: var(--label-secondary);
    font-weight: 500;
}

/* ══════════════════════════════════════════════════════
   NAV RADIO — iOS-style segmented feel
══════════════════════════════════════════════════════ */
[data-testid="stSidebar"] .stRadio > label { display: none !important; }

[data-testid="stSidebar"] .stRadio > div {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 0 0.8rem;
}

[data-testid="stSidebar"] .stRadio > div > label {
    display: flex !important;
    align-items: center;
    gap: 10px;
    padding: 9px 13px;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: all 0.12s cubic-bezier(0.4,0,0.2,1);
    font-size: 0.83rem;
    font-weight: 500;
    color: var(--label-secondary) !important;
    border: 0.5px solid transparent;
    letter-spacing: -0.01em;
}

[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: var(--glass-2);
    color: var(--label-primary) !important;
    border-color: var(--sep-nonopaque);
}

[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
    background: rgba(10,132,255,0.18) !important;
    border-color: rgba(10,132,255,0.35) !important;
    color: var(--sys-blue) !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
}

[data-testid="stSidebar"] .stRadio > div > label > div:first-child { display: none; }

/* ══════════════════════════════════════════════════════
   FILE UPLOADER
══════════════════════════════════════════════════════ */
[data-testid="stFileUploader"] {
    background: var(--glass-1) !important;
    border: 1.5px dashed rgba(10,132,255,0.38) !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.18s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(10,132,255,0.65) !important;
    background: rgba(10,132,255,0.04) !important;
    box-shadow: 0 0 0 4px rgba(10,132,255,0.06);
}

[data-testid="stFileUploader"] small,
[data-testid="stFileUploader"] span { color: var(--label-secondary) !important; }

/* ══════════════════════════════════════════════════════
   BUTTONS — Apple rounded style
══════════════════════════════════════════════════════ */
.stButton > button,
.stDownloadButton > button {
    font-family: var(--font-sf) !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.58rem 1.4rem !important;
    border: 0.5px solid var(--sep-nonopaque) !important;
    background: var(--bg-elevated-2) !important;
    color: var(--label-secondary) !important;
    transition: all 0.15s cubic-bezier(0.4,0,0.2,1) !important;
    letter-spacing: -0.01em !important;
    width: 100% !important;
    box-shadow: var(--shadow-sm) !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    background: var(--bg-elevated-3) !important;
    color: var(--label-primary) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}

.stButton > button[kind="primary"] {
    background: var(--sys-blue) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: var(--shadow-blue) !important;
}

.stButton > button[kind="primary"]:hover {
    background: #248aff !important;
    transform: translateY(-1.5px) !important;
    box-shadow: 0 6px 26px rgba(10,132,255,0.42) !important;
}

/* ══════════════════════════════════════════════════════
   SELECTBOX
══════════════════════════════════════════════════════ */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-elevated-2) !important;
    border: 0.5px solid var(--sep-nonopaque) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--label-secondary) !important;
    font-size: 0.83rem !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ══════════════════════════════════════════════════════
   TABS — iOS-style segmented control feel
══════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-elevated-2);
    border-radius: var(--radius-md);
    padding: 4px;
    gap: 2px;
    border: 0.5px solid var(--sep-nonopaque);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}

.stTabs [data-baseweb="tab"] {
    border-radius: var(--radius-xs);
    color: var(--label-secondary);
    font-weight: 500;
    font-size: 0.82rem;
    padding: 0.42rem 1rem;
    letter-spacing: -0.01em;
    transition: all 0.12s ease;
}

.stTabs [aria-selected="true"] {
    background: var(--bg-elevated-4) !important;
    color: var(--label-primary) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ══════════════════════════════════════════════════════
   ALERTS
══════════════════════════════════════════════════════ */
.stAlert {
    border-radius: var(--radius-md) !important;
    border: 0.5px solid var(--sep-nonopaque) !important;
    background: var(--bg-elevated-2) !important;
    font-size: 0.82rem !important;
    backdrop-filter: blur(20px) !important;
}

/* ══════════════════════════════════════════════════════
   METRICS — Apple card style
══════════════════════════════════════════════════════ */
[data-testid="stMetric"] {
    background: var(--bg-elevated-2);
    border: 0.5px solid var(--sep-nonopaque);
    border-radius: var(--radius-lg);
    padding: 1.2rem 1.4rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}

[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 0.5px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.12), transparent);
}

[data-testid="stMetric"]:hover {
    background: var(--bg-elevated-3);
    border-color: rgba(255,255,255,0.12);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

[data-testid="stMetricLabel"] {
    color: var(--label-tertiary) !important;
    font-size: 0.67rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

[data-testid="stMetricValue"] {
    font-family: var(--font-sf) !important;
    color: var(--label-primary) !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.04em !important;
    line-height: 1.1 !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.74rem !important;
    font-weight: 600 !important;
}

/* ══════════════════════════════════════════════════════
   DATAFRAME
══════════════════════════════════════════════════════ */
.stDataFrame {
    border-radius: var(--radius-lg) !important;
    overflow: hidden !important;
    border: 0.5px solid var(--sep-nonopaque) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ══════════════════════════════════════════════════════
   MISC
══════════════════════════════════════════════════════ */
hr {
    border: none !important;
    border-top: 0.5px solid var(--sep-nonopaque) !important;
    margin: 0.5rem 0 !important;
}

.stSpinner > div { border-top-color: var(--sys-blue) !important; }

.stSuccess, div[data-testid="stNotification"] {
    background: rgba(48,209,88,0.08) !important;
    border: 0.5px solid rgba(48,209,88,0.28) !important;
    color: var(--sys-green) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.78rem !important;
}

.stError {
    background: rgba(255,69,58,0.08) !important;
    border: 0.5px solid rgba(255,69,58,0.28) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.78rem !important;
}

/* ══════════════════════════════════════════════════════
   LANDING PAGE — Hero
══════════════════════════════════════════════════════ */
.landing-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 78vh;
    padding: 3.5rem 1.5rem;
    text-align: center;
    position: relative;
}

/* Ambient glow behind hero */
.landing-wrap::before {
    content: '';
    position: absolute;
    top: 10%; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 300px;
    background: radial-gradient(ellipse, rgba(10,132,255,0.1) 0%, transparent 70%);
    pointer-events: none;
    border-radius: 50%;
    filter: blur(60px);
}

/* Badge pill */
.landing-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(10,132,255,0.1);
    border: 0.5px solid rgba(10,132,255,0.35);
    border-radius: 100px;
    padding: 5px 16px 5px 9px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--sys-blue);
    margin-bottom: 2rem;
    box-shadow: 0 2px 12px rgba(10,132,255,0.15);
}

.landing-eyebrow-dot {
    width: 6px;
    height: 6px;
    background: var(--sys-green);
    border-radius: 50%;
    box-shadow: 0 0 10px rgba(48,209,88,0.8);
    animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.5; transform: scale(0.75); }
}

/* Headline — SF Display style */
.landing-headline {
    font-family: var(--font-sf);
    font-size: clamp(2.6rem, 6vw, 4.2rem);
    font-weight: 700;
    color: var(--label-primary);
    letter-spacing: -0.05em;
    line-height: 1.02;
    margin: 0 0 0.15rem;
}

.gradient-text {
    background: linear-gradient(135deg, #0A84FF 0%, #30D158 50%, #5AC8FA 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.landing-sub {
    font-size: 1.05rem;
    color: var(--label-secondary);
    max-width: 460px;
    margin: 1.3rem auto 3rem;
    line-height: 1.65;
    font-weight: 400;
    letter-spacing: -0.01em;
}

/* Feature grid — Apple bento style */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5px;
    max-width: 820px;
    width: 100%;
    background: var(--sep-nonopaque);
    border-radius: var(--radius-2xl);
    overflow: hidden;
    border: 0.5px solid var(--sep-nonopaque);
    margin-bottom: 3rem;
    box-shadow: var(--shadow-lg);
}

.feature-cell {
    background: var(--bg-elevated-1);
    padding: 1.6rem 1.7rem;
    text-align: left;
    transition: background 0.18s ease;
    cursor: default;
    position: relative;
    overflow: hidden;
}

.feature-cell::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 0.5px;
    background: rgba(255,255,255,0.055);
}

.feature-cell:hover { background: var(--bg-elevated-2); }

.feature-icon {
    font-size: 1.45rem;
    margin-bottom: 0.7rem;
    display: block;
    filter: saturate(1.2);
}

.feature-title {
    font-family: var(--font-sf);
    font-size: 0.86rem;
    font-weight: 700;
    color: var(--label-primary);
    margin: 0 0 4px;
    letter-spacing: -0.02em;
}

.feature-desc {
    font-size: 0.72rem;
    color: var(--label-tertiary);
    margin: 0;
    line-height: 1.5;
}

/* CTA hint */
.landing-cta {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--label-tertiary);
    font-size: 0.79rem;
    font-weight: 500;
    letter-spacing: -0.01em;
}

.landing-cta-arrow {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: var(--bg-elevated-3);
    border: 0.5px solid var(--sep-nonopaque);
    border-radius: 50%;
    font-size: 0.76rem;
    color: var(--sys-blue);
    animation: float-arrow 2s ease-in-out infinite;
    box-shadow: var(--shadow-sm);
}

@keyframes float-arrow {
    0%, 100% { transform: translateX(0);    opacity: 0.6; }
    50%       { transform: translateX(-5px); opacity: 1; }
}

/* ══════════════════════════════════════════════════════
   SECTION HEADERS
══════════════════════════════════════════════════════ */
.section-header { margin-bottom: 1.5rem; }

.section-title {
    font-family: var(--font-sf);
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--label-primary);
    letter-spacing: -0.04em;
    margin: 0 0 0.2rem;
    line-height: 1.1;
}

.section-sub {
    font-size: 0.8rem;
    color: var(--label-secondary);
    margin: 0;
    letter-spacing: -0.005em;
}

/* Health badge */
.health-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 12px 3px 8px;
    border-radius: 100px;
    font-size: 0.69rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    margin-top: 0.65rem;
    border: 0.5px solid;
}

.health-badge.healthy  { background: rgba(48,209,88,0.12);  border-color: rgba(48,209,88,0.3);  color: var(--sys-green);  }
.health-badge.moderate { background: rgba(255,159,10,0.12); border-color: rgba(255,159,10,0.3); color: var(--sys-orange); }
.health-badge.poor     { background: rgba(255,69,58,0.12);  border-color: rgba(255,69,58,0.3);  color: var(--sys-red);    }

.health-dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 6px currentColor;
    animation: pulse-dot 2.4s ease-in-out infinite;
}

/* ══════════════════════════════════════════════════════
   CHART CARDS — Apple-style cards
══════════════════════════════════════════════════════ */
.chart-card {
    background: var(--bg-elevated-2);
    border: 0.5px solid var(--sep-nonopaque);
    border-radius: var(--radius-xl);
    padding: 1.5rem 1.6rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}

.chart-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 0.5px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
}

.chart-card:hover {
    background: var(--bg-elevated-3);
    border-color: rgba(255,255,255,0.1);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.chart-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--label-tertiary);
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ══════════════════════════════════════════════════════
   INSIGHT CARDS
══════════════════════════════════════════════════════ */
.insight-card {
    background: var(--bg-elevated-2);
    border: 0.5px solid var(--sep-nonopaque);
    border-radius: var(--radius-xl);
    padding: 1.4rem 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}

.insight-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 0.5px;
    background: rgba(255,255,255,0.08);
}

.insight-card:hover {
    background: var(--bg-elevated-3);
    border-color: rgba(255,255,255,0.1);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}

.insight-icon-wrap {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    margin-bottom: 0.85rem;
    box-shadow: var(--shadow-sm);
}

.insight-icon-wrap.blue   { background: var(--fill-blue);   border: 0.5px solid rgba(10,132,255,0.25); }
.insight-icon-wrap.green  { background: var(--fill-green);  border: 0.5px solid rgba(48,209,88,0.25);  }
.insight-icon-wrap.orange { background: var(--fill-orange); border: 0.5px solid rgba(255,159,10,0.25); }
.insight-icon-wrap.red    { background: var(--fill-red);    border: 0.5px solid rgba(255,69,58,0.25);  }
.insight-icon-wrap.purple { background: var(--fill-purple); border: 0.5px solid rgba(191,90,242,0.25); }

.insight-card-title {
    font-family: var(--font-sf);
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--label-primary);
    margin-bottom: 0.4rem;
    letter-spacing: -0.02em;
}

.insight-card-body {
    font-size: 0.79rem;
    color: var(--label-secondary);
    line-height: 1.6;
}

/* ══════════════════════════════════════════════════════
   ANOMALY CALLOUT
══════════════════════════════════════════════════════ */
.anomaly-callout {
    background: rgba(255,159,10,0.07);
    border: 0.5px solid rgba(255,159,10,0.28);
    border-radius: var(--radius-md);
    padding: 0.9rem 1.2rem;
    display: flex;
    align-items: flex-start;
    gap: 11px;
    font-size: 0.79rem;
    color: var(--label-secondary);
    line-height: 1.55;
    margin-bottom: 1rem;
}

.anomaly-callout-icon { font-size: 1rem; flex-shrink: 0; margin-top: 1px; }

/* ══════════════════════════════════════════════════════
   AI INPUT & BUBBLE
══════════════════════════════════════════════════════ */
.stTextInput > div > div > input {
    background: var(--bg-elevated-2) !important;
    border: 0.5px solid var(--sep-nonopaque) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--label-primary) !important;
    font-size: 0.85rem !important;
    font-family: var(--font-sf) !important;
    padding: 0.65rem 1rem !important;
    transition: all 0.15s ease !important;
    box-shadow: inset 0 1px 0 rgba(0,0,0,0.2) !important;
}

.stTextInput > div > div > input:focus {
    border-color: rgba(10,132,255,0.55) !important;
    box-shadow: 0 0 0 3px rgba(10,132,255,0.12), inset 0 1px 0 rgba(0,0,0,0.2) !important;
    background: var(--bg-elevated-3) !important;
}

.stTextInput > div > div > input::placeholder { color: var(--label-tertiary) !important; }

.ai-bubble {
    background: linear-gradient(145deg, var(--bg-elevated-2), var(--bg-elevated-1));
    border: 0.5px solid rgba(10,132,255,0.3);
    border-radius: var(--radius-xl);
    padding: 1.2rem 1.4rem;
    font-size: 0.83rem;
    color: var(--label-secondary);
    line-height: 1.7;
    position: relative;
    box-shadow: 0 0 30px rgba(10,132,255,0.1), var(--shadow-sm);
}

.ai-bubble::before {
    content: "✦";
    position: absolute;
    top: -10px;
    left: 16px;
    background: var(--bg-elevated-2);
    padding: 0 6px;
    color: var(--sys-blue);
    font-size: 0.68rem;
}
</style>
"""

# Inject CSS once at top-level — never inside st.markdown with mixed quote styles
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── Service init ───────────────────────────────────────────────────────────
@st.cache_resource
def get_db() -> tuple[DatabaseService, bool]:
    ok = DatabaseService.init()
    return DatabaseService, ok


@st.cache_resource
def get_gemini() -> GeminiService:
    return GeminiService()


# ── Pipeline ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def run_pipeline(file_bytes: bytes, filename: str, session_id: str) -> pd.DataFrame:
    raw = pd.read_csv(io.BytesIO(file_bytes))
    df = clean_transactions(raw)
    df = categorise_transactions(df)
    df = detect_anomalies(df)

    db_svc, db_ok = get_db()
    if db_ok:
        try:
            count = db_svc.bulk_insert_transactions(df, session_id)
            logger.info("Stored %d rows for session %s", count, session_id)
        except Exception as exc:
            logger.warning("DB write skipped: %s", exc)

    return df


# ── Sidebar ────────────────────────────────────────────────────────────────
def render_sidebar() -> tuple[str | None, pd.DataFrame | None]:
    with st.sidebar:

        # Brand lockup — SVG logo
        st.markdown(
            "<div class='brand-lockup'>"

            # ── Icon mark — Apple-style rounded square with shine
            "<svg width='42' height='42' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg'"
            " style='display:block;margin-bottom:10px;filter:drop-shadow(0 4px 12px rgba(10,132,255,0.45))'>"
            "<defs>"
            "<linearGradient id='bm' x1='0%' y1='0%' x2='100%' y2='100%'>"
            "<stop offset='0%' stop-color='#0A84FF'/>"
            "<stop offset='100%' stop-color='#30D158'/>"
            "</linearGradient>"
            "<linearGradient id='shine2' x1='0%' y1='0%' x2='0%' y2='100%'>"
            "<stop offset='0%' stop-color='rgba(255,255,255,0.2)'/>"
            "<stop offset='60%' stop-color='rgba(255,255,255,0)'/>"
            "</linearGradient>"
            "</defs>"
            "<rect width='44' height='44' rx='11' fill='url(#bm)'/>"
            "<rect width='44' height='22' rx='11' fill='url(#shine2)'/>"
            "<rect x='7' y='8' width='13' height='9' rx='2.5' fill='white' fill-opacity='0.9'/>"
            "<rect x='9' y='10' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.5'/>"
            "<rect x='14' y='10' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.5'/>"
            "<rect x='9' y='13.5' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.5'/>"
            "<rect x='14' y='13.5' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.5'/>"
            "<polyline points='6,36 12,29 18,32 25,24 33,18 38,13' fill='none'"
            " stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/>"
            "<circle cx='38' cy='13' r='2.5' fill='white'/>"
            "<line x1='38' y1='5.5' x2='38' y2='10' stroke='white' stroke-width='1.5' stroke-linecap='round'/>"
            "<line x1='33.5' y1='9' x2='42.5' y2='9' stroke='white' stroke-width='1.5' stroke-linecap='round'/>"
            "</svg>"

            # ── Wordmark + tagline
            "<p class='brand-name'>Finwise</p>"
            "<p class='brand-sub'>AI Finance Analyzer &middot; v1.0</p>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Upload section
        st.markdown(
            "<div class='sidebar-section'><p class='sidebar-label'>Your Statement</p></div>",
            unsafe_allow_html=True,
        )

        uploaded = st.file_uploader(
            "Upload CSV",
            type=["csv"],
            help="HDFC, ICICI, SBI, Axis and most bank export formats",
            label_visibility="collapsed",
        )

        df = None
        if uploaded:
            with st.spinner("Analysing your finances…"):
                session_id = st.session_state.get("session_id") or str(uuid.uuid4())[:8]
                st.session_state.session_id = session_id
                try:
                    df = run_pipeline(uploaded.read(), uploaded.name, session_id)
                    st.success(f"✓ {len(df)} transactions loaded")
                except ValueError as exc:
                    st.error(str(exc))
                    df = None

        # Past sessions
        _, db_ok = get_db()
        if db_ok and df is None:
            st.markdown(
                "<div class='sidebar-section'><p class='sidebar-label'>Past Sessions</p></div>",
                unsafe_allow_html=True,
            )
            sessions = DatabaseService.list_sessions()
            if sessions:
                chosen = st.selectbox(
                    "Load session",
                    ["— select —"] + sessions,
                    label_visibility="collapsed",
                )
                if chosen and chosen != "— select —":
                    try:
                        df = DatabaseService.fetch_session_df(chosen)
                        df["date"] = pd.to_datetime(df["date"])
                        st.session_state.session_id = chosen
                        st.success(f"✓ Loaded {len(df)} rows")
                    except Exception as exc:
                        st.error(str(exc))

        # Navigation
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='sidebar-section'><p class='sidebar-label'>Navigation</p></div>",
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Page",
            ["📊  Overview", "🔍  Expense Analysis", "✦  AI Insights"],
            label_visibility="collapsed",
        )

        # System status
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        gemini = get_gemini()

        db_color = "green" if db_ok else "amber"
        db_label = "Database connected" if db_ok else "DB offline — memory only"
        ai_color = "green" if gemini.is_available else "amber"
        ai_label = "Gemini ready" if gemini.is_available else "Gemini key not set"

        st.markdown(
            f"<div class='status-row'>"
            f"<div class='status-pill'>"
            f"<div class='status-dot {db_color}'></div>"
            f"<span class='status-text'>{db_label}</span>"
            f"</div>"
            f"<div class='status-pill'>"
            f"<div class='status-dot {ai_color}'></div>"
            f"<span class='status-text'>{ai_label}</span>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    return page, df


# ── Landing page ───────────────────────────────────────────────────────────
# KEY FIX: build the HTML as a plain Python string — no triple-quoted
# f-strings with embedded quotes, no backslash escapes inside the HTML.
# Streamlit's markdown renderer can silently escape HTML when it detects
# mismatched or nested quotes inside the injected string.

LANDING_HTML = (
    "<div class='landing-wrap'>"

    # ── App icon mark — Apple-style rounded square
    "<svg width='72' height='72' viewBox='0 0 44 44' xmlns='http://www.w3.org/2000/svg'"
    " style='display:block;margin:0 auto 1.6rem;filter:drop-shadow(0 8px 24px rgba(10,132,255,0.4))'>"
    "<defs>"
    "<linearGradient id='lbm' x1='0%' y1='0%' x2='100%' y2='100%'>"
    "<stop offset='0%' stop-color='#0A84FF'/>"
    "<stop offset='100%' stop-color='#30D158'/>"
    "</linearGradient>"
    "<linearGradient id='shine' x1='0%' y1='0%' x2='0%' y2='100%'>"
    "<stop offset='0%' stop-color='rgba(255,255,255,0.22)'/>"
    "<stop offset='100%' stop-color='rgba(255,255,255,0)'/>"
    "</linearGradient>"
    "</defs>"
    "<rect width='44' height='44' rx='11' fill='url(#lbm)'/>"
    "<rect width='44' height='22' rx='11' fill='url(#shine)'/>"
    "<rect x='7' y='8' width='13' height='9' rx='2.5' fill='white' fill-opacity='0.9'/>"
    "<rect x='9' y='10' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.55'/>"
    "<rect x='14' y='10' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.55'/>"
    "<rect x='9' y='13.5' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.55'/>"
    "<rect x='14' y='13.5' width='3' height='2.5' rx='0.6' fill='#0A84FF' fill-opacity='0.55'/>"
    "<polyline points='6,36 12,29 18,32 25,24 33,18 38,13' fill='none'"
    " stroke='white' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'/>"
    "<circle cx='38' cy='13' r='2.5' fill='white'/>"
    "<line x1='38' y1='5.5' x2='38' y2='10' stroke='white' stroke-width='1.5' stroke-linecap='round'/>"
    "<line x1='33.5' y1='9' x2='42.5' y2='9' stroke='white' stroke-width='1.5' stroke-linecap='round'/>"
    "</svg>"

    # ── Badge
    "<div class='landing-eyebrow'>"
    "<span class='landing-eyebrow-dot'></span>"
    "Powered by Google Gemini"
    "</div>"

    # ── Headline — Apple's exact headline style
    "<h1 class='landing-headline'>"
    "Know exactly where<br>"
    "your <span class='gradient-text'>money goes.</span>"
    "</h1>"

    "<p class='landing-sub'>"
    "Drop in any bank statement CSV and get a complete picture &mdash; "
    "spending patterns, anomalies, and personalised savings tips in seconds."
    "</p>"

    # ── Bento feature grid
    "<div class='feature-grid'>"

    "<div class='feature-cell'>"
    "<span class='feature-icon'>&#x1F4C8;</span>"
    "<p class='feature-title'>Smart Analytics</p>"
    "<p class='feature-desc'>Income, expenses &amp; savings rate at a glance</p>"
    "</div>"

    "<div class='feature-cell'>"
    "<span class='feature-icon'>&#x1F50D;</span>"
    "<p class='feature-title'>Expense Breakdown</p>"
    "<p class='feature-desc'>Category drill-down with monthly trend lines</p>"
    "</div>"

    "<div class='feature-cell'>"
    "<span class='feature-icon'>&#x1F6A8;</span>"
    "<p class='feature-title'>Anomaly Detection</p>"
    "<p class='feature-desc'>Isolation Forest flags unusual transactions</p>"
    "</div>"

    "<div class='feature-cell'>"
    "<span class='feature-icon'>&#x2736;</span>"
    "<p class='feature-title'>AI Insights</p>"
    "<p class='feature-desc'>Personalised tips generated by Gemini</p>"
    "</div>"

    "<div class='feature-cell'>"
    "<span class='feature-icon'>&#x1F5C4;</span>"
    "<p class='feature-title'>Session Storage</p>"
    "<p class='feature-desc'>MySQL persistence &mdash; reload anytime</p>"
    "</div>"

    "<div class='feature-cell'>"
    "<span class='feature-icon'>&#x1F4E5;</span>"
    "<p class='feature-title'>Export Ready</p>"
    "<p class='feature-desc'>Download your full AI insights report</p>"
    "</div>"

    "</div>"  # /feature-grid

    # ── CTA nudge
    "<div class='landing-cta'>"
    "<span class='landing-cta-arrow'>&#x2190;</span>"
    "Upload your bank statement from the sidebar to begin"
    "</div>"

    "</div>"  # /landing-wrap
)


def render_landing() -> None:
    st.markdown(LANDING_HTML, unsafe_allow_html=True)


# ── Main ───────────────────────────────────────────────────────────────────
def main() -> None:
    page, df = render_sidebar()

    if df is None:
        render_landing()
        return

    gemini = get_gemini()

    if page == "📊  Overview":
        overview.render(df)
    elif page == "🔍  Expense Analysis":
        expense_analysis.render(df)
    elif page == "✦  AI Insights":
        ai_insights.render(df, gemini)


if __name__ == "__main__":
    main()

    