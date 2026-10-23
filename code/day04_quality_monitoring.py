import pandas as pd

from common import OUTPUT_DIR, connect, require_tables


DAILY_METRICS_SQL = """
    CREATE OR REPLACE TABLE daily_metrics AS
    WITH daily AS (
        SELECT
            d.date_day,
            COUNT(DISTINCT b.user_id) AS dau,
            COUNT(b.user_id) AS behavior_count,
            COUNT(DISTINCT b.content_id) AS active_content_count,
            COUNT(DISTINCT CASE
                WHEN u.first_active_date = d.date_day THEN b.user_id
            END) AS new_users,
            ROUND(AVG(b.rating), 2) AS avg_rating
        FROM date_dim d
        LEFT JOIN behavior_fact b
            ON d.date_day = b.event_date
        LEFT JOIN user_dim u
            ON b.user_id = u.user_id
        GROUP BY d.date_day
    ), with_baseline AS (
        SELECT
            *,
            AVG(dau) OVER (
                ORDER BY date_day
                ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
            ) AS dau_7d_avg,
            STDDEV_SAMP(dau) OVER (
                ORDER BY date_day
                ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
            ) AS dau_7d_sd
        FROM daily
    )
    SELECT
        *,
        CASE
            WHEN dau_7d_sd IS NOT NULL
             AND ABS(dau - dau_7d_avg) > 2 * dau_7d_sd
            THEN 1
            ELSE 0
        END AS is_dau_anomaly
    FROM with_baseline
    ORDER BY date_day
"""


QUALITY_QUERIES = {
    "invalid_rows": """
        SELECT COUNT(*) AS invalid_rows
        FROM behavior_fact
        WHERE user_id IS NULL
           OR content_id IS NULL
           OR event_date IS NULL
           OR rating NOT BETWEEN 0.5 AND 5
    """,
    "orphan_content": """
        SELECT COUNT(*) AS orphan_rows
        FROM behavior_fact b
        LEFT JOIN content_dim c
            ON b.content_id = c.content_id
        WHERE c.content_id IS NULL
    """,
    "duplicate_events": """
        SELECT
            user_id,
            content_id,
            event_ts,
            COUNT(*) AS duplicate_count
        FROM behavior_fact
        GROUP BY user_id, content_id, event_ts
        HAVING COUNT(*) > 1
        ORDER BY duplicate_count DESC
        LIMIT 100
    """,
    "date_coverage": """
        SELECT
            MIN(event_date) AS first_event_date,
            MAX(event_date) AS last_event_date,
            COUNT(DISTINCT event_date) AS active_dates,
            COUNT(*) AS behavior_count
        FROM behavior_fact
    """,
    "anomaly_dates": """
        SELECT *
        FROM daily_metrics
        WHERE is_dau_anomaly = 1
        ORDER BY date_day
    """,
    "activity_funnel": """
        WITH user_stats AS (
            SELECT
                user_id,
                COUNT(*) AS behavior_count
            FROM behavior_fact
            GROUP BY user_id
        )
        SELECT
            SUM(CASE WHEN behavior_count >= 1 THEN 1 ELSE 0 END)
                AS users_with_1_plus_behavior,
            SUM(CASE WHEN behavior_count >= 5 THEN 1 ELSE 0 END)
                AS users_with_5_plus_behavior,
            SUM(CASE WHEN behavior_count >= 20 THEN 1 ELSE 0 END)
                AS users_with_20_plus_behavior,
            SUM(CASE WHEN behavior_count >= 50 THEN 1 ELSE 0 END)
                AS users_with_50_plus_behavior
        FROM user_stats
    """,
    "daily_rolling_metrics": """
        SELECT
            date_day,
            dau,
            behavior_count,
            active_content_count,
            dau_7d_avg,
            dau_7d_sd,
            is_dau_anomaly
        FROM daily_metrics
        ORDER BY date_day
    """,
}


def main() -> None:
    connection = connect()
    try:
        require_tables(
            connection,
            "content_dim",
            "behavior_fact",
            "user_dim",
            "date_dim",
        )
        connection.execute(DAILY_METRICS_SQL)

        output_path = OUTPUT_DIR / "ml_day04_quality_and_anomaly.xlsx"
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            daily_metrics = connection.sql(
                "SELECT * FROM daily_metrics ORDER BY date_day"
            ).df()
            daily_metrics.to_excel(writer, sheet_name="daily_metrics", index=False)

            for sheet_name, query in QUALITY_QUERIES.items():
                result = connection.sql(query).df()
                result.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                print(f"{sheet_name}: {len(result)} row(s)")

        daily_metrics.to_csv(
            OUTPUT_DIR / "ml_day04_daily_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        print(f"Saved: {output_path}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
