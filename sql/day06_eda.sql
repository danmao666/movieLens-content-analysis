-- Run code/day06_eda.py to create charts and the EDA workbook.

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
LIMIT 100;

SELECT
    u.user_id,
    u.behavior_count,
    u.content_count,
    ROUND(AVG(b.rating), 2) AS avg_rating
FROM user_dim u
JOIN behavior_fact b ON u.user_id = b.user_id
GROUP BY u.user_id, u.behavior_count, u.content_count;
