import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import OUTPUT_DIR
from week2_common import connect_week2, require_week2_tables, save_excel


USER_SEGMENTS_SQL = """
    CREATE OR REPLACE TABLE week2_user_segments AS
    WITH ranked AS (
        SELECT
            user_id,
            first_active_date,
            last_active_date,
            behavior_count,
            content_count,
            NTILE(4) OVER (
                ORDER BY behavior_count, user_id
            ) AS activity_quartile
        FROM user_dim
    )
    SELECT
        *,
        CASE activity_quartile
            WHEN 1 THEN 'low'
            WHEN 2 THEN 'medium_low'
            WHEN 3 THEN 'medium_high'
            ELSE 'high'
        END AS user_segment
    FROM ranked
"""


CONTENT_CATEGORY_SQL = """
    CREATE OR REPLACE TABLE week2_content_category AS
    SELECT
        content_id,
        title,
        genres,
        CASE
            WHEN genres IS NULL OR genres = '' THEN 'unknown'
            ELSE split_part(genres, '|', 1)
        END AS primary_genre
    FROM content_dim
"""


GENRE_PERFORMANCE_SQL = """
    CREATE OR REPLACE TABLE week2_genre_performance AS
    SELECT
        g.genre,
        COUNT(*) AS behavior_count,
        COUNT(DISTINCT b.user_id) AS active_users,
        COUNT(DISTINCT b.content_id) AS active_content_count,
        ROUND(AVG(b.rating), 4) AS avg_rating
    FROM behavior_fact b
    JOIN content_dim c ON b.content_id = c.content_id
    CROSS JOIN UNNEST(string_split(c.genres, '|')) AS g(genre)
    GROUP BY g.genre
    ORDER BY active_users DESC
"""


COHORT_SQL = """
    CREATE OR REPLACE TABLE week2_user_cohort AS
    SELECT
        user_id,
        first_active_date,
        CAST(DATE_TRUNC('month', first_active_date) AS DATE) AS cohort_month
    FROM user_dim
"""


ACTIVITY_MONTH_SQL = """
    CREATE OR REPLACE TABLE week2_user_activity_month AS
    SELECT
        user_id,
        CAST(DATE_TRUNC('month', event_date) AS DATE) AS activity_month
    FROM behavior_fact
    GROUP BY user_id, activity_month
"""


COHORT_RETENTION_SQL = """
    CREATE OR REPLACE TABLE week2_cohort_retention AS
    WITH activity AS (
        SELECT
            c.cohort_month,
            a.user_id,
            a.activity_month,
            DATE_DIFF(
                'month',
                c.cohort_month,
                a.activity_month
            ) AS period_number
        FROM week2_user_cohort c
        JOIN week2_user_activity_month a
            ON c.user_id = a.user_id
        WHERE a.activity_month >= c.cohort_month
    ), cohort_sizes AS (
        SELECT
            cohort_month,
            COUNT(DISTINCT user_id) AS cohort_users
        FROM week2_user_cohort
        GROUP BY cohort_month
    ), retained AS (
        SELECT
            cohort_month,
            period_number,
            COUNT(DISTINCT user_id) AS retained_users
        FROM activity
        WHERE period_number BETWEEN 0 AND 12
        GROUP BY cohort_month, period_number
    )
    SELECT
        r.cohort_month,
        r.period_number,
        s.cohort_users,
        r.retained_users,
        ROUND(r.retained_users * 1.0 / NULLIF(s.cohort_users, 0), 4)
            AS retention_rate
    FROM retained r
    JOIN cohort_sizes s USING (cohort_month)
    ORDER BY cohort_month, period_number
"""


def save_segment_chart(summary: pd.DataFrame) -> None:
    order = ["low", "medium_low", "medium_high", "high"]
    summary = summary.set_index("user_segment").reindex(order).reset_index()
    plt.figure(figsize=(9, 5))
    sns.barplot(data=summary, x="user_segment", y="user_count", color="#4E79A7")
    plt.title("User Segments by Activity Quartile")
    plt.xlabel("User segment")
    plt.ylabel("Users")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day11_user_segments.png", dpi=150)
    plt.close()


