"""
app/utils/anomaly_detector.py
Isolation Forest–based anomaly detection on transaction amounts.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import RobustScaler

from config.settings import APP_CONFIG

logger = logging.getLogger(__name__)


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds `is_anomaly` (bool) and `anomaly_score` (float) columns.
    Only runs on debit transactions; credits are never flagged.
    Requires at least 10 debit rows to fit the model.
    """
    df = df.copy()
    df["is_anomaly"] = False
    df["anomaly_score"] = 0.0

    debit_mask = df["transaction_type"] == "debit"
    debit_df = df[debit_mask].copy()

    if len(debit_df) < 10:
        logger.warning("Too few debit rows (%d) for anomaly detection.", len(debit_df))
        return df

    # Feature engineering
    debit_df["day_of_week"] = debit_df["date"].dt.dayofweek
    debit_df["day_of_month"] = debit_df["date"].dt.day

    features = debit_df[["amount", "day_of_week", "day_of_month"]].values
    scaler = RobustScaler()
    features_scaled = scaler.fit_transform(features)

    iso = IsolationForest(
        contamination=APP_CONFIG.anomaly_contamination,
        random_state=42,
        n_estimators=200,
    )
    iso.fit(features_scaled)

    preds = iso.predict(features_scaled)       # -1 = anomaly, 1 = normal
    scores = iso.decision_function(features_scaled)  # negative = more anomalous

    df.loc[debit_mask, "is_anomaly"] = preds == -1
    df.loc[debit_mask, "anomaly_score"] = -scores  # flip so higher = more anomalous

    n_anomalies = int((preds == -1).sum())
    logger.info("Anomaly detection: %d / %d flagged.", n_anomalies, len(debit_df))
    return df
