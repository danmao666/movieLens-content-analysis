import importlib.metadata
import platform
import sys
from pathlib import Path

import pandas as pd

import duckdb

from common import DATA_DIR, OUTPUT_DIR, connect, csv_sql_path


def main() -> None:
    connection = connect()
    try:
        movies_path = csv_sql_path("movies.csv")
        ratings_path = csv_sql_path("ratings.csv")

        connection.execute(f"""
            CREATE OR REPLACE TABLE content_dim AS
            SELECT
                CAST(movieId AS INTEGER) AS content_id,
                title,
                genres
            FROM read_csv_auto('{movies_path}')
        """)

        connection.execute(f"""
            CREATE OR REPLACE TABLE behavior_fact AS
            SELECT
                CAST(userId AS INTEGER) AS user_id,
                CAST(movieId AS INTEGER) AS content_id,
                CAST(rating AS DOUBLE) AS rating,
                to_timestamp(CAST("timestamp" AS BIGINT)) AS event_ts,
                CAST(
                    to_timestamp(CAST("timestamp" AS BIGINT)) AS DATE
                ) AS event_date
            FROM read_csv_auto('{ratings_path}')
        """)

        connection.execute("""
            CREATE OR REPLACE TABLE user_dim AS
            SELECT
                user_id,
                MIN(event_date) AS first_active_date,
                MAX(event_date) AS last_active_date,
                COUNT(*) AS behavior_count,
                COUNT(DISTINCT content_id) AS content_count
            FROM behavior_fact
            GROUP BY user_id
        """)

        connection.execute("""
            CREATE OR REPLACE TABLE date_dim AS
            SELECT
                CAST(day_value AS DATE) AS date_day,
                date_part('year', day_value) AS year,
                date_part('month', day_value) AS month,
                date_part('week', day_value) AS week,
                date_part('dayofweek', day_value) AS weekday
            FROM generate_series(
                (SELECT MIN(event_date) FROM behavior_fact),
                (SELECT MAX(event_date) FROM behavior_fact),
                INTERVAL '1 day'
            ) AS t(day_value)
        """)

        table_counts = connection.sql("""
            SELECT 'content_dim' AS table_name, COUNT(*) AS row_count
            FROM content_dim
            UNION ALL
            SELECT 'behavior_fact', COUNT(*) FROM behavior_fact
            UNION ALL
            SELECT 'user_dim', COUNT(*) FROM user_dim
            UNION ALL
            SELECT 'date_dim', COUNT(*) FROM date_dim
            ORDER BY table_name
        """).df()

        table_counts.to_csv(
            OUTPUT_DIR / "ml_day01_table_counts.csv",
            index=False,
            encoding="utf-8-sig",
        )

        environment = pd.DataFrame(
            [
                {"item": "python", "value": sys.version.split()[0]},
                {"item": "python_executable", "value": sys.executable},
                {"item": "platform", "value": platform.platform()},
                {"item": "duckdb", "value": duckdb.__version__},
                {
                    "item": "pandas",
                    "value": importlib.metadata.version("pandas"),
                },
                {
                    "item": "jupyterlab",
                    "value": importlib.metadata.version("jupyterlab"),
                },
            ]
        )

        dataset_files = pd.DataFrame(
            [
                {
                    "file_name": path.name,
                    "size_mb": round(path.stat().st_size / 1024**2, 2),
                }
                for path in sorted(DATA_DIR.iterdir())
                if path.is_file()
            ]
        )

        sample_movies = connection.sql("""
            SELECT *
            FROM content_dim
            ORDER BY content_id
            LIMIT 10
        """).df()
        sample_behavior = connection.sql("""
            SELECT *
            FROM behavior_fact
            ORDER BY event_ts
            LIMIT 10
        """).df()
        if not sample_behavior.empty and "event_ts" in sample_behavior:
            sample_behavior["event_ts"] = pd.to_datetime(
                sample_behavior["event_ts"]
            ).dt.tz_localize(None)

        baseline_tasks = pd.DataFrame(
            [
                {
                    "area": "SQL",
                    "task": "Write a daily COUNT(DISTINCT user_id) query",
                    "reference": "code/day02_sql_basics.py",
                    "status": "completed by this project",
                },
                {
                    "area": "Python",
                    "task": "Read a CSV sample and inspect columns",
                    "reference": "code/day01_setup.py",
                    "status": "completed by this project",
                },
                {
                    "area": "Excel",
                    "task": "Create a pivot-style summary and chart",
                    "reference": "code/day05_excel_dashboard.py",
                    "status": "completed by this project",
                },
            ]
        )

        with pd.ExcelWriter(
            OUTPUT_DIR / "ml_day01_environment_and_data_profile.xlsx",
            engine="openpyxl",
        ) as writer:
            environment.to_excel(writer, sheet_name="environment", index=False)
            dataset_files.to_excel(writer, sheet_name="dataset_files", index=False)
            table_counts.to_excel(writer, sheet_name="table_counts", index=False)
            sample_movies.to_excel(writer, sheet_name="sample_movies", index=False)
            sample_behavior.to_excel(
                writer,
                sheet_name="sample_behavior",
                index=False,
            )
            baseline_tasks.to_excel(
                writer,
                sheet_name="baseline_tasks",
                index=False,
            )

        print(table_counts.to_string(index=False))
        print(f"Database: {Path(connection.execute('SELECT current_database()').fetchone()[0])}")
        print(
            "Day 1 baseline saved: "
            f"{OUTPUT_DIR / 'ml_day01_environment_and_data_profile.xlsx'}"
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
