"""
app/services/gemini_service.py
Gemini API integration for personalised financial insights.
"""
from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from config.settings import APP_CONFIG

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed; AI insights disabled.")


def _build_prompt(summary: dict, category_df: pd.DataFrame, top_df: pd.DataFrame) -> str:
    cat_text = "\n".join(
        f"  - {row['Category']}: ₹{row['Amount']:,.0f}"
        for _, row in category_df.iterrows()
    )
    top_text = "\n".join(
        f"  {i+1}. {row['description'][:50]} — ₹{row['amount']:,.0f} ({row['category']})"
        for i, (_, row) in enumerate(top_df.iterrows())
    )

    return f"""
You are a certified personal finance advisor. Analyse the following financial data 
and provide concise, actionable, empathetic advice.

## Financial Summary
- Total Income:    ₹{summary['total_income']:,.2f}
- Total Expense:   ₹{summary['total_expense']:,.2f}
- Net Savings:     ₹{summary['net_savings']:,.2f}
- Savings Rate:    {summary['savings_rate']:.1f}%
- Health Score:    {summary['health_score']}/100
- Anomalies found: {summary['num_anomalies']}
- Date Range:      {summary['date_range'][0]} to {summary['date_range'][1]}

## Category-wise Spending
{cat_text}

## Top 10 Transactions
{top_text}

Based on this data, please provide:

1. **Overall Financial Assessment** (2-3 sentences)
2. **3 Key Spending Concerns** with specific numbers
3. **5 Personalised Savings Tips** tailored to the actual spending patterns
4. **Action Plan for Next 30 Days** — 3 concrete steps
5. **Positive Highlights** — what the user is doing well

Keep the tone encouraging, professional, and specific to the data above.
Use ₹ symbol for all monetary values. Use markdown formatting.
""".strip()


class GeminiService:
    def __init__(self) -> None:
        self._model = None
        if not _GEMINI_AVAILABLE:
            return
        api_key = APP_CONFIG.gemini_api_key
        if not api_key:
            logger.warning("GEMINI_API_KEY not set; AI insights will be unavailable.")
            return
        try:
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(APP_CONFIG.gemini_model)
            logger.info("Gemini model initialised: %s", APP_CONFIG.gemini_model)
        except Exception as exc:
            logger.error("Gemini init failed: %s", exc)

    @property
    def is_available(self) -> bool:
        return self._model is not None

    def generate_insights(
        self,
        summary: dict,
        category_df: pd.DataFrame,
        top_df: pd.DataFrame,
    ) -> str:
        if not self.is_available:
            return (
                "⚠️ **AI Insights Unavailable**\n\n"
                "Please set a valid `GEMINI_API_KEY` in your `.env` file "
                "to enable personalised financial insights powered by Google Gemini."
            )
        prompt = _build_prompt(summary, category_df, top_df)
        try:
            response = self._model.generate_content(prompt)
            return response.text
        except Exception as exc:
            logger.error("Gemini generation failed: %s", exc)
            return f"⚠️ **AI Insights Error**\n\n{exc}"
