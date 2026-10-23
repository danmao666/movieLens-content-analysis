-- Run code/day04_quality_monitoring.py to create daily_metrics and export checks.

-- 1. Invalid values
SELECT COUNT(*) AS invalid_rows
FROM behavior_fact
WHERE user_id IS NULL
   OR content_id IS NULL
   OR event_date IS NULL
   OR rating NOT BETWEEN 0.5 AND 5;

-- 2. Behaviors whose content ID is not in the content table
SELECT COUNT(*) AS orphan_rows
FROM behavior_fact b
LEFT JOIN content_dim c ON b.content_id = c.content_id
WHERE c.content_id IS NULL;

-- 3. Potential exact duplicate events
SELECT
    user_id,
    content_id,
    event_ts,
    COUNT(*) AS duplicate_count
FROM behavior_fact
GROUP BY user_id, content_id, event_ts
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 100;

-- 4. Daily metric table with a seven-day historical baseline
CREATE OR REPLACE TABLE daily_metrics AS
WITH daily AS (
    SELECT
        d.date_day,
        COUNT(DISTINCT b.user_id) AS dau,
        COUNT(b.user_id) AS behavior_count,
        COUNT(DISTINCT b.content_id) AS active_content_count,
        COUNT(DISTINCT CASE
            WHEN u.first_active_date = d.date_day THEN b.user_id
        END) AS new_users,
        ROUND(AVG(b.rating), 2) AS avg_rating
    FROM date_dim d
    LEFT JOIN behavior_fact b ON d.date_day = b.event_date
    LEFT JOIN user_dim u ON b.user_id = u.user_id
    GROUP BY d.date_day
), with_baseline AS (
    SELECT
        *,
        AVG(dau) OVER (
            ORDER BY date_day
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) AS dau_7d_avg,
        STDDEV_SAMP(dau) OVER (
            ORDER BY date_day
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) AS dau_7d_sd
    FROM daily
)
SELECT
    *,
    CASE
        WHEN dau_7d_sd IS NOT NULL
         AND ABS(dau - dau_7d_avg) > 2 * dau_7d_sd
        THEN 1
        ELSE 0
    END AS is_dau_anomaly
FROM with_baseline
ORDER BY date_day;

-- 5. Dates marked as anomalies
SELECT *
FROM daily_metrics
WHERE is_dau_anomaly = 1
ORDER BY date_day;

-- 6. User activity funnel
WITH user_stats AS (
    SELECT user_id, COUNT(*) AS behavior_count
    FROM behavior_fact
    GROUP BY user_id
)
SELECT
    SUM(CASE WHEN behavior_count >= 1 THEN 1 ELSE 0 END)
        AS users_with_1_plus_behavior,
    SUM(CASE WHEN behavior_count >= 5 THEN 1 ELSE 0 END)
        AS users_with_5_plus_behavior,
    SUM(CASE WHEN behavior_count >= 20 THEN 1 ELSE 0 END)
        AS users_with_20_plus_behavior,
    SUM(CASE WHEN behavior_count >= 50 THEN 1 ELSE 0 END)
        AS users_with_50_plus_behavior
FROM user_stats;

-- 7. Seven-day rolling monitoring output
SELECT
    date_day,
    dau,
    behavior_count,
    active_content_count,
    dau_7d_avg,
    dau_7d_sd,
    is_dau_anomaly
FROM daily_metrics
ORDER BY date_day;
