import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import OUTPUT_DIR
from week2_common import connect_week2, require_week2_tables, save_excel


DAILY_TRENDS_SQL = """
    CREATE OR REPLACE TABLE week2_daily_trends AS
    SELECT
        m.*,
        LAG(dau) OVER (ORDER BY date_day) AS previous_dau,
        LAG(behavior_count) OVER (ORDER BY date_day) AS previous_behavior_count,
        AVG(dau) OVER (
            ORDER BY date_day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS dau_7d_avg,
        AVG(behavior_count) OVER (
            ORDER BY date_day
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS behavior_count_7d_avg
    FROM week2_daily_metrics m
    ORDER BY date_day
"""


RETENTION_SQL = """
    CREATE OR REPLACE TABLE week2_retention_daily AS
    WITH first_active AS (
        SELECT
            user_id,
            MIN(event_date) AS first_date
        FROM week2_user_activity_day
        GROUP BY user_id
    ), cohort_retention AS (
        SELECT
            f.first_date,
            COUNT(DISTINCT f.user_id) AS cohort_users,
            COUNT(DISTINCT CASE
                WHEN a.event_date = f.first_date + INTERVAL '1 day'
                THEN f.user_id
            END) AS retained_d1,
            COUNT(DISTINCT CASE
                WHEN a.event_date = f.first_date + INTERVAL '7 days'
                THEN f.user_id
            END) AS retained_d7,
            COUNT(DISTINCT CASE
                WHEN a.event_date = f.first_date + INTERVAL '30 days'
                THEN f.user_id
            END) AS retained_d30
        FROM first_active f
        LEFT JOIN week2_user_activity_day a
            ON f.user_id = a.user_id
        GROUP BY f.first_date
    )
    SELECT
        first_date,
        cohort_users,
        retained_d1,
        retained_d7,
        retained_d30,
        ROUND(retained_d1 * 1.0 / NULLIF(cohort_users, 0), 4)
            AS d1_retention,
        ROUND(retained_d7 * 1.0 / NULLIF(cohort_users, 0), 4)
            AS d7_retention,
        ROUND(retained_d30 * 1.0 / NULLIF(cohort_users, 0), 4)
            AS d30_retention
    FROM cohort_retention
    ORDER BY first_date
"""


CONCENTRATION_SQL = """
    CREATE OR REPLACE TABLE week2_content_concentration AS
    WITH monthly_content AS (
        SELECT
            CAST(DATE_TRUNC('month', event_date) AS DATE) AS month_start,
            content_id,
            SUM(behavior_count) AS behavior_count
        FROM week2_content_activity_day
        GROUP BY month_start, content_id
    ), ranked AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY month_start
                ORDER BY behavior_count DESC, content_id
            ) AS content_rank,
            SUM(behavior_count) OVER (
                PARTITION BY month_start
            ) AS monthly_behavior_count
        FROM monthly_content
    )
    SELECT
        month_start,
        MAX(monthly_behavior_count) AS monthly_behavior_count,
        SUM(
            CASE WHEN content_rank <= 10 THEN behavior_count ELSE 0 END
        ) AS top10_behavior_count,
        ROUND(
            SUM(
                CASE WHEN content_rank <= 10 THEN behavior_count ELSE 0 END
            ) * 1.0
            / NULLIF(MAX(monthly_behavior_count), 0),
            4
        ) AS top10_behavior_share
    FROM ranked
    GROUP BY month_start
    ORDER BY month_start
"""


def save_trend_chart(daily: pd.DataFrame) -> None:
    daily = daily.copy()
    daily["date_day"] = pd.to_datetime(daily["date_day"])
    plt.figure(figsize=(14, 5))
    plt.plot(daily["date_day"], daily["dau"], label="DAU", color="#2F6B9A")
    plt.plot(
        daily["date_day"],
        daily["dau_7d_avg"],
        label="7-day average",
        color="#F28E2B",
    )
    plt.title("DAU Trend and Seven-Day Average")
    plt.xlabel("Date")
    plt.ylabel("DAU")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day10_dau_trend.png", dpi=150)
    plt.close()


