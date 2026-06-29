"""
app/utils/analytics.py
Computes all KPIs and aggregations for the dashboard.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class FinancialSummary:
    total_income: float
    total_expense: float
    net_savings: float
    savings_rate: float          # 0–100 %
    health_score: float          # 0–100
    num_transactions: int
    num_anomalies: int
    avg_monthly_expense: float
    top_category: str
    date_range: tuple[str, str]


def compute_summary(df: pd.DataFrame) -> FinancialSummary:
    income_df = df[df["transaction_type"] == "credit"]
    expense_df = df[df["transaction_type"] == "debit"]

    total_income = income_df["amount"].sum()
    total_expense = expense_df["amount"].sum()
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0

    # Monthly avg expense
    if not expense_df.empty:
        monthly = (
            expense_df.groupby(expense_df["date"].dt.to_period("M"))["amount"]
            .sum()
        )
        avg_monthly_expense = monthly.mean()
    else:
        avg_monthly_expense = 0.0

    # Top spend category (excluding Income)
    cat_expense = (
        expense_df[expense_df["category"] != "Income"]
        .groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    top_category = cat_expense.index[0] if not cat_expense.empty else "N/A"

    num_anomalies = int(df.get("is_anomaly", pd.Series(False)).sum())

    # Health score
    health_score = _compute_health_score(
        savings_rate=savings_rate,
        num_anomalies=num_anomalies,
        total_income=total_income,
        total_expense=total_expense,
        df=df,
    )

    date_range = (
        str(df["date"].min().date()),
        str(df["date"].max().date()),
    )

    return FinancialSummary(
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        net_savings=round(net_savings, 2),
        savings_rate=round(savings_rate, 2),
        health_score=round(health_score, 1),
        num_transactions=len(df),
        num_anomalies=num_anomalies,
        avg_monthly_expense=round(avg_monthly_expense, 2),
        top_category=top_category,
        date_range=date_range,
    )


def _compute_health_score(
    savings_rate: float,
    num_anomalies: int,
    total_income: float,
    total_expense: float,
    df: pd.DataFrame,
) -> float:
    """
    Weighted scoring across 4 dimensions (total 100 pts).
    """
    score = 0.0

    # 1. Savings rate (40 pts)
    score += min(savings_rate / 30 * 40, 40)

    # 2. Expense ratio (25 pts)
    if total_income > 0:
        expense_ratio = total_expense / total_income
        # Ideal < 0.7
        score += max(0, (1 - expense_ratio) / 0.3 * 25)
    else:
        score += 0

    # 3. Anomaly penalty (20 pts)
    anomaly_rate = num_anomalies / max(len(df), 1)
    score += max(0, 20 - anomaly_rate * 200)

    # 4. Consistency — low std dev of monthly spend (15 pts)
    expense_df = df[df["transaction_type"] == "debit"]
    if not expense_df.empty:
        monthly = (
            expense_df.groupby(expense_df["date"].dt.to_period("M"))["amount"].sum()
        )
        cv = monthly.std() / (monthly.mean() + 1e-9)
        score += max(0, 15 - cv * 15)
    else:
        score += 15

    return min(max(score, 0), 100)


# ── Aggregation helpers ────────────────────────────────────────────────────

def monthly_spending_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Returns monthly income & expense totals."""
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    pivot = (
        df.groupby(["month", "transaction_type"])["amount"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    pivot.columns.name = None
    pivot = pivot.rename(columns={"credit": "Income", "debit": "Expense"})
    for col in ("Income", "Expense"):
        if col not in pivot.columns:
            pivot[col] = 0.0
    return pivot.sort_values("month")


def category_spending(df: pd.DataFrame) -> pd.DataFrame:
    """Category-wise expense totals (debits only)."""
    expense = df[df["transaction_type"] == "debit"]
    cat = (
        expense.groupby("category")["amount"]
        .sum()
        .reset_index()
        .sort_values("amount", ascending=False)
    )
    cat.columns = ["Category", "Amount"]
    return cat


def top_expenses(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top-n individual debit transactions."""
    expense = df[df["transaction_type"] == "debit"].copy()
    return (
        expense.nlargest(n, "amount")[["date", "description", "amount", "category"]]
        .reset_index(drop=True)
    )


def anomaly_transactions(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["is_anomaly"] == True].copy()
