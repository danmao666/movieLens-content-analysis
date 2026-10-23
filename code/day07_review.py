from datetime import date

import pandas as pd

from common import OUTPUT_DIR, connect, require_tables


METRICS = [
    {
        "metric": "DAU",
        "definition": "Distinct users with at least one rating on a date.",
        "sql_logic": "COUNT(DISTINCT user_id) grouped by event_date",
    },
    {
        "metric": "New users",
        "definition": "Users whose first observed rating date is the current date.",
        "sql_logic": "first_active_date = date_day",
    },
    {
        "metric": "Behavior count",
        "definition": "Number of rating records on a date.",
        "sql_logic": "COUNT(*) grouped by event_date",
    },
    {
        "metric": "Active content",
        "definition": "Distinct movies receiving at least one rating on a date.",
        "sql_logic": "COUNT(DISTINCT content_id) grouped by event_date",
    },
    {
        "metric": "D7 retention",
        "definition": "Share of first-active-day users active exactly seven days later.",
        "sql_logic": "event_date = first_date + INTERVAL '7 days'",
    },
    {
        "metric": "User churn proxy",
        "definition": "A user with no later observed rating for the chosen inactivity window.",
        "sql_logic": "last_active_date plus an inactivity threshold",
    },
]


def write_report(
    output_path,
    daily: pd.DataFrame,
    content: pd.DataFrame,
    retention: pd.DataFrame,
) -> None:
    max_dau_row = daily.loc[daily["dau"].idxmax()]
    min_dau_row = daily.loc[daily["dau"].idxmin()]
    top_content = content.iloc[0]

    cohort_users = retention["cohort_users"].sum()
    retained_users = retention["retained_on_day_7"].sum()
    d7_rate = retained_users / cohort_users if cohort_users else 0

    report = f"""# Week 1 Review: Simulated Content Platform Analysis

## 1. Business question

This project uses the public MovieLens 25M dataset to simulate analysis for a content platform. The first-week focus is user activity, content performance, retention, data quality, and metric monitoring.

## 2. Metric definitions

- DAU: distinct users with at least one rating on a date.
- Behavior count: number of rating records on a date.
- Active content: distinct movies receiving a rating on a date.
- D7 retention: first-active-day users with an observed rating exactly seven days later.
- Churn proxy: a user whose last observed rating is followed by the selected inactivity window without another rating.

## 3. Data findings

- Highest DAU date: {max_dau_row['date_day']} with {int(max_dau_row['dau']):,} users.
- Lowest DAU date: {min_dau_row['date_day']} with {int(min_dau_row['dau']):,} users.
- Highest-activity content after the minimum-volume filter: {top_content['title']} with {int(top_content['active_users']):,} active users.
- Observed D7 retention across eligible cohorts: {d7_rate:.2%}.
- Potential DAU anomaly dates are marked in `ml_day04_daily_metrics.csv` and the Day 5 workbook.

## 4. Interpretation

These findings describe observed rating activity. They do not prove why users were active or inactive. Content popularity should be evaluated together with volume, active users, and average rating rather than average rating alone.

## 5. Suggested actions

1. Monitor DAU, behavior count, and active content together.
2. Examine high-active-user content for recommendation and related-content opportunities.
3. Segment users by observed behavior frequency before designing re-engagement experiments.
4. Investigate flagged dates against data pipeline and product-event logs when those logs are available.

## 6. Validation plan

Test a recommendation change with user-level randomization. Use D7 activity or rating activity as a primary metric, and monitor rating count per user, content diversity, and negative feedback as guardrail metrics.

## 7. Limitations

MovieLens contains ratings and tags, not impressions, clicks, watch time, registration dates, user demographics, or product release logs. The project is a simulated business analysis and must not be presented as a real company's business result.

Generated on: {date.today().isoformat()}
"""
    output_path.write_text(report, encoding="utf-8")


def main() -> None:
    connection = connect()
    try:
        require_tables(
            connection,
            "daily_metrics",
            "behavior_fact",
            "content_dim",
        )

        daily = connection.sql("""
            SELECT *
            FROM daily_metrics
            ORDER BY date_day
        """).df()
        content = connection.sql("""
            SELECT
                c.title,
                c.genres,
                COUNT(*) AS behavior_count,
                COUNT(DISTINCT b.user_id) AS active_users,
                ROUND(AVG(b.rating), 2) AS avg_rating
            FROM behavior_fact b
            JOIN content_dim c ON b.content_id = c.content_id
            GROUP BY c.content_id, c.title, c.genres
            HAVING COUNT(*) >= 100
            ORDER BY active_users DESC
            LIMIT 100
        """).df()
        retention = connection.sql("""
            WITH first_active AS (
                SELECT user_id, MIN(event_date) AS first_date
                FROM behavior_fact
                GROUP BY user_id
            )
            SELECT
                f.first_date,
                COUNT(DISTINCT f.user_id) AS cohort_users,
                COUNT(DISTINCT CASE
                    WHEN b.event_date = f.first_date + INTERVAL '7 days'
                    THEN f.user_id
                END) AS retained_on_day_7
            FROM first_active f
            LEFT JOIN behavior_fact b ON f.user_id = b.user_id
            GROUP BY f.first_date
            ORDER BY f.first_date
        """).df()

        daily.to_csv(
            OUTPUT_DIR / "ml_day07_daily_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        pd.DataFrame(METRICS).to_excel(
            OUTPUT_DIR / "ml_day07_metric_dictionary.xlsx",
            index=False,
        )
        write_report(
            OUTPUT_DIR / "ml_day07_one_page_conclusion.md",
            daily,
            content,
            retention,
        )
        print("Saved day 7 metrics, metric dictionary, and conclusion.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
