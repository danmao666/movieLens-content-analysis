-- Day 10: DAU, retention, content concentration, and user frequency.

CREATE OR REPLACE TABLE week2_daily_trends AS
SELECT
    m.*,
    LAG(dau) OVER (ORDER BY date_day) AS previous_dau,
    LAG(behavior_count) OVER (ORDER BY date_day) AS previous_behavior_count,
    AVG(dau) OVER (
        ORDER BY date_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS dau_7d_avg,
    AVG(behavior_count) OVER (
        ORDER BY date_day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS behavior_count_7d_avg
FROM week2_daily_metrics m
ORDER BY date_day;

CREATE OR REPLACE TABLE week2_retention_daily AS
WITH first_active AS (
    SELECT user_id, MIN(event_date) AS first_date
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
    LEFT JOIN week2_user_activity_day a ON f.user_id = a.user_id
    GROUP BY f.first_date
)
SELECT
    *,
    ROUND(retained_d1 * 1.0 / NULLIF(cohort_users, 0), 4) AS d1_retention,
    ROUND(retained_d7 * 1.0 / NULLIF(cohort_users, 0), 4) AS d7_retention,
    ROUND(retained_d30 * 1.0 / NULLIF(cohort_users, 0), 4) AS d30_retention
FROM cohort_retention
ORDER BY first_date;

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
        SUM(behavior_count) OVER (PARTITION BY month_start)
            AS monthly_behavior_count
    FROM monthly_content
)
SELECT
    month_start,
    MAX(monthly_behavior_count) AS monthly_behavior_count,
    SUM(CASE WHEN content_rank <= 10 THEN behavior_count ELSE 0 END)
        AS top10_behavior_count,
    ROUND(
        SUM(CASE WHEN content_rank <= 10 THEN behavior_count ELSE 0 END) * 1.0
        / NULLIF(MAX(monthly_behavior_count), 0),
        4
    ) AS top10_behavior_share
FROM ranked
GROUP BY month_start
ORDER BY month_start;
