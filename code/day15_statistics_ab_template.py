from datetime import date

import numpy as np
import pandas as pd
from scipy import stats

from common import OUTPUT_DIR
from week3_common import connect_week3, require_week3_tables, save_excel


def bootstrap_mean_ci(values, iterations=2000, seed=42):
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    samples = rng.choice(
        values,
        size=(iterations, len(values)),
        replace=True,
    ).mean(axis=1)
    return np.quantile(samples, [0.025, 0.975])


def main() -> None:
    connection = connect_week3()
    try:
        require_week3_tables(connection, "week2_daily_metrics")
        daily = connection.sql("""
            SELECT
                date_day,
                weekday,
                dau,
                behavior_count,
                active_content_count,
                new_users
            FROM week2_daily_metrics
            WHERE behavior_count > 0
            ORDER BY date_day
        """).df()
        daily["date_day"] = pd.to_datetime(daily["date_day"])
        daily["period"] = np.where(
            daily["weekday"].isin([0, 6]), "weekend", "weekday"
        )

        sampled = daily.sample(
            n=min(30, len(daily)),
            random_state=42,
        )
        mean_ci = bootstrap_mean_ci(daily["dau"])
        weekend = daily.loc[daily["period"] == "weekend", "dau"]
        weekday = daily.loc[daily["period"] == "weekday", "dau"]
        t_test = stats.ttest_ind(
            weekend,
            weekday,
            equal_var=False,
            nan_policy="omit",
        )
        mann_whitney = stats.mannwhitneyu(
            weekend,
            weekday,
            alternative="two-sided",
        )
        correlation = stats.pearsonr(
            daily["dau"],
            daily["behavior_count"],
        )

        summary = pd.DataFrame(
            [
                {
                    "analysis": "DAU mean",
                    "sample_size": len(daily),
                    "estimate": daily["dau"].mean(),
                    "variance": daily["dau"].var(ddof=1),
                    "ci_lower": mean_ci[0],
                    "ci_upper": mean_ci[1],
                    "p_value": np.nan,
                    "interpretation": "Bootstrap 95% CI for observed daily DAU mean.",
                },
                {
                    "analysis": "Weekend vs weekday DAU Welch t-test",
                    "sample_size": len(weekend) + len(weekday),
                    "estimate": weekend.mean() - weekday.mean(),
                    "variance": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": t_test.pvalue,
                    "interpretation": "Observational difference; not a causal weekend effect.",
                },
                {
                    "analysis": "Weekend vs weekday Mann-Whitney test",
                    "sample_size": len(weekend) + len(weekday),
                    "estimate": weekend.median() - weekday.median(),
                    "variance": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": mann_whitney.pvalue,
                    "interpretation": "Distribution comparison for observed daily DAU.",
                },
                {
                    "analysis": "DAU vs behavior count Pearson correlation",
                    "sample_size": len(daily),
                    "estimate": correlation.statistic,
                    "variance": np.nan,
                    "ci_lower": np.nan,
                    "ci_upper": np.nan,
                    "p_value": correlation.pvalue,
                    "interpretation": "Correlation is not evidence of causality.",
                },
            ]
        )
        sample_profile = sampled.describe().T.reset_index().rename(
            columns={"index": "variable"}
        )
        sample_profile["sampling_method"] = "Simple random sample, seed=42"
        ab_template = pd.DataFrame(
            [
                {
                    "field": "hypothesis",
                    "value": "Personalized recommendations increase seven-day rating-active rate.",
                },
                {
                    "field": "unit",
                    "value": "User, with persistent assignment.",
                },
                {
                    "field": "primary_metric",
                    "value": "Users with at least one rating in days 1-7 / eligible assigned users.",
                },
                {
                    "field": "guardrails",
                    "value": "Ratings per user, content diversity, average rating, low-rating share, event completeness.",
                },
                {"field": "alpha", "value": 0.05},
                {"field": "confidence_level", "value": 0.95},
                {"field": "power", "value": 0.80},
                {
                    "field": "reporting",
                    "value": "Absolute lift, relative lift, p-value, and confidence interval.",
                },
                {
                    "field": "causal_requirement",
                    "value": "Random assignment and pre-declared analysis; observational MovieLens data cannot estimate the A/B effect.",
                },
            ]
        )
        output = save_excel(
            {
                "statistical_summary": summary,
                "sample_profile": sample_profile,
                "ab_template": ab_template,
            },
            "ml_day15_statistics_and_ab_template.xlsx",
        )
        summary.to_csv(
            OUTPUT_DIR / "ml_day15_statistical_summary.csv",
            index=False,
            encoding="utf-8-sig",
        )
        # sample_profile 只写 Excel，不单独导出 CSV
        ab_template.to_csv(
            OUTPUT_DIR / "ml_day15_ab_template.csv",
            index=False,
            encoding="utf-8-sig",
        )
        report = f"""# Day 15: Statistics and A/B Analysis Template

## Observed descriptive statistics

- Active-day observations: {len(daily):,}.
- Mean DAU: {daily['dau'].mean():,.2f}.
- Sample variance of DAU: {daily['dau'].var(ddof=1):,.2f}.
- Bootstrap 95% confidence interval for mean DAU: [{mean_ci[0]:,.2f}, {mean_ci[1]:,.2f}].
- Pearson correlation between DAU and rating volume: {correlation.statistic:.4f}, p-value {correlation.pvalue:.4g}.

## Sampling and inference

A reproducible simple random sample of at most 30 active days is saved in the workbook. The weekend/weekday tests describe observational differences. They do not establish that the day type caused the difference because time, user mix, and content mix are not randomized.

## A/B template

The proposed recommendation experiment uses user-level randomization, a seven-day rating-active primary metric, guardrail metrics, alpha 0.05, 95% confidence intervals, and 80% target power. MovieLens does not contain randomized variants, so no treatment effect is reported here.

Generated on: {date.today().isoformat()}
"""
        (OUTPUT_DIR / "ml_day15_statistics_and_ab_template.md").write_text(
            report,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
