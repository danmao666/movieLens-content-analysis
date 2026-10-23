from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from common import OUTPUT_DIR
from week3_common import (
    MODEL_FEATURES,
    classification_metrics,
    ensure_model_dir,
    save_excel,
    split_temporal_dataset,
)


ENHANCED_FEATURES = MODEL_FEATURES + [
    "activity_intensity_90d",
    "content_diversity_90d",
    "recent_activity_share",
    "rating_range_proxy",
]


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["activity_intensity_90d"] = (
        frame["behavior_count_90d"]
        / frame["active_days_90d"].clip(lower=1)
    )
    frame["content_diversity_90d"] = (
        frame["content_count_90d"]
        / frame["behavior_count_90d"].clip(lower=1)
    )
    frame["recent_activity_share"] = (
        frame["behavior_count_30d"]
        / frame["behavior_count_90d"].clip(lower=1)
    )
    frame["rating_range_proxy"] = (
        frame["rating_std_90d"].fillna(0)
        * frame["high_rating_share_90d"].fillna(0)
    )
    return frame.replace([np.inf, -np.inf], np.nan).fillna(0)


def evaluate_model(name, model, train, test, features):
    model.fit(train[features], train["target_future_active"])
    probabilities = model.predict_proba(test[features])[:, 1]
    metrics, predictions = classification_metrics(
        test["target_future_active"],
        probabilities,
    )
    metrics["model"] = name
    metrics["features"] = len(features)
    return metrics, predictions, probabilities, model


def main() -> None:
    dataset_path = OUTPUT_DIR / "ml_day16_model_dataset.csv"
    if not dataset_path.exists():
        raise FileNotFoundError(
            "Run code/day16_logistic_baseline.py before Day 18."
        )
    dataset = pd.read_csv(dataset_path)
    dataset["snapshot_cutoff"] = pd.to_datetime(dataset["snapshot_cutoff"])
    dataset = add_features(dataset)
    train, test = split_temporal_dataset(dataset)

    baseline = Pipeline(
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
    enhanced = RandomForestClassifier(
        n_estimators=120,
        max_depth=10,
        min_samples_leaf=10,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )

    baseline_metrics, baseline_predictions, baseline_probabilities, baseline = (
        evaluate_model(
            "logistic_with_enhanced_features",
            baseline,
            train,
            test,
            ENHANCED_FEATURES,
        )
    )
    forest_metrics, forest_predictions, forest_probabilities, enhanced = (
        evaluate_model(
            "random_forest_with_enhanced_features",
            enhanced,
            train,
            test,
            ENHANCED_FEATURES,
        )
    )
    comparison = pd.DataFrame([baseline_metrics, forest_metrics])

    best_name = "random_forest_with_enhanced_features"
    best_model = enhanced
    best_predictions = forest_predictions
    best_probabilities = forest_probabilities
    if forest_metrics["roc_auc"] < baseline_metrics["roc_auc"]:
        best_name = "logistic_with_enhanced_features"
        best_model = baseline
        best_predictions = baseline_predictions
        best_probabilities = baseline_probabilities

    errors = test[[
        "user_id",
        "snapshot_cutoff",
        "target_future_active",
    ]].copy()
    errors["predicted"] = best_predictions
    errors["predicted_probability"] = best_probabilities
    errors["error_type"] = np.select(
        [
            (errors["target_future_active"] == 1) & (errors["predicted"] == 0),
            (errors["target_future_active"] == 0) & (errors["predicted"] == 1),
        ],
        ["false_negative", "false_positive"],
        default="correct",
    )
    errors = errors[errors["error_type"] != "correct"].sort_values(
        "predicted_probability",
        ascending=False,
    )

    leakage_checks = []
    forbidden_tokens = ["target", "future", "label", "post"]
    for feature in ENHANCED_FEATURES:
        leakage_checks.append(
            {
                "feature": feature,
                "contains_forbidden_token": any(
                    token in feature.lower() for token in forbidden_tokens
                ),
                "source_period": "at or before snapshot cutoff",
            }
        )
    leakage_report = pd.DataFrame(leakage_checks)
    leakage_report.loc[len(leakage_report)] = {
        "feature": "target_future_active",
        "contains_forbidden_token": True,
        "source_period": "label only; excluded from features",
    }

    confusion = confusion_matrix(
        test["target_future_active"],
        best_predictions,
        labels=[0, 1],
    )
    display = ConfusionMatrixDisplay(
        confusion_matrix=confusion,
        display_labels=["inactive", "active"],
    )
    display.plot(cmap="Purples")
    plt.title(f"Day 18 Best Model: {best_name}")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day18_best_model_confusion_matrix.png", dpi=150)
    plt.close()

    if hasattr(best_model, "feature_importances_"):
        importance = pd.DataFrame(
            {
                "feature": ENHANCED_FEATURES,
                "importance": best_model.feature_importances_,
            }
        ).sort_values("importance", ascending=False)
    else:
        coefficients = best_model.named_steps["logistic"].coef_[0]
        importance = pd.DataFrame(
            {
                "feature": ENHANCED_FEATURES,
                "importance": np.abs(coefficients),
            }
        ).sort_values("importance", ascending=False)

    model_dir = ensure_model_dir()
    import pickle

    with (model_dir / "day18_best_model.pkl").open("wb") as file:
        pickle.dump(best_model, file)
    output = save_excel(
        {
            "model_comparison": comparison,
            "feature_importance": importance,
            "misclassified_samples": errors.head(10000),
            "leakage_checks": leakage_report,
        },
        "ml_day18_model_comparison.xlsx",
    )
    comparison.to_csv(
        OUTPUT_DIR / "ml_day18_model_comparison.csv",
        index=False,
        encoding="utf-8-sig",
    )
    errors.to_csv(
        OUTPUT_DIR / "ml_day18_misclassified_samples.csv",
        index=False,
        encoding="utf-8-sig",
    )
    leakage_report.to_csv(
        OUTPUT_DIR / "ml_day18_leakage_checks.csv",
        index=False,
        encoding="utf-8-sig",
    )
    report = f"""# Day 18: Feature Engineering and Model Comparison

## Models

- Logistic regression with standardized enhanced features.
- Random forest with the same enhanced features.
- Temporal test data is kept at the later snapshot cutoff.

## Comparison

{comparison.to_string(index=False)}

The selected best model for the error analysis is `{best_name}` based on test ROC-AUC. The selection is a baseline comparison, not a production model-selection process.

## Feature engineering

- Activity intensity: behavior count divided by active days.
- Content diversity: distinct contents divided by behavior count.
- Recent activity share: 30-day behavior divided by 90-day behavior.
- Rating range proxy: rating standard deviation multiplied by high-rating share.

## Error analysis

False positives and false negatives are saved in `ml_day18_misclassified_samples.csv`. Review these rows for sparse histories, borderline probabilities, and user behavior patterns rather than only reporting a single score.

## Leakage audit

The feature audit explicitly excludes `target_future_active` and any future/post-event feature. All features are computed from events at or before the snapshot cutoff. Rebuilding features after the label window would invalidate the evaluation.

## Limitations

The target is future rating activity, not confirmed churn or conversion. The model has no exposure, recommendation, demographic, or product context.

Generated on: {date.today().isoformat()}
"""
    (OUTPUT_DIR / "ml_day18_model_comparison.md").write_text(
        report,
        encoding="utf-8",
    )
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