def save_genre_chart(genre: pd.DataFrame) -> None:
    plot_data = genre.head(15).sort_values("active_users")
    plt.figure(figsize=(10, 7))
    sns.barplot(
        data=plot_data,
        x="active_users",
        y="genre",
        color="#59A14F",
    )
    plt.title("Genre Performance by Active Users")
    plt.xlabel("Active users")
    plt.ylabel("Genre")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day11_genre_performance.png", dpi=150)
    plt.close()


def save_cohort_heatmap(cohort: pd.DataFrame) -> None:
    matrix = cohort.pivot(
        index="cohort_month",
        columns="period_number",
        values="retention_rate",
    )
    plt.figure(figsize=(14, 8))
    sns.heatmap(matrix, cmap="Blues", vmin=0, vmax=1)
    plt.title("Monthly Cohort Retention")
    plt.xlabel("Months since first activity")
    plt.ylabel("Cohort month")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day11_cohort_retention.png", dpi=150)
    plt.close()


def main() -> None:
    sns.set_theme(style="whitegrid")
    connection = connect_week2()
    try:
        require_week2_tables(connection, "behavior_fact", "content_dim", "user_dim")
        connection.execute(USER_SEGMENTS_SQL)
        connection.execute(CONTENT_CATEGORY_SQL)
        connection.execute(GENRE_PERFORMANCE_SQL)
        connection.execute(COHORT_SQL)
        connection.execute(ACTIVITY_MONTH_SQL)
        connection.execute(COHORT_RETENTION_SQL)

        segments = connection.sql("""
            SELECT
                user_segment,
                COUNT(*) AS user_count,
                ROUND(AVG(behavior_count), 2) AS avg_behavior_count,
                ROUND(AVG(content_count), 2) AS avg_content_count,
                ROUND(AVG(
                    DATE_DIFF('day', first_active_date, last_active_date)
                ), 2) AS avg_active_span_days
            FROM week2_user_segments
            GROUP BY user_segment
            ORDER BY MIN(activity_quartile)
        """).df()
        genre = connection.sql("""
            SELECT *
            FROM week2_genre_performance
            WHERE behavior_count >= 1000
            ORDER BY active_users DESC
        """).df()
        cohort = connection.sql("""
            SELECT *
            FROM week2_cohort_retention
            ORDER BY cohort_month, period_number
        """).df()
        content_category = connection.sql("""
            SELECT *
            FROM week2_content_category
            ORDER BY content_id
        """).df()

        segment_summary = segments.copy()
        save_segment_chart(segment_summary)
        save_genre_chart(genre)
        save_cohort_heatmap(cohort)

        output = save_excel(
            {
                "user_segments": segments,
                "genre_performance": genre,
                "cohort_retention": cohort,
                "content_category_sample": content_category.head(10000),
            },
            "ml_day11_segmentation_and_cohort.xlsx",
        )
        segments.to_csv(
            OUTPUT_DIR / "ml_day11_user_segments.csv",
            index=False,
            encoding="utf-8-sig",
        )
        genre.to_csv(
            OUTPUT_DIR / "ml_day11_genre_performance.csv",
            index=False,
            encoding="utf-8-sig",
        )
        cohort.to_csv(
            OUTPUT_DIR / "ml_day11_cohort_retention.csv",
            index=False,
            encoding="utf-8-sig",
        )

        high_segment = segments.loc[
            segments["user_segment"] == "high"
        ].iloc[0]
        top_genre = genre.iloc[0]
        report = f"""# Day 11: User and Content Segmentation

## User segmentation

Users are divided into four activity quartiles using `NTILE(4)` on observed rating count. The high segment contains {int(high_segment['user_count']):,} users and averages {high_segment['avg_behavior_count']:.2f} observed behaviors.

## Content categorization

Movies are categorized by the first genre listed in the MovieLens `genres` field. Genre results should be read with both active users and rating volume; the leading qualifying genre by active users is {top_genre['genre']}.

## Cohort retention

Monthly cohorts are based on each user's first observed rating month. Retention period 0 is the cohort month; later periods count users with at least one rating in the corresponding calendar month.

## Business use

- Use activity segments to tailor re-engagement and recommendation messages.
- Use high-active-user genres as candidate content groups, not as proof of causal preference.
- Compare cohort retention before and after a recommendation change in a future experiment.

## Limitation

The data has no registration date or exposure log. Cohorts and segments describe observed rating activity only.
"""
        (OUTPUT_DIR / "ml_day11_segmentation_and_cohort.md").write_text(
            report,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
