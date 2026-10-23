from datetime import date

import pandas as pd

from common import OUTPUT_DIR
from week4_common import connect_week4, require_week4_tables, save_excel


TESTS = [
    {
        "id": "SQL01",
        "topic": "Retention",
        "time_limit_minutes": 25,
        "question": "按首日活跃日期计算 D1、D7、D30 留存率，并排除尚未到达观察窗口的 cohort。",
    },
    {
        "id": "SQL02",
        "topic": "Funnel",
        "time_limit_minutes": 15,
        "question": "按行为次数计算用户 1+、5+、20+、50+ 行为漏斗，并计算每层相对总用户的比例。",
    },
    {
        "id": "SQL03",
        "topic": "Top N",
        "time_limit_minutes": 25,
        "question": "按一级类型取活跃用户数 Top 3 内容，同时返回内容排名、行为次数和平均评分。",
    },
    {
        "id": "SQL04",
        "topic": "Anomaly",
        "time_limit_minutes": 25,
        "question": "计算 DAU 环比、28 日历史均值、标准差和 z-score，并标记异常日期。",
    },
]


ANSWERS = {
    "SQL01": """
        WITH first_active AS (
            SELECT user_id, MIN(event_date) AS first_date
            FROM behavior_fact
            GROUP BY user_id
        ), cohort AS (
            SELECT
                f.first_date,
                COUNT(DISTINCT f.user_id) AS cohort_users,
                COUNT(DISTINCT CASE
                    WHEN a.event_date = f.first_date + INTERVAL '1 day'
                    THEN f.user_id END) AS retained_d1,
                COUNT(DISTINCT CASE
                    WHEN a.event_date = f.first_date + INTERVAL '7 days'
                    THEN f.user_id END) AS retained_d7,
                COUNT(DISTINCT CASE
                    WHEN a.event_date = f.first_date + INTERVAL '30 days'
                    THEN f.user_id END) AS retained_d30
            FROM first_active f
            LEFT JOIN behavior_fact a ON f.user_id = a.user_id
            GROUP BY f.first_date
        )
        SELECT
            *,
            ROUND(retained_d1 * 1.0 / NULLIF(cohort_users, 0), 4) AS d1_rate,
            ROUND(retained_d7 * 1.0 / NULLIF(cohort_users, 0), 4) AS d7_rate,
            ROUND(retained_d30 * 1.0 / NULLIF(cohort_users, 0), 4) AS d30_rate
        FROM cohort
        ORDER BY first_date;
    """,
    "SQL02": """
        WITH user_stats AS (
            SELECT user_id, COUNT(*) AS behavior_count
            FROM behavior_fact
            GROUP BY user_id
        ), funnel AS (
            SELECT
                COUNT(*) AS total_users,
                SUM(CASE WHEN behavior_count >= 1 THEN 1 ELSE 0 END) AS users_1_plus,
                SUM(CASE WHEN behavior_count >= 5 THEN 1 ELSE 0 END) AS users_5_plus,
                SUM(CASE WHEN behavior_count >= 20 THEN 1 ELSE 0 END) AS users_20_plus,
                SUM(CASE WHEN behavior_count >= 50 THEN 1 ELSE 0 END) AS users_50_plus
            FROM user_stats
        )
        SELECT
            *,
            ROUND(users_1_plus * 1.0 / total_users, 4) AS rate_1_plus,
            ROUND(users_5_plus * 1.0 / total_users, 4) AS rate_5_plus,
            ROUND(users_20_plus * 1.0 / total_users, 4) AS rate_20_plus,
            ROUND(users_50_plus * 1.0 / total_users, 4) AS rate_50_plus
        FROM funnel;
    """,
    "SQL03": """
        WITH content_stats AS (
            SELECT
                c.content_id,
                c.title,
                split_part(c.genres, '|', 1) AS primary_genre,
                COUNT(*) AS behavior_count,
                COUNT(DISTINCT b.user_id) AS active_users,
                ROUND(AVG(b.rating), 2) AS avg_rating
            FROM behavior_fact b
            JOIN content_dim c ON b.content_id = c.content_id
            GROUP BY c.content_id, c.title, c.genres
        ), ranked AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY primary_genre
                    ORDER BY active_users DESC, behavior_count DESC
                ) AS genre_rank
            FROM content_stats
        )
        SELECT *
        FROM ranked
        WHERE genre_rank <= 3
        ORDER BY primary_genre, genre_rank;
    """,
    "SQL04": """
        WITH history AS (
            SELECT
                *,
                LAG(dau) OVER (ORDER BY date_day) AS previous_dau,
                AVG(dau) OVER (
                    ORDER BY date_day
                    ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
                ) AS dau_28d_avg,
                STDDEV_SAMP(dau) OVER (
                    ORDER BY date_day
                    ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
                ) AS dau_28d_sd
            FROM week2_daily_metrics
        )
        SELECT
            date_day,
            dau,
            previous_dau,
            ROUND((dau - previous_dau) * 1.0 / NULLIF(previous_dau, 0), 4)
                AS dau_change_rate,
            dau_28d_avg,
            dau_28d_sd,
            CASE
                WHEN dau_28d_sd > 0
                THEN ROUND((dau - dau_28d_avg) / dau_28d_sd, 4)
            END AS dau_z_score,
            CASE
                WHEN dau_28d_sd > 0
                 AND ABS((dau - dau_28d_avg) / dau_28d_sd) >= 2
                THEN 1 ELSE 0
            END AS is_anomaly
        FROM history
        ORDER BY date_day;
    """,
}


