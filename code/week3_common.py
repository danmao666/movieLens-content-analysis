from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from common import DB_PATH, OUTPUT_DIR, connect, require_tables


MODEL_DIR = Path(__file__).resolve().parents[1] / "models"

MODEL_FEATURES = [
    "behavior_count_30d",
    "behavior_count_90d",
    "active_days_90d",
    "content_count_90d",
    "avg_rating_90d",
    "rating_std_90d",
    "high_rating_share_90d",
    "days_since_last_activity",
]


def connect_week3():
    return connect()


def require_week3_tables(connection, *table_names: str) -> None:
    require_tables(connection, *table_names)


def ensure_model_dir() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    return MODEL_DIR




def save_excel(sheets: dict, filename: str) -> Path:
    output_path = OUTPUT_DIR / filename
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output_path




def get_dataset_end_date(connection) -> date:
    value = connection.sql(
        "SELECT MAX(event_date) AS max_date FROM behavior_fact"
    ).df().iloc[0]["max_date"]
    return pd.Timestamp(value).date()


def _sql_date(value: date) -> str:
    return value.isoformat()


def build_snapshot_features(
    connection,
    cutoff: date,
    horizon_days: int = 30,
    lookback_days: int = 90,
) -> pd.DataFrame:
    """Create a point-in-time user feature table and future-activity label.

    Every feature is calculated at or before the cutoff. The target only uses
    events after the cutoff, which keeps the temporal model split auditable.
    """
    feature_start = cutoff - timedelta(days=lookback_days)
    future_end = cutoff + timedelta(days=horizon_days)
    cutoff_sql = _sql_date(cutoff)
    start_sql = _sql_date(feature_start)
    future_end_sql = _sql_date(future_end)

    query = f"""
        WITH eligible AS (
            SELECT
                user_id,
                MAX(event_date) AS last_activity_before_cutoff
            FROM behavior_fact
            WHERE event_date <= DATE '{cutoff_sql}'
            GROUP BY user_id
        ), history AS (
            SELECT
                e.user_id,
                SUM(CASE
                    WHEN b.event_date > DATE '{cutoff_sql}' - INTERVAL '30 days'
                    THEN 1 ELSE 0
                END) AS behavior_count_30d,
                COUNT(*) AS behavior_count_90d,
                COUNT(DISTINCT b.event_date) AS active_days_90d,
                COUNT(DISTINCT b.content_id) AS content_count_90d,
                AVG(b.rating) AS avg_rating_90d,
                STDDEV_SAMP(b.rating) AS rating_std_90d,
                AVG(CASE WHEN b.rating >= 4 THEN 1.0 ELSE 0.0 END)
                    AS high_rating_share_90d
            FROM eligible e
            JOIN behavior_fact b
                ON e.user_id = b.user_id
               AND b.event_date BETWEEN DATE '{start_sql}'
                   AND DATE '{cutoff_sql}'
            GROUP BY e.user_id
        ), labels AS (
            SELECT
                e.user_id,
                CASE WHEN COUNT(f.user_id) > 0 THEN 1 ELSE 0 END
                    AS target_future_active
            FROM eligible e
            LEFT JOIN behavior_fact f
                ON e.user_id = f.user_id
               AND f.event_date > DATE '{cutoff_sql}'
               AND f.event_date <= DATE '{future_end_sql}'
            GROUP BY e.user_id
        )
        SELECT
            h.user_id,
            DATE '{cutoff_sql}' AS snapshot_cutoff,
            h.behavior_count_30d,
            h.behavior_count_90d,
            h.active_days_90d,
            h.content_count_90d,
            h.avg_rating_90d,
            h.rating_std_90d,
            h.high_rating_share_90d,
            DATE_DIFF(
                'day',
                e.last_activity_before_cutoff,
                DATE '{cutoff_sql}'
            ) AS days_since_last_activity,
            l.target_future_active
        FROM history h
        JOIN eligible e ON h.user_id = e.user_id
        JOIN labels l ON h.user_id = l.user_id
    """
    frame = connection.sql(query).df()
    frame["snapshot_cutoff"] = pd.to_datetime(frame["snapshot_cutoff"])
    numeric_columns = MODEL_FEATURES + ["target_future_active"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame[numeric_columns] = frame[numeric_columns].replace(
        [np.inf, -np.inf], np.nan
    )
    frame["rating_std_90d"] = frame["rating_std_90d"].fillna(0.0)
    frame = frame.dropna(subset=MODEL_FEATURES + ["target_future_active"])
    return frame


def build_temporal_model_dataset(connection) -> pd.DataFrame:
    max_date = get_dataset_end_date(connection)
    train_cutoff = max_date - timedelta(days=60)
    test_cutoff = max_date - timedelta(days=30)
    train = build_snapshot_features(connection, train_cutoff)
    test = build_snapshot_features(connection, test_cutoff)
    dataset = pd.concat([train, test], ignore_index=True)
    dataset = dataset.sort_values(["snapshot_cutoff", "user_id"]).reset_index(
        drop=True
    )
    return dataset


def split_temporal_dataset(dataset: pd.DataFrame):
    cutoffs = sorted(dataset["snapshot_cutoff"].dropna().unique())
    if len(cutoffs) < 2:
        raise ValueError("Expected separate train and test snapshot cutoffs.")
    train = dataset[dataset["snapshot_cutoff"] == cutoffs[0]].copy()
    test = dataset[dataset["snapshot_cutoff"] == cutoffs[-1]].copy()
    return train, test


def classification_metrics(y_true, probabilities, threshold: float = 0.5):
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        balanced_accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )

    predictions = (np.asarray(probabilities) >= threshold).astype(int)
    result = {
        "accuracy": accuracy_score(y_true, predictions),
        "balanced_accuracy": balanced_accuracy_score(y_true, predictions),
        "precision": precision_score(y_true, predictions, zero_division=0),
        "recall": recall_score(y_true, predictions, zero_division=0),
        "f1": f1_score(y_true, predictions, zero_division=0),
    }
    if len(np.unique(y_true)) == 2:
        result["roc_auc"] = roc_auc_score(y_true, probabilities)
        result["average_precision"] = average_precision_score(
            y_true, probabilities
        )
    else:
        result["roc_auc"] = np.nan
        result["average_precision"] = np.nan
    return result, predictions
