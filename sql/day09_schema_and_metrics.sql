-- Day 9: data model and daily metric SQL.
-- Run code/day09_schema_and_metrics.py for the project-relative execution.

CREATE OR REPLACE TABLE week2_user_activity_day AS
SELECT
    user_id,
    event_date,
    COUNT(*) AS behavior_count,
    COUNT(DISTINCT content_id) AS active_content_count
FROM behavior_fact
GROUP BY user_id, event_date;

CREATE OR REPLACE TABLE week2_content_activity_day AS
SELECT
    content_id,
    event_date,
    COUNT(*) AS behavior_count,
    COUNT(DISTINCT user_id) AS active_users,
    ROUND(AVG(rating), 4) AS avg_rating
FROM behavior_fact
GROUP BY content_id, event_date;

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
LEFT JOIN behavior_fact b ON d.date_day = b.event_date
LEFT JOIN user_dim u ON b.user_id = u.user_id
GROUP BY d.date_day, d.weekday
ORDER BY d.date_day;

SELECT *
FROM week2_daily_metrics
ORDER BY date_day;
