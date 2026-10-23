import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import OUTPUT_DIR, connect, require_tables


def save_daily_plot(daily: pd.DataFrame) -> None:
    daily = daily.copy()
    daily["date_day"] = pd.to_datetime(daily["date_day"])
    daily["dau_7d_avg"] = daily["dau"].rolling(7, min_periods=1).mean()

    plt.figure(figsize=(14, 5))
    plt.plot(daily["date_day"], daily["dau"], label="DAU", color="#2F6B9A")
    plt.plot(
        daily["date_day"],
        daily["dau_7d_avg"],
        label="7-day average",
        color="#F28E2B",
        linewidth=2,
    )
    anomaly_days = daily[daily["is_dau_anomaly"] == 1]
    if not anomaly_days.empty:
        plt.scatter(
            anomaly_days["date_day"],
            anomaly_days["dau"],
            color="#C00000",
            label="Anomaly",
            zorder=3,
        )
    plt.title("Daily Active Users")
    plt.xlabel("Date")
    plt.ylabel("DAU")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day06_dau_trend.png", dpi=150)
    plt.close()


def save_content_plot(content: pd.DataFrame) -> None:
    plot_data = content.head(20).sort_values("active_users")
    plt.figure(figsize=(10, 8))
    sns.barplot(
        data=plot_data,
        x="active_users",
        y="title",
        color="#2F6B9A",
    )
    plt.title("Top Content by Active Users")
    plt.xlabel("Active users")
    plt.ylabel("Content")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day06_content_ranking.png", dpi=150)
    plt.close()


def save_user_plot(users: pd.DataFrame) -> None:
    users = users.copy()
    users["log_behavior_count"] = np.log1p(users["behavior_count"])
    plt.figure(figsize=(10, 5))
    sns.histplot(data=users, x="log_behavior_count", bins=40, color="#59A14F")
    plt.title("Distribution of User Activity")
    plt.xlabel("log(1 + behavior count)")
    plt.ylabel("Users")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day06_user_activity.png", dpi=150)
    plt.close()


def save_rating_plot(ratings: pd.DataFrame) -> None:
    plt.figure(figsize=(9, 5))
    sns.barplot(data=ratings, x="rating", y="rating_count", color="#E15759")
    plt.title("Rating Distribution")
    plt.xlabel("Rating")
    plt.ylabel("Records")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day06_rating_distribution.png", dpi=150)
    plt.close()


