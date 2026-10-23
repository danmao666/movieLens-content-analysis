-- Day 12: daily change, rolling mean, standard deviation, and thresholds.

CREATE OR REPLACE TABLE week2_anomaly_monitoring AS
WITH history AS (
    SELECT
        m.*,
        LAG(dau) OVER (ORDER BY date_day) AS previous_dau,
        LAG(behavior_count) OVER (ORDER BY date_day) AS previous_behavior_count,
        LAG(active_content_count) OVER (ORDER BY date_day)
            AS previous_active_content_count,
        LAG(new_users) OVER (ORDER BY date_day) AS previous_new_users,
        AVG(dau) OVER (
            ORDER BY date_day ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS dau_28d_avg,
        STDDEV_SAMP(dau) OVER (
            ORDER BY date_day ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS dau_28d_sd,
        COUNT(dau) OVER (
            ORDER BY date_day ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
        ) AS baseline_days
    FROM week2_daily_metrics m
), scored AS (
    SELECT
        *,
        ROUND((dau - previous_dau) * 1.0 / NULLIF(previous_dau, 0), 4)
            AS dau_change_rate,
        ROUND((behavior_count - previous_behavior_count) * 1.0
            / NULLIF(previous_behavior_count, 0), 4)
            AS behavior_change_rate,
        ROUND((active_content_count - previous_active_content_count) * 1.0
            / NULLIF(previous_active_content_count, 0), 4)
            AS active_content_change_rate,
        ROUND((new_users - previous_new_users) * 1.0
            / NULLIF(previous_new_users, 0), 4)
            AS new_users_change_rate,
        CASE
            WHEN dau_28d_sd > 0
            THEN ROUND((dau - dau_28d_avg) / dau_28d_sd, 4)
        END AS dau_z_score
    FROM history
), flagged AS (
    SELECT
        *,
        CASE
            WHEN baseline_days >= 7
             AND (ABS(dau_z_score) >= 2 OR ABS(dau_change_rate) >= 0.30)
            THEN 1
            ELSE 0
        END AS is_anomaly,
        CASE
            WHEN baseline_days < 7 THEN 'insufficient baseline'
            WHEN ABS(dau_z_score) >= 2 THEN 'z-score threshold'
            WHEN ABS(dau_change_rate) >= 0.30 THEN 'change-rate threshold'
            ELSE 'normal'
        END AS anomaly_rule
    FROM scored
)
SELECT
    *,
    CASE
        WHEN is_anomaly = 0 THEN 'normal'
        WHEN behavior_change_rate <= -0.30
         AND active_content_change_rate <= -0.30
            THEN 'behavior and content decrease'
        WHEN behavior_change_rate <= -0.30 THEN 'behavior volume decrease'
        WHEN active_content_change_rate <= -0.30 THEN 'active content decrease'
        WHEN new_users_change_rate <= -0.30 THEN 'new-user proxy decrease'
        WHEN behavior_change_rate >= 0.30 THEN 'behavior volume increase'
        ELSE 'needs investigation'
    END AS diagnostic_reason
FROM flagged
ORDER BY date_day;

SELECT *
FROM week2_anomaly_monitoring
WHERE is_anomaly = 1
ORDER BY date_day;
