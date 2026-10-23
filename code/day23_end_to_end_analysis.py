from datetime import date

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from common import OUTPUT_DIR
from week4_common import connect_week4, project_facts, require_week4_tables, save_excel


def save_chart(daily, content, segments, anomaly_dates):
    daily = daily.copy()
    daily["date_day"] = pd.to_datetime(daily["date_day"])

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes[0, 0].plot(daily["date_day"], daily["dau"], color="#2F6B9A")
    axes[0, 0].set_title("DAU trend")
    axes[0, 0].set_ylabel("DAU")

    top_content = content.head(10).sort_values("active_users")
    sns.barplot(
        data=top_content,
        x="active_users",
        y="title",
        color="#59A14F",
        ax=axes[0, 1],
    )
    axes[0, 1].set_title("Top content by active users")

    sns.barplot(
        data=segments,
        x="user_segment",
        y="user_count",
        color="#F28E2B",
        ax=axes[1, 0],
    )
    axes[1, 0].set_title("User activity segments")
    axes[1, 0].tick_params(axis="x", rotation=25)

    anomaly_dates = anomaly_dates.copy()
    anomaly_dates["date_day"] = pd.to_datetime(anomaly_dates["date_day"])
    axes[1, 1].plot(daily["date_day"], daily["dau"], color="#2F6B9A")
    if not anomaly_dates.empty:
        axes[1, 1].scatter(
            anomaly_dates["date_day"],
            anomaly_dates["dau"],
            color="#C00000",
            s=12,
        )
    axes[1, 1].set_title("Anomaly dates")
    axes[1, 1].set_ylabel("DAU")

    fig.suptitle("End-to-End Content Platform Analysis", fontsize=16)
    fig.tight_layout()
    path = OUTPUT_DIR / "ml_day23_end_to_end_summary.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> None:
    sns.set_theme(style="whitegrid")
    connection = connect_week4()
    try:
        require_week4_tables(
            connection,
            "behavior_fact",
            "content_dim",
            "week2_daily_metrics",
            "week2_user_segments",
            "week2_cohort_retention",
            "week2_anomaly_monitoring",
        )
        facts = project_facts(connection)
        daily = connection.sql("""
            SELECT * FROM week2_daily_metrics ORDER BY date_day
        """).df()
        content = connection.sql("""
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
            LIMIT 100
        """).df()
        segments = connection.sql("""
            SELECT
                user_segment,
                COUNT(*) AS user_count,
                ROUND(AVG(behavior_count), 2) AS avg_behavior_count,
                ROUND(AVG(content_count), 2) AS avg_content_count
            FROM week2_user_segments
            GROUP BY user_segment
            ORDER BY MIN(activity_quartile)
        """).df()
        retention = connection.sql("""
            SELECT * FROM week2_cohort_retention
            ORDER BY cohort_month, period_number
        """).df()
        anomalies = connection.sql("""
            SELECT * FROM week2_anomaly_monitoring
            WHERE is_anomaly = 1
            ORDER BY date_day
        """).df()
        cause_summary = (
            anomalies.groupby("diagnostic_reason", as_index=False)
            .agg(anomaly_count=("date_day", "count"))
            .sort_values("anomaly_count", ascending=False)
        )
        chart = save_chart(daily, content, segments, anomalies)

        d7 = retention.loc[
            retention["period_number"] == 1, "retention_rate"
        ]
        d7_rate = float(d7.mean()) if not d7.empty else 0.0
        top_segment = segments.sort_values("user_count", ascending=False).iloc[0]

        report = f"""# Day 23: End-to-End Analysis Report

## 1. Business problem

The project evaluates user rating activity, content reach, retention proxies, and daily metric stability for a simulated content platform. It uses MovieLens 25M public data, not real company data.

## 2. Metric definitions

- DAU: distinct users with at least one rating on a date.
- New-user proxy: first observed rating on a date because registration data is unavailable.
- Content reach: distinct users rating a content item.
- D7 retention: users with a rating exactly seven days after first observed activity divided by the cohort size.
- Anomaly: a date flagged by a historical z-score or change-rate rule.

## 3. Data discovery

- Records: {int(facts['scale']['behavior_count']):,}.
- Users: {int(facts['scale']['user_count']):,}.
- Content items: {int(facts['scale']['content_count']):,}.
- Date range: {facts['scale']['first_date']} to {facts['scale']['last_date']}.
- Latest observed DAU: {int(facts['latest']['dau']):,} on {facts['latest']['date_day']}.
- Highest qualifying content by active users: {facts['top_content']['title']} with {int(facts['top_content']['active_users']):,} users.
- Average monthly period-1 cohort retention where available: {d7_rate:.2%}.
- Largest activity segment: {top_segment['user_segment']} with {int(top_segment['user_count']):,} users.

## 4. Cause judgment

The data supports associations, not causal conclusions. DAU movement should be investigated with behavior volume, active content, user segments, and pipeline completeness. The anomaly cause summary is an automated diagnostic direction only; product, campaign, release, and data-pipeline logs would be needed to confirm a cause.

## 5. Optimization suggestions

1. Target activity segments with personalized recommendation or re-engagement experiments.
2. Use high-reach content as recommendation candidates while monitoring long-tail content coverage.
3. Monitor retention and content concentration together to avoid optimizing activity at the expense of diversity.
4. Treat anomaly dates as an investigation queue with an owner and resolution status.

## 6. Validation plan

Use the Day 13 user-level A/B plan. The primary metric is seven-day rating-active rate. Guardrails include ratings per active user, content diversity, rating quality, sample-ratio mismatch, and event completeness. Report absolute lift, relative lift, p-value, and a 95% confidence interval.

## 7. Data limitations

MovieLens has ratings and tags but no registrations, impressions, clicks, watch time, demographics, campaigns, recommendation exposures, or product-release events. Churn, retention, new users, and activity are proxies. The results must not be described as real-company outcomes.

## Reproduction

- Summary chart: `{chart.name}`.
- Data workbook: `ml_day23_end_to_end_analysis.xlsx`.
- Source tables: DuckDB `content_platform.duckdb`.

Generated on: {date.today().isoformat()}
"""
        output = save_excel(
            {
                "overview": pd.DataFrame([facts["latest"]]),
                "daily_metrics": daily,
                "content_activity": content,
                "user_segments": segments,
                "retention": retention,
                "anomalies": anomalies,
                "cause_summary": cause_summary,
            },
            "ml_day23_end_to_end_analysis.xlsx",
        )
        daily.to_csv(
            OUTPUT_DIR / "ml_day23_daily_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        (OUTPUT_DIR / "ml_day23_end_to_end_report.md").write_text(
            report,
            encoding="utf-8",
        )
        print(f"Saved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
