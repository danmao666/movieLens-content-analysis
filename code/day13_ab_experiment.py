from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week2_common import connect_week2, require_week2_tables


PLAN_ROWS = [
    {
        "item": "Experiment hypothesis",
        "design": "A personalized recommendation strategy increases the share of users with a rating activity in the following seven days compared with the current strategy.",
    },
    {
        "item": "Randomization unit",
        "design": "User-level randomization with persistent assignment. Do not randomize individual content impressions if users can receive both treatments.",
    },
    {
        "item": "Control",
        "design": "Existing recommendation or ranking strategy.",
    },
    {
        "item": "Treatment",
        "design": "Personalized recommendation strategy defined before launch, with the same user eligibility rules as control.",
    },
    {
        "item": "Primary metric",
        "design": "Seven-day rating-active rate: the share of assigned users with at least one rating event in the seven-day measurement window.",
    },
    {
        "item": "Guardrail metrics",
        "design": "Ratings per active user, distinct contents rated, average rating, low-rating share, assignment balance, and data completeness.",
    },
    {
        "item": "Significance",
        "design": "Two-sided test with alpha = 0.05. Report absolute lift, relative lift, 95% confidence interval, and p-value.",
    },
    {
        "item": "Power and sample size",
        "design": "Set power to 80% and define the minimum detectable effect using a pre-experiment baseline. Do not claim a sample size until the baseline and traffic capacity are known.",
    },
    {
        "item": "Experiment checks",
        "design": "Check sample-ratio mismatch, duplicate exposure, cross-device contamination, missing events, eligibility drift, and early stopping rules before reading results.",
    },
    {
        "item": "Decision rule",
        "design": "Ship only if the primary metric improves with a 95% interval excluding zero, no material guardrail degradation occurs, and data-quality checks pass.",
    },
]


def main() -> None:
    connection = connect_week2()
    try:
        require_week2_tables(connection, "week2_daily_metrics")
        profile = connection.sql("""
            SELECT
                COUNT(DISTINCT user_id) AS observed_users,
                MIN(event_date) AS first_date,
                MAX(event_date) AS last_date
            FROM behavior_fact
        """).df().iloc[0]

        plan = pd.DataFrame(PLAN_ROWS)
        plan.to_csv(
            OUTPUT_DIR / "ml_day13_ab_experiment_plan.csv",
            index=False,
            encoding="utf-8-sig",
        )

        report = f"""# Day 13: Recommendation A/B Experiment Plan

## Context

This is a proposed experiment for the simulated content-platform project. The MovieLens dataset contains historical ratings, not randomized treatment and control assignments. Therefore this document defines a future experiment; it does not report an experiment result.

The source data includes {int(profile['observed_users']):,} observed users between {profile['first_date']} and {profile['last_date']}. These figures describe data scale only and must not be used as the required experiment sample size.

## Hypothesis

A personalized recommendation strategy increases the probability that an eligible user produces at least one rating in the following seven days, without reducing content diversity or rating quality.

## Design

- **Randomization unit:** user.
- **Assignment:** persistent 50/50 control and treatment assignment where possible.
- **Control:** current recommendation or ranking logic.
- **Treatment:** pre-specified personalized recommendation logic.
- **Primary metric:** seven-day rating-active rate.
- **Guardrails:** ratings per active user, distinct contents rated, average rating, low-rating share, sample-ratio mismatch, and event completeness.

## Statistical plan

Use a two-sided test with alpha = 0.05, 80% power, and a pre-declared minimum detectable effect. Report absolute lift, relative lift, p-value, and a 95% confidence interval. Calculate sample size from a real pre-experiment baseline and expected traffic; the public historical data does not provide a valid randomized baseline.

Do not repeatedly inspect and stop based only on a temporary p-value. Define the experiment duration, eligibility rules, exclusion rules, and stopping criteria before launch.

## Risks and checks

Check sample-ratio mismatch, duplicate users, users receiving both treatments, missing activity events, changes in eligible population, and guardrail deterioration. A statistically significant result is not sufficient if data quality or user experience guardrails fail.

## Decision rule

Ship the treatment only if the primary metric improves, the 95% confidence interval excludes zero, no material guardrail worsens, and all assignment and data-quality checks pass.

Generated on: {date.today().isoformat()}
"""
        (OUTPUT_DIR / "ml_day13_ab_experiment_plan.md").write_text(
            report,
            encoding="utf-8",
        )
        print("Saved Day 13 A/B experiment plan.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
