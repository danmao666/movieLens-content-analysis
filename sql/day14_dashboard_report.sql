-- Day 14 dashboard/report source queries.

SELECT *
FROM week2_daily_metrics
ORDER BY date_day;

SELECT *
FROM week2_anomaly_monitoring
WHERE is_anomaly = 1
ORDER BY date_day;

SELECT
    user_segment,
    COUNT(*) AS user_count,
    ROUND(AVG(behavior_count), 2) AS avg_behavior_count,
    ROUND(AVG(content_count), 2) AS avg_content_count
FROM week2_user_segments
GROUP BY user_segment
ORDER BY MIN(activity_quartile);

SELECT *
FROM week2_cohort_retention
ORDER BY cohort_month, period_number;

SELECT
    c.content_id,
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

SELECT *
FROM week2_content_concentration
ORDER BY month_start;
