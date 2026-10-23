from datetime import date
from pathlib import Path

import pandas as pd

from common import DB_PATH, OUTPUT_DIR
from week3_common import save_excel


EXPECTED_FILES = [
    "ml_day15_statistics_and_ab_template.xlsx",
    "ml_day16_logistic_baseline.xlsx",
    "ml_day17_pytorch_mlp.xlsx",
    "ml_day18_model_comparison.xlsx",
    "ml_day19_transformer_llm.xlsx",
    "ml_day20_spark_status.csv",
    "ml_day14_dashboard.xlsx",
    "ml_day14_report_draft.md",
]


def read_metric(path: Path, model_name: str) -> dict:
    if not path.exists():
        return {"model": model_name, "status": "missing"}
    try:
        frame = pd.read_csv(path)
        row = frame.iloc[0].to_dict()
        row["model"] = model_name
        row["status"] = "available"
        return row
    except Exception as error:
        return {
            "model": model_name,
            "status": f"read_error: {type(error).__name__}",
        }


def get_week2_table_status() -> pd.DataFrame:
    import duckdb

    if not DB_PATH.exists():
        return pd.DataFrame(
            [{"table_name": "database", "status": "missing"}]
        )
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        tables = connection.sql("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND (table_name LIKE 'week2_%' OR table_name LIKE 'week3_%')
            ORDER BY table_name
        """).df()
        if tables.empty:
            return pd.DataFrame(
                [{"table_name": "week2/week3 tables", "status": "missing"}]
            )
        tables["status"] = "available"
        return tables
    finally:
        connection.close()


def main() -> None:
    file_status = pd.DataFrame(
        [
            {
                "file": filename,
                "exists": (OUTPUT_DIR / filename).exists(),
            }
            for filename in EXPECTED_FILES
        ]
    )
    model_metrics = pd.DataFrame(
        [
            read_metric(
                OUTPUT_DIR / "ml_day16_logistic_metrics.csv",
                "logistic_baseline",
            ),
            read_metric(
                OUTPUT_DIR / "ml_day17_pytorch_metrics.csv",
                "pytorch_mlp",
            ),
            read_metric(
                OUTPUT_DIR / "ml_day18_model_comparison.csv",
                "day18_comparison",
            ),
        ]
    )
    table_status = get_week2_table_status()
    output = save_excel(
        {
            "file_status": file_status,
            "model_metrics": model_metrics,
            "table_status": table_status,
        },
        "ml_day21_final_acceptance.xlsx",
    )

    missing = file_status.loc[~file_status["exists"], "file"].tolist()
    available_models = model_metrics.loc[
        model_metrics["status"] == "available", "model"
    ].tolist()
    spark_status = (OUTPUT_DIR / "ml_day20_spark_status.csv").exists()
    missing_text = (
        "None" if not missing else "\n".join(f"- {item}" for item in missing)
    )
    summary = f"""# Day 21: Project Finalization

## 30-day project positioning

This is a reproducible public-data project simulating content-platform growth, recommendation, monitoring, and user-activity analysis. The project demonstrates SQL, Python, Excel, statistics, scikit-learn, PyTorch, optional Transformer inference, and PySpark execution where dependencies are available.

## Week 3 outputs

- Day 15: descriptive statistics, sampling, confidence intervals, hypothesis tests, correlation/causality distinction, and an A/B template.
- Day 16: time-aware logistic-regression baseline for future rating activity.
- Day 17: PyTorch MLP with Dataset, loss, optimizer, training history, validation, and saved weights.
- Day 18: feature engineering, model comparison, leakage checks, feature importance, and misclassified samples.
- Day 19: TF-IDF content-tag baseline plus optional pre-trained Transformer inference.
- Day 20: PySpark DataFrame metrics, join, window ranking, partitions, shuffle/plan artifacts, and Hadoop/Spark concepts.

## Current acceptance status

- Available model outputs: {', '.join(available_models) if available_models else 'None'}.
- PySpark status file present: {spark_status}.
- Missing expected files:

{missing_text}

## Limitations

MovieLens has ratings and tags but no registration, exposure, click, watch-time, demographic, campaign, or randomized experiment data. Future activity, retention, churn, and recommendation labels are proxies. No model result should be described as a real company's business result.

## Reproducibility

Use `code/README_week3.md` for the third-week run order. Keep the dataset under `dataset/ml-25m`, run data-processing scripts before model scripts, and record package versions and model metrics in the final project README.

Generated on: {date.today().isoformat()}
"""
    (OUTPUT_DIR / "ml_day21_final_summary.md").write_text(
        summary,
        encoding="utf-8",
    )
    readme = f"""# Content Platform Growth and Recommendation Analysis

This project uses MovieLens 25M as a public dataset to simulate a content-platform analysis. It is not a real company case study.

## Data

- Path: `dataset/ml-25m`.
- Main files: `ratings.csv`, `movies.csv`, and `tags.csv`.
- Rating events are used as a proxy for user activity.

## Tools

- SQL: DuckDB.
- Python: pandas, NumPy, scikit-learn, PyTorch, and optional Transformers/PySpark.
- Excel: KPI dashboards and result workbooks.
- R: secondary chart reproduction in Week 1.

## Run order

- Week 1: `code/README_week1.md`.
- Week 2: `code/README_week2.md`.
- Week 3: `code/README_week3.md`.

## Final status

The detailed acceptance status is in `days/ml_day21_final_acceptance.xlsx` and `days/ml_day21_final_summary.md`.

Generated on: {date.today().isoformat()}
"""
    (Path(__file__).resolve().parents[1] / "README.md").write_text(
        readme,
        encoding="utf-8",
    )
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