def main() -> None:
    connection = connect_week4()
    try:
        require_week4_tables(
            connection,
            "behavior_fact",
            "content_dim",
            "week2_daily_metrics",
        )
        questions = pd.DataFrame(TESTS)
        results = {}
        for test in TESTS:
            results[test["id"]] = connection.sql(ANSWERS[test["id"]]).df()

        rubric = pd.DataFrame(
            [
                {
                    "criterion": "Correctness",
                    "points": 40,
                    "check": "Result includes correct grain, filters, and metric formula.",
                },
                {
                    "criterion": "SQL structure",
                    "points": 25,
                    "check": "Uses CTE/subquery/window function where appropriate.",
                },
                {
                    "criterion": "Edge cases",
                    "points": 20,
                    "check": "Handles NULLIF, unavailable cohort windows, and duplicate users.",
                },
                {
                    "criterion": "Business explanation",
                    "points": 15,
                    "check": "Explains what the result means and what action it supports.",
                },
            ]
        )
        output = save_excel(
            {
                "test_instructions": questions,
                "rubric": rubric,
                **{key: value.head(10000) for key, value in results.items()},
            },
            "ml_day22_sql_timed_test.xlsx",
        )
        questions.to_csv(
            OUTPUT_DIR / "ml_day22_sql_timed_test.csv",
            index=False,
            encoding="utf-8-sig",
        )
        sql_text = "-- Day 22 SQL timed test answer key\n\n"
        for test in TESTS:
            sql_text += f"-- {test['id']}: {test['question']}\n"
            sql_text += ANSWERS[test["id"]].strip() + "\n\n"
        (OUTPUT_DIR / "ml_day22_sql_timed_test_answer_key.sql").write_text(
            sql_text,
            encoding="utf-8",
        )
        report = f"""# Day 22: 90-Minute SQL Timed Test

## Practice setup

Complete the four questions in 90 minutes without looking at the answer key. The script runs the answer key only to verify that the project tables support the requested business questions. This output does not claim that a timed attempt has been completed.

- Retention: 25 minutes.
- Funnel: 15 minutes.
- Top N: 25 minutes.
- Anomaly indicators: 25 minutes.

## Required skills

CTE, subquery, `COUNT(DISTINCT)`, date arithmetic, `CASE WHEN`, `ROW_NUMBER`, `LAG`, rolling mean, standard deviation, `NULLIF`, and business interpretation.

## Self-scoring

Use the rubric in `ml_day22_sql_timed_test.xlsx`. Record the time spent, failed test cases, and one improvement in a separate practice log before moving to Day 23.

Generated on: {date.today().isoformat()}
"""
        (OUTPUT_DIR / "ml_day22_sql_timed_test.md").write_text(
            report,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
