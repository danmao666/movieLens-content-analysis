from datetime import date
from pathlib import Path

import pandas as pd

from common import DB_PATH, OUTPUT_DIR
from week4_common import PORTFOLIO_DIR, save_excel


PROJECT_DIR = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "content_platform.duckdb",
    "README.md",
    "code/README_week1.md",
    "code/README_week2.md",
    "code/README_week3.md",
    "code/README_week4.md",
    "days/ml_day14_dashboard.xlsx",
    "days/ml_day23_end_to_end_analysis.xlsx",
    "days/ml_day23_end_to_end_report.md",
    "days/ml_day22_sql_timed_test.xlsx",
    "days/ml_day25_data_interview_questions.xlsx",
    "days/ml_day26_ai_interview.xlsx",
    "days/ml_day27_resume_versions.xlsx",
    "days/ml_day28_project_presentation.xlsx",
    "days/ml_day29_weakness_remediation.xlsx",
    "portfolio/README.md",
    "portfolio/DATA_DICTIONARY.csv",
    "portfolio/DATA_LIMITATIONS.md",
    "portfolio/resume_bytedance.md",
    "portfolio/resume_pdd.md",
    "portfolio/resume_bilibili.md",
    "models/day16_logistic_baseline.pkl",
    "models/day17_pytorch_mlp.pt",
    "models/day18_best_model.pkl",
]


def announcement_template() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "source",
            "announcement_date",
            "organization",
            "position",
            "location",
            "employment_type",
            "requirements",
            "keyword_match",
            "evidence_link",
            "source_checked_at",
            "verification_status",
            "reviewer",
            "notes",
        ]
    )


def application_template() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "company",
            "position",
            "target_version",
            "source_link",
            "deadline",
            "applied_date",
            "status",
            "contact",
            "next_action",
            "next_action_date",
            "notes",
        ]
    )


def main() -> None:
    file_status = pd.DataFrame(
        [
            {
                "path": path,
                "exists": (PROJECT_DIR / path).exists(),
                "size_bytes": (PROJECT_DIR / path).stat().st_size
                if (PROJECT_DIR / path).exists()
                else 0,
            }
            for path in REQUIRED_FILES
        ]
    )
    source_files = pd.DataFrame(
        [
            {
                "area": "Week 1",
                "target": "SQL/Python/Excel/R foundations",
                "status": "complete",
                "evidence": "code/day01-day07 and days/ml_day01-ml_day07",
            },
            {
                "area": "Week 2",
                "target": "business analysis/dashboard/experiment",
                "status": "complete",
                "evidence": "code/day08-day14 and days/ml_day08-ml_day14",
            },
            {
                "area": "Week 3",
                "target": "statistics/ML/PyTorch/Spark",
                "status": "complete with stated limits",
                "evidence": "code/day15-day21 and days/ml_day15-ml_day21",
            },
            {
                "area": "Week 4",
                "target": "mock work/interview/resume/application readiness",
                "status": "complete as templates and generated materials",
                "evidence": "code/day22-day30 and portfolio/",
            },
        ]
    )
    application = application_template()
    announcements = announcement_template()
    acceptance = pd.DataFrame(
        [
            {
                "criterion": "SQL 50-70 questions",
                "status": "requires learner practice log",
                "evidence": "sql/ and Day 22 timed test",
                "next_step": "Complete timed attempt and record score.",
            },
            {
                "criterion": "Python EDA notebook",
                "status": "complete via scripts/workbooks",
                "evidence": "code/day06_eda.py and ml_day06_eda_results.xlsx",
                "next_step": "Explain every chart in interview.",
            },
            {
                "criterion": "Dashboard",
                "status": "complete",
                "evidence": "ml_day14_dashboard.xlsx and ml_day23_end_to_end_analysis.xlsx",
                "next_step": "Open workbook and verify formulas/charts before submission.",
            },
            {
                "criterion": "A/B experiment",
                "status": "complete as design",
                "evidence": "ml_day13_ab_experiment_plan.md",
                "next_step": "Memorize primary/guardrail metric rationale.",
            },
            {
                "criterion": "PyTorch model",
                "status": "complete",
                "evidence": "ml_day17_pytorch_metrics.csv and models/day17_pytorch_mlp.pt",
                "next_step": "Explain train/validation/test and error analysis.",
            },
            {
                "criterion": "PySpark task",
                "status": "complete on reproducible local sample",
                "evidence": "ml_day20_spark_status.csv and physical plan",
                "next_step": "State sample limitation; explain how full run needs more memory.",
            },
            {
                "criterion": "Resume and portfolio",
                "status": "draft ready for personal details",
                "evidence": "portfolio/resume_*.md and portfolio/README.md",
                "next_step": "Add true personal information and tailor to each JD.",
            },
            {
                "criterion": "Application materials",
                "status": "templates ready",
                "evidence": "announcement and application templates",
                "next_step": "Fill only verified openings with source links and dates.",
            },
        ]
    )

    output = save_excel(
        {
            "acceptance": acceptance,
            "file_status": file_status,
            "week_status": source_files,
            "application_tracker": application,
            "announcement_template": announcements,
        },
        "ml_day30_final_acceptance.xlsx",
    )
    file_status.to_csv(
        OUTPUT_DIR / "ml_day30_file_status.csv",
        index=False,
        encoding="utf-8-sig",
    )
    acceptance.to_csv(
        OUTPUT_DIR / "ml_day30_acceptance_checklist.csv",
        index=False,
        encoding="utf-8-sig",
    )
    application.to_csv(
        OUTPUT_DIR / "ml_day30_application_tracker.csv",
        index=False,
        encoding="utf-8-sig",
    )
    announcements.to_csv(
        OUTPUT_DIR / "ml_day30_announcement_information_template.csv",
        index=False,
        encoding="utf-8-sig",
    )

    missing = file_status.loc[~file_status["exists"], "path"].tolist()
    missing_text = "None" if not missing else "\n".join(f"- {item}" for item in missing)
    report = f"""# Day 30: Final Acceptance and Application Readiness

## Final status

The project contains a complete public-data portfolio from SQL analysis through model and interview materials. Missing personal information, a human timed SQL score, and real job-application records cannot be fabricated by code.

## Missing required files

{missing_text}

## Before sending an application

1. Add real name, contact, education, location, availability, and work authorization to the selected resume.
2. Read the actual job description and remove keywords that are not supported by the project.
3. Open the dashboard and verify that metrics, dates, and charts are legible.
4. Practice the ten-minute explanation and answer the SQL/AI questions without reading.
5. Fill the application tracker only with verified source links, dates, and status.
6. Keep an evidence link and verification status for every announcement record.

## Honest positioning

Lead with data analysis, content analysis, and business analysis applications. Present AI/PyTorch/Spark as concrete baseline project work with measured limits, not as “expert” or “full-scale production” experience.

Generated on: {date.today().isoformat()}
"""
    (OUTPUT_DIR / "ml_day30_final_acceptance.md").write_text(
        report,
        encoding="utf-8",
    )
    print(f"Saved: {output}")


if __name__ == "__main__":
    main()