def get_quality_report(connection, users: pd.DataFrame) -> pd.DataFrame:
    quality = connection.sql("""
        SELECT
            SUM(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END)
                AS null_user_id,
            SUM(CASE WHEN content_id IS NULL THEN 1 ELSE 0 END)
                AS null_content_id,
            SUM(CASE WHEN event_date IS NULL THEN 1 ELSE 0 END)
                AS null_event_date,
            SUM(CASE WHEN rating NOT BETWEEN 0.5 AND 5 THEN 1 ELSE 0 END)
                AS invalid_rating,
            SUM(CASE WHEN rating < 0.5 OR rating > 5 THEN 1 ELSE 0 END)
                AS rating_outlier,
            (
                SELECT COUNT(*)
                FROM content_dim
                WHERE title IS NULL OR genres IS NULL
            ) AS incomplete_content_rows,
            (
                SELECT COUNT(*)
                FROM (
                    SELECT user_id, content_id, event_ts
                    FROM behavior_fact
                    GROUP BY user_id, content_id, event_ts
                    HAVING COUNT(*) > 1
                ) duplicate_groups
            ) AS duplicate_event_groups
        FROM behavior_fact
    """).df()

    q1 = users["behavior_count"].quantile(0.25)
    q3 = users["behavior_count"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr
    user_activity_outliers = int(
        np.sum(users["behavior_count"].to_numpy() > upper_bound)
    )

    quality["user_activity_iqr_outliers"] = user_activity_outliers
    quality["user_activity_iqr_upper_bound"] = upper_bound
    return quality


def get_python_cleaning_report(
    connection,
    users: pd.DataFrame,
) -> pd.DataFrame:
    """Run pandas/numpy checks on a bounded sample and full-table SQL checks."""
    sample = connection.sql("""
        SELECT user_id, content_id, rating, event_ts, event_date
        FROM behavior_fact
        ORDER BY event_ts
        LIMIT 100000
    """).df()

    null_cells = int(sample.isna().sum().sum())
    duplicate_rows = int(sample.duplicated().sum())
    rating_q1 = sample["rating"].quantile(0.25)
    rating_q3 = sample["rating"].quantile(0.75)
    rating_iqr = rating_q3 - rating_q1
    rating_lower = rating_q1 - 1.5 * rating_iqr
    rating_upper = rating_q3 + 1.5 * rating_iqr
    rating_outliers = int(
        ((sample["rating"] < rating_lower) | (sample["rating"] > rating_upper)).sum()
    )

    user_q1 = users["behavior_count"].quantile(0.25)
    user_q3 = users["behavior_count"].quantile(0.75)
    user_iqr = user_q3 - user_q1
    user_upper = user_q3 + 1.5 * user_iqr

    return pd.DataFrame(
        [
            {
                "check": "pandas sample rows",
                "value": len(sample),
                "method": "sample DataFrame row count",
            },
            {
                "check": "pandas sample null cells",
                "value": null_cells,
                "method": "sample.isna().sum().sum()",
            },
            {
                "check": "pandas sample duplicate rows",
                "value": duplicate_rows,
                "method": "sample.duplicated().sum()",
            },
            {
                "check": "rating IQR outliers in sample",
                "value": rating_outliers,
                "method": "NumPy/pandas IQR rule",
            },
            {
                "check": "rating IQR lower bound",
                "value": rating_lower,
                "method": "Q1 - 1.5 * IQR",
            },
            {
                "check": "rating IQR upper bound",
                "value": rating_upper,
                "method": "Q3 + 1.5 * IQR",
            },
            {
                "check": "user activity IQR upper bound",
                "value": user_upper,
                "method": "Q3 + 1.5 * IQR",
            },
        ]
    )


def main() -> None:
    sns.set_theme(style="whitegrid")
    connection = connect()
    try:
        require_tables(
            connection,
            "behavior_fact",
            "content_dim",
            "user_dim",
            "daily_metrics",
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

        users = connection.sql("""
            SELECT user_id, behavior_count, content_count, avg_rating
            FROM user_dim
            JOIN (
                SELECT user_id, ROUND(AVG(rating), 2) AS avg_rating
                FROM behavior_fact
                GROUP BY user_id
            ) USING (user_id)
        """).df()

        ratings = connection.sql("""
            SELECT rating, COUNT(*) AS rating_count
            FROM behavior_fact
            GROUP BY rating
            ORDER BY rating
        """).df()

        save_daily_plot(daily)
        save_content_plot(content)
        save_user_plot(users)
        save_rating_plot(ratings)
        quality = get_quality_report(connection, users)
        python_cleaning = get_python_cleaning_report(connection, users)

        daily["date_day"] = pd.to_datetime(daily["date_day"])
        summary = pd.DataFrame(
            {
                "metric": [
                    "max_dau",
                    "min_dau",
                    "mean_dau",
                    "max_behavior_count",
                    "content_rows_after_threshold",
                    "user_count",
                ],
                "value": [
                    daily["dau"].max(),
                    daily["dau"].min(),
                    round(daily["dau"].mean(), 2),
                    daily["behavior_count"].max(),
                    len(content),
                    len(users),
                ],
            }
        )
        with pd.ExcelWriter(
            OUTPUT_DIR / "ml_day06_eda_results.xlsx",
            engine="openpyxl",
        ) as writer:
            daily.to_excel(writer, sheet_name="daily_metrics", index=False)
            content.to_excel(writer, sheet_name="content_metrics", index=False)
            users.to_excel(writer, sheet_name="user_metrics", index=False)
            ratings.to_excel(writer, sheet_name="rating_distribution", index=False)
            summary.to_excel(writer, sheet_name="summary", index=False)
            quality.to_excel(writer, sheet_name="quality_checks", index=False)
            python_cleaning.to_excel(
                writer,
                sheet_name="python_cleaning",
                index=False,
            )

        daily.to_csv(
            OUTPUT_DIR / "ml_day06_daily_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        print("Saved day 6 charts and EDA workbook.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
