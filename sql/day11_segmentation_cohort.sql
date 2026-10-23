-- Day 11: user segmentation, content categories, and cohort retention.

CREATE OR REPLACE TABLE week2_user_segments AS
WITH ranked AS (
    SELECT
        user_id,
        first_active_date,
        last_active_date,
        behavior_count,
        content_count,
        NTILE(4) OVER (ORDER BY behavior_count, user_id) AS activity_quartile
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
FROM ranked;

CREATE OR REPLACE TABLE week2_content_category AS
SELECT
    content_id,
    title,
    genres,
    CASE
        WHEN genres IS NULL OR genres = '' THEN 'unknown'
        ELSE split_part(genres, '|', 1)
    END AS primary_genre
FROM content_dim;

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
ORDER BY active_users DESC;

CREATE OR REPLACE TABLE week2_user_cohort AS
SELECT
    user_id,
    first_active_date,
    CAST(DATE_TRUNC('month', first_active_date) AS DATE) AS cohort_month
FROM user_dim;

CREATE OR REPLACE TABLE week2_user_activity_month AS
SELECT
    user_id,
    CAST(DATE_TRUNC('month', event_date) AS DATE) AS activity_month
FROM behavior_fact
GROUP BY user_id, activity_month;

CREATE OR REPLACE TABLE week2_cohort_retention AS
WITH activity AS (
    SELECT
        c.cohort_month,
        a.user_id,
        a.activity_month,
        DATE_DIFF('month', c.cohort_month, a.activity_month) AS period_number
    FROM week2_user_cohort c
    JOIN week2_user_activity_month a ON c.user_id = a.user_id
    WHERE a.activity_month >= c.cohort_month
), cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT user_id) AS cohort_users
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
ORDER BY cohort_month, period_number;
