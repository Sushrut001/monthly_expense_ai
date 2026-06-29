"""
app/utils/preprocessor.py
Cleans and normalises raw bank transaction CSVs.
Handles a wide variety of column-name conventions.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Canonical column names we want after normalisation
_DATE_ALIASES = {"date", "transaction date", "txn date", "value date", "posting date"}
_DESC_ALIASES = {
    "description",
    "narration",
    "particulars",
    "details",
    "remarks",
    "memo",
    "transaction description",
    "transaction details",
}
_AMOUNT_ALIASES = {"amount", "transaction amount", "txn amount", "value"}
_DEBIT_ALIASES = {"debit", "debit amount", "withdrawal", "dr"}
_CREDIT_ALIASES = {"credit", "credit amount", "deposit", "cr"}
_TYPE_ALIASES = {"type", "transaction type", "txn type", "dr/cr"}


def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case and strip column names for fuzzy matching."""
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def _find_col(df: pd.DataFrame, aliases: set[str]) -> Optional[str]:
    for col in df.columns:
        if col in aliases:
            return col
    return None


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts a raw DataFrame from an uploaded CSV.
    Returns a clean DataFrame with columns:
        date, description, amount (always positive), transaction_type (debit/credit)
    Raises ValueError for unrecognised formats.
    """
    df = _normalise_columns(df.copy())
    df.dropna(how="all", inplace=True)

    # ── Date ───────────────────────────────────────────────────────────
    date_col = _find_col(df, _DATE_ALIASES)
    if date_col is None:
        raise ValueError(
            "Cannot find a date column. Expected one of: "
            + str(_DATE_ALIASES)
        )
    df["date"] = pd.to_datetime(df[date_col], errors="coerce")
    df.dropna(subset=["date"], inplace=True)

    # ── Description ────────────────────────────────────────────────────
    desc_col = _find_col(df, _DESC_ALIASES)
    if desc_col is None:
        # Fall back to first non-numeric text column
        for col in df.columns:
            if df[col].dtype == object and col not in ("date",):
                desc_col = col
                break
    df["description"] = (
        df[desc_col].astype(str).str.strip() if desc_col else "Unknown"
    )

    # ── Amount + type ──────────────────────────────────────────────────
    amount_col = _find_col(df, _AMOUNT_ALIASES)
    debit_col = _find_col(df, _DEBIT_ALIASES)
    credit_col = _find_col(df, _CREDIT_ALIASES)
    type_col = _find_col(df, _TYPE_ALIASES)

    def _to_float(s: pd.Series) -> pd.Series:
        return (
            s.astype(str)
            .str.replace(r"[₹$€£,\s]", "", regex=True)
            .str.replace(r"\((.+)\)", r"-\1", regex=True)
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )

    if debit_col and credit_col:
        debit = _to_float(df[debit_col])
        credit = _to_float(df[credit_col])
        df["amount"] = np.where(credit > 0, credit, debit)
        df["transaction_type"] = np.where(credit > 0, "credit", "debit")
    elif amount_col:
        df["amount"] = _to_float(df[amount_col])
        if type_col:
            raw_type = df[type_col].astype(str).str.lower().str.strip()
            df["transaction_type"] = np.where(
                raw_type.isin({"cr", "credit", "c", "deposit"}), "credit", "debit"
            )
        else:
            df["transaction_type"] = np.where(df["amount"] >= 0, "credit", "debit")
    else:
        raise ValueError("Cannot identify amount columns in CSV.")

    df["amount"] = df["amount"].abs()

    # ── Final tidy ─────────────────────────────────────────────────────
    df = df[["date", "description", "amount", "transaction_type"]].copy()
    df = df[df["amount"] > 0].reset_index(drop=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    logger.info("Preprocessing complete: %d rows", len(df))
    return df
