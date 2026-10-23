# Week 2 Code

Week 2 follows the 30-day target: turn the Week 1 data model into business analysis, monitoring, experiment design, and a presentable dashboard/report.

The project continues to use:

- Python + DuckDB + SQL as the main path.
- The existing MovieLens 25M data under `dataset/ml-25m`.
- `days` for Excel, CSV, PNG, and Markdown outputs.
- The same `content_platform.duckdb` created in Week 1.

MovieLens contains ratings and tags, not real impressions, clicks, viewing time, registrations, campaigns, or company event logs. Every Week 2 report must describe rating activity as a proxy and must not present the results as real-company results.

## Run order

Use Anaconda Prompt or another terminal where the Miniconda `base` environment is active. Run scripts one at a time from the project directory:

```bat
cd /d "C:\Users\17860\Desktop\date analysis"

python code\day08_business_questions.py
python code\day09_schema_and_metrics.py
python code\day10_trend_analysis.py
python code\day11_segmentation_cohort.py
python code\day12_anomaly_monitoring.py
python code\day13_ab_experiment.py
python code\day14_dashboard_report.py
```

The scripts share one DuckDB file, so do not run them concurrently. Day 8 and Day 13 are primarily documentation/design tasks; the scripts save reproducible Markdown and CSV outputs rather than inventing business or experiment results.

## Day mapping and acceptance

### Day 8: business questions

- Defines churn, high-activity content, and metric fluctuation questions.
- Defines DAU, new-user proxy, content active users, D7 retention, concentration, and anomaly metrics.
- Records the public-data limitations and decisions the analysis should support.

Outputs:

- `days/ml_day08_business_questions.md`
- `days/ml_day08_business_questions.csv`
- `days/ml_day08_metric_definitions.csv`

### Day 9: data model and daily SQL metrics

- Reuses Week 1 `user_dim`, `content_dim`, `behavior_fact`, and `date_dim`.
- Creates user-day and content-day aggregate tables.
- Creates `week2_daily_metrics` with DAU, new users, behavior count, active content, average rating, and ratings per active user.

Outputs:

- `sql/day09_schema_and_metrics.sql`
- `days/ml_day09_schema_and_metrics.xlsx`
- `days/ml_day09_daily_metrics.csv`

### Day 10: trends and concentration

- Calculates daily trends, day-over-day changes, seven-day averages, D1/D7/D30 retention, user frequency buckets, and top-ten content concentration.
- Produces trend charts and a written interpretation.

Outputs:

- `sql/day10_trend_analysis.sql`
- `days/ml_day10_trend_analysis.xlsx`
- `days/ml_day10_dau_trend.png`
- `days/ml_day10_retention_trend.png`
- `days/ml_day10_content_concentration.png`
- `days/ml_day10_trend_analysis.md`

### Day 11: user/content segmentation and cohorts

- Uses SQL `NTILE(4)` to create user activity quartiles.
- Categorizes content by the first MovieLens genre field.
- Builds monthly user cohorts and period retention.
- Produces segment, genre, and cohort visualizations.

Outputs:

- `sql/day11_segmentation_cohort.sql`
- `days/ml_day11_segmentation_and_cohort.xlsx`
- `days/ml_day11_user_segments.png`
- `days/ml_day11_genre_performance.png`
- `days/ml_day11_cohort_retention.png`
- `days/ml_day11_segmentation_and_cohort.md`

### Day 12: anomaly monitoring

- Calculates previous-day change rates.
- Calculates a 28-row historical moving average and standard deviation.
- Uses a minimum baseline, absolute z-score threshold, and change-rate threshold.
- Adds a first diagnostic reason based on behavior, active content, and new-user movement.

Outputs:

- `sql/day12_anomaly_monitoring.sql`
- `days/ml_day12_anomaly_monitoring.xlsx`
- `days/ml_day12_anomaly_monitoring.csv`
- `days/ml_day12_anomaly_dates.csv`
- `days/ml_day12_anomaly_monitoring.png`
- `days/ml_day12_anomaly_monitoring.md`

An anomaly is an investigation trigger, not proof of a product incident or business cause.

### Day 13: A/B experiment design

- Defines the recommendation hypothesis, user-level randomization, control, treatment, primary metric, guardrails, alpha, confidence interval, power, and decision rule.
- Does not fabricate treatment/control results because MovieLens has no randomized experiment assignment.

Outputs:

- `sql/day13_ab_experiment.sql`
- `days/ml_day13_ab_experiment_plan.md`
- `days/ml_day13_ab_experiment_plan.csv`

### Day 14: dashboard and report

- Combines overview KPIs, daily trends, anomaly dates, user segments, retention, content ranking, content concentration, cause summary, and actions.
- Creates an Excel dashboard and a report draft with the required seven sections.

Outputs:

- `sql/day14_dashboard_report.sql`
- `days/ml_day14_dashboard.xlsx`
- `days/ml_day14_report_draft.md`

## Week 2 acceptance against the 30-day plan

- Business questions are explicit and tied to metrics.
- Daily metrics are reproducible from SQL and the four core tables.
- Trends include DAU, retention, content activity, frequency, and concentration.
- User, content, and cohort results are saved and interpretable.
- Anomaly monitoring includes change rate, moving average, standard deviation, threshold, and diagnostic direction.
- A/B plan includes hypothesis, randomization unit, primary metric, guardrails, significance, confidence interval, and decision rule.
- Dashboard contains the required sections from the monthly plan.
- Report contains business problem, metric definitions, findings, cause judgment, suggestions, validation, and limitations.
