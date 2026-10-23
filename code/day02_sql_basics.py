import pandas as pd

from common import OUTPUT_DIR, connect, require_tables


QUERIES = {
    "overview": """
        SELECT
            COUNT(*) AS behavior_count,
            COUNT(DISTINCT user_id) AS user_count,
            COUNT(DISTINCT content_id) AS content_count,
            MIN(event_date) AS first_date,
            MAX(event_date) AS last_date
        FROM behavior_fact
    """,
    "rating_distribution": """
        SELECT
            rating,
            COUNT(*) AS rating_count
        FROM behavior_fact
        GROUP BY rating
        ORDER BY rating
    """,
    "daily_dau": """
        SELECT
            event_date,
            COUNT(DISTINCT user_id) AS dau,
            COUNT(*) AS behavior_count
        FROM behavior_fact
        GROUP BY event_date
        ORDER BY event_date
    """,
    "top_content": """
        SELECT
            c.content_id,
            c.title,
            c.genres,
            COUNT(*) AS behavior_count,
            COUNT(DISTINCT b.user_id) AS active_users,
            ROUND(AVG(b.rating), 2) AS avg_rating
        FROM behavior_fact b
        JOIN content_dim c
            ON b.content_id = c.content_id
        GROUP BY c.content_id, c.title, c.genres
        HAVING COUNT(*) >= 100
        ORDER BY active_users DESC
        LIMIT 50
    """,
    "top_users": """
        SELECT
            user_id,
            COUNT(*) AS behavior_count,
            COUNT(DISTINCT content_id) AS content_count,
            ROUND(AVG(rating), 2) AS avg_rating
        FROM behavior_fact
        GROUP BY user_id
        ORDER BY behavior_count DESC
        LIMIT 50
    """,
    "rating_levels": """
        SELECT
            CASE
                WHEN rating >= 4 THEN 'high'
                WHEN rating >= 3 THEN 'middle'
                ELSE 'low'
            END AS rating_level,
            COUNT(*) AS behavior_count,
            ROUND(AVG(rating), 2) AS avg_rating
        FROM behavior_fact
        GROUP BY rating_level
        ORDER BY rating_level
    """,
    "genre_performance": """
        SELECT
            g.genre,
            COUNT(*) AS behavior_count,
            COUNT(DISTINCT b.user_id) AS active_users,
            COUNT(DISTINCT b.content_id) AS active_content_count,
            ROUND(AVG(b.rating), 2) AS avg_rating
        FROM behavior_fact b
        JOIN content_dim c
            ON b.content_id = c.content_id
        CROSS JOIN UNNEST(string_split(c.genres, '|')) AS g(genre)
        GROUP BY g.genre
        HAVING COUNT(*) >= 1000
        ORDER BY active_users DESC
    """,
    "user_segments": """
        WITH user_stats AS (
            SELECT
                user_id,
                COUNT(*) AS behavior_count
            FROM behavior_fact
            GROUP BY user_id
        )
        SELECT
            CASE
                WHEN behavior_count >= 50 THEN 'high'
                WHEN behavior_count >= 20 THEN 'middle'
                ELSE 'low'
            END AS user_segment,
            COUNT(*) AS user_count,
            ROUND(AVG(behavior_count), 2) AS avg_behavior_count
        FROM user_stats
        GROUP BY user_segment
        ORDER BY user_segment
    """,
    "high_rating_content": """
        SELECT
            c.title,
            COUNT(*) AS behavior_count,
            ROUND(AVG(b.rating), 2) AS avg_rating
        FROM behavior_fact b
        JOIN content_dim c
            ON b.content_id = c.content_id
        GROUP BY c.content_id, c.title
        HAVING COUNT(*) >= 100
           AND AVG(b.rating) >= 4
        ORDER BY avg_rating DESC, behavior_count DESC
        LIMIT 50
    """,
    "monthly_activity": """
        SELECT
            DATE_TRUNC('month', event_date) AS month_start,
            COUNT(DISTINCT user_id) AS mau,
            COUNT(*) AS behavior_count
        FROM behavior_fact
        GROUP BY month_start
        ORDER BY month_start
    """,
}


def main() -> None:
    connection = connect()
    try:
        require_tables(connection, "content_dim", "behavior_fact")
        output_path = OUTPUT_DIR / "ml_day02_sql_basics.xlsx"
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_name, query in QUERIES.items():
                result = connection.sql(query).df()
                result.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                print(f"{sheet_name}: {len(result)} row(s)")
        print(f"Saved: {output_path}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
