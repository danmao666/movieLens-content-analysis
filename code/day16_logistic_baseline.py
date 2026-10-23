import pickle
from datetime import date

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import OUTPUT_DIR
from week3_common import (
    MODEL_FEATURES,
    build_temporal_model_dataset,
    classification_metrics,
    connect_week3,
    ensure_model_dir,
    require_week3_tables,
    save_excel,
    split_temporal_dataset,
)


def main() -> None:
    connection = connect_week3()
    try:
        require_week3_tables(connection, "behavior_fact", "content_dim")
        dataset = build_temporal_model_dataset(connection)
        dataset_path = OUTPUT_DIR / "ml_day16_model_dataset.csv"
        dataset.to_csv(dataset_path, index=False, encoding="utf-8-sig")
        train, test = split_temporal_dataset(dataset)

        model = Pipeline(
            [
                ("scale", StandardScaler()),
                (
                    "logistic",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=42,
                    ),
                ),
            ]
        )
        model.fit(train[MODEL_FEATURES], train["target_future_active"])
        probabilities = model.predict_proba(test[MODEL_FEATURES])[:, 1]
        metrics, predictions = classification_metrics(
            test["target_future_active"],
            probabilities,
        )
        metrics.update(
            {
                "model": "logistic_baseline",
                "train_rows": len(train),
                "test_rows": len(test),
                "train_cutoff": str(train["snapshot_cutoff"].iloc[0].date()),
                "test_cutoff": str(test["snapshot_cutoff"].iloc[0].date()),
                "positive_rate_train": train["target_future_active"].mean(),
                "positive_rate_test": test["target_future_active"].mean(),
            }
        )
        metrics_frame = pd.DataFrame([metrics])
        confusion = confusion_matrix(
            test["target_future_active"],
            predictions,
            labels=[0, 1],
        )
        confusion_frame = pd.DataFrame(
            confusion,
            index=["actual_0", "actual_1"],
            columns=["predicted_0", "predicted_1"],
        ).reset_index(names="actual")

        model_dir = ensure_model_dir()
        with (model_dir / "day16_logistic_baseline.pkl").open("wb") as file:
            pickle.dump(model, file)

        display = ConfusionMatrixDisplay(
            confusion_matrix=confusion,
            display_labels=["inactive", "active"],
        )
        display.plot(cmap="Blues")
        plt.title("Day 16 Logistic Baseline")
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / "ml_day16_logistic_confusion_matrix.png", dpi=150)
        plt.close()

        output = save_excel(
            {
                "metrics": metrics_frame,
                "confusion_matrix": confusion_frame,
                "feature_list": pd.DataFrame({"feature": MODEL_FEATURES}),
                "test_predictions": test.assign(
                    predicted=predictions,
                    predicted_probability=probabilities,
                ).head(10000),
            },
            "ml_day16_logistic_baseline.xlsx",
        )
        metrics_frame.to_csv(
            OUTPUT_DIR / "ml_day16_logistic_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        report = f"""# Day 16: Logistic Regression Baseline

## Target

`target_future_active = 1` means that a user with observed activity before the snapshot cutoff has at least one rating in the following 30 days. This is a future-rating activity proxy, not a confirmed churn label.

## Temporal split

- Train snapshot: {metrics['train_cutoff']}.
- Test snapshot: {metrics['test_cutoff']}.
- Feature lookback: 90 days, calculated only on or before each snapshot cutoff.
- Evaluation horizon: 30 days after each cutoff.

## Metrics

{metrics_frame.to_string(index=False)}

## Leakage controls

The model excludes future events from features. `target_future_active` is retained only as the label. The temporal test snapshot is later than the training snapshot and is not randomly mixed with training rows.

## Limitations

The target represents rating activity and the features contain no registration, exposure, or user-demographic information. Results should be used as a baseline for model development, not as a production churn score.

Generated on: {date.today().isoformat()}
"""
        (OUTPUT_DIR / "ml_day16_logistic_baseline.md").write_text(
            report,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
