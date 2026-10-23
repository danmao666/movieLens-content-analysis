-- Run code/day05_excel_dashboard.py to export the Excel dashboard.

SELECT *
FROM daily_metrics
ORDER BY date_day;

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
LIMIT 50;

SELECT
    CASE
        WHEN behavior_count >= 50 THEN 'high'
        WHEN behavior_count >= 20 THEN 'middle'
        ELSE 'low'
    END AS user_segment,
    COUNT(*) AS user_count,
    ROUND(AVG(behavior_count), 2) AS avg_behavior_count
FROM user_dim
GROUP BY user_segment
ORDER BY user_segment;
