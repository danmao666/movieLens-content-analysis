-- Run code/day03_sql_advanced.py to execute the queries and export Excel results.

-- 1. User statistics
SELECT
    user_id,
    COUNT(*) AS behavior_count,
    COUNT(DISTINCT content_id) AS content_count,
    MIN(event_date) AS first_active_date,
    MAX(event_date) AS last_active_date,
    ROUND(AVG(rating), 2) AS avg_rating
FROM behavior_fact
GROUP BY user_id
ORDER BY behavior_count DESC
LIMIT 100;

-- 6. Explicit subquery: users above average activity
SELECT
    u.user_id,
    u.behavior_count,
    u.content_count
FROM user_dim u
WHERE u.behavior_count > (
    SELECT AVG(behavior_count)
    FROM user_dim
)
ORDER BY u.behavior_count DESC
LIMIT 100;

-- 2. Content ranking with window functions
WITH content_stats AS (
    SELECT
        content_id,
        COUNT(*) AS behavior_count,
        COUNT(DISTINCT user_id) AS active_users,
        ROUND(AVG(rating), 2) AS avg_rating
    FROM behavior_fact
    GROUP BY content_id
)
SELECT
    c.content_id,
    c.title,
    c.genres,
    s.behavior_count,
    s.active_users,
    s.avg_rating,
    RANK() OVER (ORDER BY s.active_users DESC) AS active_user_rank,
    RANK() OVER (ORDER BY s.behavior_count DESC) AS behavior_rank
FROM content_stats s
JOIN content_dim c ON s.content_id = c.content_id
ORDER BY active_user_rank
LIMIT 100;

-- 3. Daily DAU and day-over-day change
WITH daily AS (
    SELECT
        d.date_day,
        COUNT(DISTINCT b.user_id) AS dau
    FROM date_dim d
    LEFT JOIN behavior_fact b ON d.date_day = b.event_date
    GROUP BY d.date_day
)
SELECT
    date_day,
    dau,
    LAG(dau) OVER (ORDER BY date_day) AS previous_dau,
    dau - LAG(dau) OVER (ORDER BY date_day) AS dau_change,
    ROUND(
        (dau - LAG(dau) OVER (ORDER BY date_day)) * 1.0
        / NULLIF(LAG(dau) OVER (ORDER BY date_day), 0),
        4
    ) AS dau_change_rate
FROM daily
ORDER BY date_day;

-- 4. Day-7 retention and return within days 1 to 7
WITH first_active AS (
    SELECT user_id, MIN(event_date) AS first_date
    FROM behavior_fact
    GROUP BY user_id
)
SELECT
    f.first_date,
    COUNT(DISTINCT f.user_id) AS cohort_users,
    COUNT(DISTINCT CASE
        WHEN b.event_date = f.first_date + INTERVAL '7 days'
        THEN f.user_id
    END) AS retained_on_day_7,
    COUNT(DISTINCT CASE
        WHEN b.event_date BETWEEN
             f.first_date + INTERVAL '1 day'
             AND f.first_date + INTERVAL '7 days'
        THEN f.user_id
    END) AS returned_in_days_1_to_7
FROM first_active f
LEFT JOIN behavior_fact b ON f.user_id = b.user_id
GROUP BY f.first_date
ORDER BY f.first_date;

-- 5. Continuous active-day streaks
WITH active_days AS (
    SELECT DISTINCT user_id, event_date
    FROM behavior_fact
), numbered AS (
    SELECT
        user_id,
        event_date,
        ROW_NUMBER() OVER (
            PARTITION BY user_id ORDER BY event_date
        ) AS row_number
    FROM active_days
), grouped AS (
    SELECT
        user_id,
        event_date,
        event_date
            - CAST(row_number AS INTEGER) * INTERVAL '1 day'
            AS streak_key
    FROM numbered
)
SELECT
    user_id,
    MIN(event_date) AS streak_start,
    MAX(event_date) AS streak_end,
    COUNT(*) AS streak_days
FROM grouped
GROUP BY user_id, streak_key
HAVING COUNT(*) >= 3
ORDER BY streak_days DESC, user_id
LIMIT 100;