def save_retention_chart(retention: pd.DataFrame) -> None:
    retention = retention.copy()
    retention["first_date"] = pd.to_datetime(retention["first_date"])
    plt.figure(figsize=(14, 5))
    plt.plot(retention["first_date"], retention["d1_retention"], label="D1")
    plt.plot(retention["first_date"], retention["d7_retention"], label="D7")
    plt.plot(retention["first_date"], retention["d30_retention"], label="D30")
    plt.title("Daily Cohort Retention")
    plt.xlabel("First active date")
    plt.ylabel("Retention rate")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day10_retention_trend.png", dpi=150)
    plt.close()


def save_concentration_chart(concentration: pd.DataFrame) -> None:
    concentration = concentration.copy()
    concentration["month_start"] = pd.to_datetime(concentration["month_start"])
    plt.figure(figsize=(14, 5))
    plt.plot(
        concentration["month_start"],
        concentration["top10_behavior_share"],
        color="#59A14F",
    )
    plt.title("Top Ten Content Behavior Concentration")
    plt.xlabel("Month")
    plt.ylabel("Share of behavior volume")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day10_content_concentration.png", dpi=150)
    plt.close()


def main() -> None:
    sns.set_theme(style="whitegrid")
    connection = connect_week2()
    try:
        require_week2_tables(
            connection,
            "week2_daily_metrics",
            "week2_user_activity_day",
            "week2_content_activity_day",
        )
        connection.execute(DAILY_TRENDS_SQL)
        connection.execute(RETENTION_SQL)
        connection.execute(CONCENTRATION_SQL)

        daily = connection.sql(
            "SELECT * FROM week2_daily_trends ORDER BY date_day"
        ).df()
        retention = connection.sql(
            "SELECT * FROM week2_retention_daily ORDER BY first_date"
        ).df()
        concentration = connection.sql(
            "SELECT * FROM week2_content_concentration ORDER BY month_start"
        ).df()
        frequency = connection.sql("""
            SELECT
                user_id,
                behavior_count,
                content_count,
                CASE
                    WHEN behavior_count < 50 THEN '1-49'
                    WHEN behavior_count < 100 THEN '50-99'
                    WHEN behavior_count < 250 THEN '100-249'
                    WHEN behavior_count < 500 THEN '250-499'
                    ELSE '500+'
                END AS frequency_bucket
            FROM user_dim
            ORDER BY behavior_count DESC
        """).df()
        content = connection.sql("""
            SELECT
                c.content_id,
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

        save_trend_chart(daily)
        save_retention_chart(retention)
        save_concentration_chart(concentration)

        output = save_excel(
            {
                "daily_trends": daily,
                "retention": retention,
                "concentration": concentration,
                "user_frequency": frequency,
                "content_activity": content,
            },
            "ml_day10_trend_analysis.xlsx",
        )
        daily.to_csv(
            OUTPUT_DIR / "ml_day10_daily_trends.csv",
            index=False,
            encoding="utf-8-sig",
        )
        retention.to_csv(
            OUTPUT_DIR / "ml_day10_retention.csv",
            index=False,
            encoding="utf-8-sig",
        )

        max_dau = daily.loc[daily["dau"].idxmax()]
        max_concentration = concentration.loc[
            concentration["top10_behavior_share"].idxmax()
        ]
        report = f"""# Day 10: Trend Analysis

## Findings to investigate

- The highest observed DAU date is {max_dau['date_day']} with {int(max_dau['dau']):,} rating-active users.
- The highest monthly top-ten content concentration is {max_concentration['top10_behavior_share']:.2%} in {max_concentration['month_start']}.
- The workbook contains daily DAU, cohort retention, user frequency, content activity, and concentration results.

## Interpretation rules

1. A DAU movement should be compared with behavior count and active content before calling it a user problem.
2. Retention here means a later rating event, not a confirmed product return or watch event.
3. A high top-ten share means rating behavior is concentrated; it does not prove that long-tail content has no value.
4. Content rankings use a minimum rating-volume filter to reduce small-sample noise.

## Next analysis

Use Day 11 to compare user segments, content genres, and monthly cohorts. Use Day 12 to turn the trend signals into a repeatable anomaly monitor.
"""
        (OUTPUT_DIR / "ml_day10_trend_analysis.md").write_text(
            report,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
