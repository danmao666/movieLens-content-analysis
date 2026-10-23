import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from common import OUTPUT_DIR
from week2_common import connect_week2, require_week2_tables, save_excel


MONITORING_SQL = """
    CREATE OR REPLACE TABLE week2_anomaly_monitoring AS
    WITH history AS (
        SELECT
            m.*,
            LAG(dau) OVER (ORDER BY date_day) AS previous_dau,
            LAG(behavior_count) OVER (ORDER BY date_day)
                AS previous_behavior_count,
            LAG(active_content_count) OVER (ORDER BY date_day)
                AS previous_active_content_count,
            LAG(new_users) OVER (ORDER BY date_day) AS previous_new_users,
            AVG(dau) OVER (
                ORDER BY date_day
                ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
            ) AS dau_28d_avg,
            STDDEV_SAMP(dau) OVER (
                ORDER BY date_day
                ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
            ) AS dau_28d_sd,
            COUNT(dau) OVER (
                ORDER BY date_day
                ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
            ) AS baseline_days
        FROM week2_daily_metrics m
    ),
    scored AS (
        SELECT
            *,
            ROUND(
                (dau - previous_dau) * 1.0
                / NULLIF(previous_dau, 0),
                4
            ) AS dau_change_rate,
            ROUND(
                (behavior_count - previous_behavior_count) * 1.0
                / NULLIF(previous_behavior_count, 0),
                4
            ) AS behavior_change_rate,
            ROUND(
                (active_content_count - previous_active_content_count) * 1.0
                / NULLIF(previous_active_content_count, 0),
                4
            ) AS active_content_change_rate,
            ROUND(
                (new_users - previous_new_users) * 1.0
                / NULLIF(previous_new_users, 0),
                4
            ) AS new_users_change_rate,
            CASE
                WHEN dau_28d_sd > 0
                THEN ROUND((dau - dau_28d_avg) / dau_28d_sd, 4)
            END AS dau_z_score
        FROM history
    ),
    flagged AS (
        SELECT
            *,
            CASE
                WHEN baseline_days >= 7
                 AND (
                     ABS(dau_z_score) >= 2
                     OR ABS(dau_change_rate) >= 0.30
                 )
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
            WHEN behavior_change_rate <= -0.30
                THEN 'behavior volume decrease'
            WHEN active_content_change_rate <= -0.30
                THEN 'active content decrease'
            WHEN new_users_change_rate <= -0.30
                THEN 'new-user proxy decrease'
            WHEN behavior_change_rate >= 0.30
                THEN 'behavior volume increase'
            ELSE 'needs investigation'
        END AS diagnostic_reason
    FROM flagged
    ORDER BY date_day
"""


def save_monitor_chart(monitor: pd.DataFrame) -> None:
    monitor = monitor.copy()
    monitor["date_day"] = pd.to_datetime(monitor["date_day"])
    plt.figure(figsize=(15, 6))
    plt.plot(monitor["date_day"], monitor["dau"], label="DAU", color="#2F6B9A")
    plt.plot(
        monitor["date_day"],
        monitor["dau_28d_avg"],
        label="28-day baseline",
        color="#F28E2B",
    )
    plt.plot(
        monitor["date_day"],
        monitor["dau_28d_avg"] + 2 * monitor["dau_28d_sd"],
        label="upper threshold",
        color="#999999",
        linestyle="--",
    )
    plt.plot(
        monitor["date_day"],
        monitor["dau_28d_avg"] - 2 * monitor["dau_28d_sd"],
        label="lower threshold",
        color="#999999",
        linestyle="--",
    )
    anomalies = monitor[monitor["is_anomaly"] == 1]
    plt.scatter(
        anomalies["date_day"],
        anomalies["dau"],
        color="#C00000",
        label="anomaly",
        zorder=3,
    )
    plt.title("DAU Anomaly Monitoring")
    plt.xlabel("Date")
    plt.ylabel("DAU")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "ml_day12_anomaly_monitoring.png", dpi=150)
    plt.close()


def main() -> None:
    sns.set_theme(style="whitegrid")
    connection = connect_week2()
    try:
        require_week2_tables(connection, "week2_daily_metrics")
        connection.execute(MONITORING_SQL)
        monitor = connection.sql("""
            SELECT *
            FROM week2_anomaly_monitoring
            ORDER BY date_day
        """).df()
        anomalies = monitor[monitor["is_anomaly"] == 1].copy()
        reasons = (
            anomalies.groupby("diagnostic_reason", as_index=False)
            .agg(anomaly_count=("date_day", "count"))
            .sort_values("anomaly_count", ascending=False)
        )
        save_monitor_chart(monitor)
        output = save_excel(
            {
                "monitoring": monitor,
                "anomaly_dates": anomalies,
                "cause_summary": reasons,
            },
            "ml_day12_anomaly_monitoring.xlsx",
        )
        monitor.to_csv(
            OUTPUT_DIR / "ml_day12_anomaly_monitoring.csv",
            index=False,
            encoding="utf-8-sig",
        )
        anomalies.to_csv(
            OUTPUT_DIR / "ml_day12_anomaly_dates.csv",
            index=False,
            encoding="utf-8-sig",
        )

        report = f"""# Day 12: Anomaly Monitoring

## Monitoring method

- Daily comparison: current DAU against the previous observed date.
- Historical baseline: the previous 28 calendar rows, excluding the current date.
- Statistical threshold: absolute z-score at least 2 after at least 7 baseline rows.
- Change-rate threshold: absolute DAU change of at least 30 percent.
- Diagnostic fields: behavior volume, active content, and new-user proxy change rates.

## Current output

The monitor marked {len(anomalies):,} rows as potential anomalies. These are investigation triggers, not confirmed incidents. The `diagnostic_reason` field gives the first automated direction for investigation.

## Investigation order

1. Confirm the date and compare DAU with behavior count and active content.
2. Check whether the movement is isolated to new users or broad across user segments.
3. Check content and data-pipeline completeness.
4. Check product, campaign, release, or external-event logs when available.

The threshold and reason rules are implemented in `code/day12_anomaly_monitoring.py` and `sql/day12_anomaly_monitoring.sql`.
"""
        (OUTPUT_DIR / "ml_day12_anomaly_monitoring.md").write_text(
            report,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
