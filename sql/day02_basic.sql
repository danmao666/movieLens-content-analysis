-- Run code/day02_sql_basics.py to execute every query and export an Excel file.

-- 1. Overall scale
SELECT
    COUNT(*) AS behavior_count,
    COUNT(DISTINCT user_id) AS user_count,
    COUNT(DISTINCT content_id) AS content_count,
    MIN(event_date) AS first_date,
    MAX(event_date) AS last_date
FROM behavior_fact;

-- 2. Rating distribution
SELECT rating, COUNT(*) AS rating_count
FROM behavior_fact
GROUP BY rating
ORDER BY rating;

-- 3. Daily active users
SELECT
    event_date,
    COUNT(DISTINCT user_id) AS dau,
    COUNT(*) AS behavior_count
FROM behavior_fact
GROUP BY event_date
ORDER BY event_date;

-- 4. Content performance
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
LIMIT 50;

-- 5. User activity ranking
SELECT
    user_id,
    COUNT(*) AS behavior_count,
    COUNT(DISTINCT content_id) AS content_count,
    ROUND(AVG(rating), 2) AS avg_rating
FROM behavior_fact
GROUP BY user_id
ORDER BY behavior_count DESC
LIMIT 50;

-- 6. Rating levels
SELECT
    CASE
        WHEN rating >= 4 THEN 'high'
        WHEN rating >= 3 THEN 'middle'
        ELSE 'low'
    END AS rating_level,
    COUNT(*) AS behavior_count,
    ROUND(AVG(rating), 2) AS avg_rating
FROM behavior_fact
GROUP BY rating_level
ORDER BY rating_level;

-- 7. Genre performance
SELECT
    g.genre,
    COUNT(*) AS behavior_count,
    COUNT(DISTINCT b.user_id) AS active_users,
    COUNT(DISTINCT b.content_id) AS active_content_count,
    ROUND(AVG(b.rating), 2) AS avg_rating
FROM behavior_fact b
JOIN content_dim c ON b.content_id = c.content_id
CROSS JOIN UNNEST(string_split(c.genres, '|')) AS g(genre)
GROUP BY g.genre
HAVING COUNT(*) >= 1000
ORDER BY active_users DESC;

-- 8. User segments
WITH user_stats AS (
    SELECT user_id, COUNT(*) AS behavior_count
    FROM behavior_fact
    GROUP BY user_id
)
SELECT
    CASE
        WHEN behavior_count >= 50 THEN 'high'
        WHEN behavior_count >= 20 THEN 'middle'
        ELSE 'low'
    END AS user_segment,
    COUNT(*) AS user_count,
    ROUND(AVG(behavior_count), 2) AS avg_behavior_count
FROM user_stats
GROUP BY user_segment
ORDER BY user_segment;

-- 9. Content with both sufficient volume and high average rating
SELECT
    c.title,
    COUNT(*) AS behavior_count,
    ROUND(AVG(b.rating), 2) AS avg_rating
FROM behavior_fact b
JOIN content_dim c ON b.content_id = c.content_id
GROUP BY c.content_id, c.title
HAVING COUNT(*) >= 100
   AND AVG(b.rating) >= 4
ORDER BY avg_rating DESC, behavior_count DESC
LIMIT 50;

-- 10. Monthly active users using a date function
SELECT
    DATE_TRUNC('month', event_date) AS month_start,
    COUNT(DISTINCT user_id) AS mau,
    COUNT(*) AS behavior_count
FROM behavior_fact
GROUP BY month_start
ORDER BY month_start;
