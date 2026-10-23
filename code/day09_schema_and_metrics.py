import pandas as pd

from common import OUTPUT_DIR
from week2_common import connect_week2, require_week2_tables, save_excel


METRIC_DEFINITIONS = [
    {
        "metric": "DAU",
        "sql_logic": "COUNT(DISTINCT user_id) by event_date",
        "business_meaning": "Daily rating-active users",
    },
    {
        "metric": "New users",
        "sql_logic": "first_active_date = date_day",
        "business_meaning": "First observed rating activity on the date",
    },
    {
        "metric": "Behavior count",
        "sql_logic": "COUNT(*) by event_date",
        "business_meaning": "Daily rating volume",
    },
    {
        "metric": "Active content",
        "sql_logic": "COUNT(DISTINCT content_id) by event_date",
        "business_meaning": "Content receiving at least one rating",
    },
    {
        "metric": "Ratings per active user",
        "sql_logic": "behavior_count / NULLIF(dau, 0)",
        "business_meaning": "Average observed rating frequency per active user",
    },
]


DAILY_METRICS_SQL = """
    CREATE OR REPLACE TABLE week2_daily_metrics AS
    SELECT
        d.date_day,
        CAST(DATE_TRUNC('week', d.date_day) AS DATE) AS week_start,
        CAST(DATE_TRUNC('month', d.date_day) AS DATE) AS month_start,
        d.weekday,
        COUNT(DISTINCT b.user_id) AS dau,
        COUNT(b.user_id) AS behavior_count,
        COUNT(DISTINCT b.content_id) AS active_content_count,
        COUNT(DISTINCT CASE
            WHEN u.first_active_date = d.date_day THEN b.user_id
        END) AS new_users,
        ROUND(AVG(b.rating), 4) AS avg_rating,
        ROUND(
            COUNT(b.user_id) * 1.0
            / NULLIF(COUNT(DISTINCT b.user_id), 0),
            4
        ) AS ratings_per_active_user
    FROM date_dim d
    LEFT JOIN behavior_fact b
        ON d.date_day = b.event_date
    LEFT JOIN user_dim u
        ON b.user_id = u.user_id
    GROUP BY d.date_day, d.weekday
    ORDER BY d.date_day
"""


def main() -> None:
    connection = connect_week2()
    try:
        require_week2_tables(
            connection,
            "content_dim",
            "behavior_fact",
            "user_dim",
            "date_dim",
        )

        connection.execute("""
            CREATE OR REPLACE TABLE week2_user_activity_day AS
            SELECT
                user_id,
                event_date,
                COUNT(*) AS behavior_count,
                COUNT(DISTINCT content_id) AS active_content_count
            FROM behavior_fact
            GROUP BY user_id, event_date
        """)

        connection.execute("""
            CREATE OR REPLACE TABLE week2_content_activity_day AS
            SELECT
                content_id,
                event_date,
                COUNT(*) AS behavior_count,
                COUNT(DISTINCT user_id) AS active_users,
                ROUND(AVG(rating), 4) AS avg_rating
            FROM behavior_fact
            GROUP BY content_id, event_date
        """)
        connection.execute(DAILY_METRICS_SQL)

        table_profile = connection.sql("""
            SELECT 'content_dim' AS table_name, COUNT(*) AS row_count
            FROM content_dim
            UNION ALL
            SELECT 'behavior_fact', COUNT(*) FROM behavior_fact
            UNION ALL
            SELECT 'user_dim', COUNT(*) FROM user_dim
            UNION ALL
            SELECT 'date_dim', COUNT(*) FROM date_dim
            UNION ALL
            SELECT 'week2_user_activity_day', COUNT(*)
            FROM week2_user_activity_day
            UNION ALL
            SELECT 'week2_content_activity_day', COUNT(*)
            FROM week2_content_activity_day
            UNION ALL
            SELECT 'week2_daily_metrics', COUNT(*)
            FROM week2_daily_metrics
            ORDER BY table_name
        """).df()

        daily_metrics = connection.sql(
            "SELECT * FROM week2_daily_metrics ORDER BY date_day"
        ).df()
        daily_metrics.to_csv(
            OUTPUT_DIR / "ml_day09_daily_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        pd.DataFrame(METRIC_DEFINITIONS).to_csv(
            OUTPUT_DIR / "ml_day09_metric_definitions.csv",
            index=False,
            encoding="utf-8-sig",
        )
        output = save_excel(
            {
                "table_profile": table_profile,
                "metric_definitions": pd.DataFrame(METRIC_DEFINITIONS),
                "daily_metrics_sample": daily_metrics.head(1000),
            },
            "ml_day09_schema_and_metrics.xlsx",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
