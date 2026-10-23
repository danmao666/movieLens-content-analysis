-- Day 22: 90-minute SQL timed test answer key.
-- Try the four prompts without reading the answer key first.

-- SQL01: D1/D7/D30 cohort retention
WITH first_active AS (
    SELECT user_id, MIN(event_date) AS first_date
    FROM behavior_fact
    GROUP BY user_id
), cohort AS (
    SELECT
        f.first_date,
        COUNT(DISTINCT f.user_id) AS cohort_users,
        COUNT(DISTINCT CASE
            WHEN a.event_date = f.first_date + INTERVAL '1 day'
            THEN f.user_id END) AS retained_d1,
        COUNT(DISTINCT CASE
            WHEN a.event_date = f.first_date + INTERVAL '7 days'
            THEN f.user_id END) AS retained_d7,
        COUNT(DISTINCT CASE
            WHEN a.event_date = f.first_date + INTERVAL '30 days'
            THEN f.user_id END) AS retained_d30
    FROM first_active f
    LEFT JOIN behavior_fact a ON f.user_id = a.user_id
    GROUP BY f.first_date
)
SELECT
    *,
    ROUND(retained_d1 * 1.0 / NULLIF(cohort_users, 0), 4) AS d1_rate,
    ROUND(retained_d7 * 1.0 / NULLIF(cohort_users, 0), 4) AS d7_rate,
    ROUND(retained_d30 * 1.0 / NULLIF(cohort_users, 0), 4) AS d30_rate
FROM cohort
ORDER BY first_date;

-- SQL02: behavior funnel
WITH user_stats AS (
    SELECT user_id, COUNT(*) AS behavior_count
    FROM behavior_fact
    GROUP BY user_id
), funnel AS (
    SELECT
        COUNT(*) AS total_users,
        SUM(CASE WHEN behavior_count >= 1 THEN 1 ELSE 0 END) AS users_1_plus,
        SUM(CASE WHEN behavior_count >= 5 THEN 1 ELSE 0 END) AS users_5_plus,
        SUM(CASE WHEN behavior_count >= 20 THEN 1 ELSE 0 END) AS users_20_plus,
        SUM(CASE WHEN behavior_count >= 50 THEN 1 ELSE 0 END) AS users_50_plus
    FROM user_stats
)
SELECT
    *,
    ROUND(users_1_plus * 1.0 / total_users, 4) AS rate_1_plus,
    ROUND(users_5_plus * 1.0 / total_users, 4) AS rate_5_plus,
    ROUND(users_20_plus * 1.0 / total_users, 4) AS rate_20_plus,
    ROUND(users_50_plus * 1.0 / total_users, 4) AS rate_50_plus
FROM funnel;

-- SQL03: Top 3 content within each primary genre
WITH content_stats AS (
    SELECT
        c.content_id,
        c.title,
        split_part(c.genres, '|', 1) AS primary_genre,
        COUNT(*) AS behavior_count,
        COUNT(DISTINCT b.user_id) AS active_users,
        ROUND(AVG(b.rating), 2) AS avg_rating
    FROM behavior_fact b
    JOIN content_dim c ON b.content_id = c.content_id
    GROUP BY c.content_id, c.title, c.genres
), ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY primary_genre
            ORDER BY active_users DESC, behavior_count DESC
        ) AS genre_rank
    FROM content_stats
)
SELECT *
FROM ranked
WHERE genre_rank <= 3
ORDER BY primary_genre, genre_rank;

-- SQL04: anomaly indicators
WITH history AS (
    SELECT
        *,
        LAG(dau) OVER (ORDER BY date_day) AS previous_dau,
        AVG(dau) OVER (
            ORDER BY date_day
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS dau_28d_avg,
        STDDEV_SAMP(dau) OVER (
            ORDER BY date_day
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS dau_28d_sd
    FROM week2_daily_metrics
)
SELECT
    date_day,
    dau,
    previous_dau,
    ROUND((dau - previous_dau) * 1.0 / NULLIF(previous_dau, 0), 4)
        AS dau_change_rate,
    dau_28d_avg,
    dau_28d_sd,
    CASE
        WHEN dau_28d_sd > 0
        THEN ROUND((dau - dau_28d_avg) / dau_28d_sd, 4)
    END AS dau_z_score,
    CASE
        WHEN dau_28d_sd > 0
         AND ABS((dau - dau_28d_avg) / dau_28d_sd) >= 2
        THEN 1 ELSE 0
    END AS is_anomaly
FROM history
ORDER BY date_day;
