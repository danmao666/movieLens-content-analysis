-- Run code/day07_review.py to export the metric dictionary and conclusion.

-- Daily metrics used by the review
SELECT *
FROM daily_metrics
ORDER BY date_day;

-- Top content after excluding very low-volume titles
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
LIMIT 100;

-- Cohort-level D7 retention
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
    END) AS retained_on_day_7
FROM first_active f
LEFT JOIN behavior_fact b ON f.user_id = b.user_id
GROUP BY f.first_date
ORDER BY f.first_date;
