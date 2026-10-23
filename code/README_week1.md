# Week 1 Code

The project uses the existing Miniconda `base` environment and the existing MovieLens 25M files.

## How this maps to the 30-day plan

The 30-day project target is an end-to-end simulated content-platform project:

- SQL for multi-table joins, CTEs, window functions, retention, funnels, and anomaly monitoring.
- Python for data cleaning, exploratory analysis, visualisation, and later modelling.
- Excel for a KPI monitoring dashboard.
- R as a secondary tool, reproducing one analysis chart on Day 7.
- A reproducible database and outputs that become the input for Week 2 business analysis.

These scripts are intentionally based on the actual MovieLens 25M data, not the earlier seven-row practice data. MovieLens ratings are a proxy for content-platform behaviour; they are not real viewing, click, or company data.

## Paths

- Dataset: `C:\Users\17860\Desktop\date analysis\dataset\ml-25m`
- Code: `C:\Users\17860\Desktop\date analysis\code`
- SQL: `C:\Users\17860\Desktop\date analysis\sql`
- Outputs: `C:\Users\17860\Desktop\date analysis\days`
- Database: `C:\Users\17860\Desktop\date analysis\content_platform.duckdb`

## Run order

Run these commands from the project directory in the Miniconda terminal:

```powershell
Set-Location -LiteralPath 'C:\Users\17860\Desktop\date analysis'
python code/day01_setup.py
python code/day02_sql_basics.py
python code/day03_sql_advanced.py
python code/day04_quality_monitoring.py
python code/day05_excel_dashboard.py
python code/day06_eda.py
python code/day07_review.py
Rscript code/day07_r_dau.R
```

`days` remains the output directory for Excel files, CSV files, charts, and the review report. The scripts do not delete the previous files in that directory. Their MovieLens outputs use the `ml_` prefix so they can be distinguished from the earlier small practice dataset outputs.

## Day mapping

### Day 1: baseline, environment, data, and project tables

Required task: confirm the working Python/Jupyter environment, profile the chosen data, and create a reusable data model.

Script output:

- `content_dim`
- `behavior_fact`
- `user_dim`
- `date_dim`
- environment, dataset, and table-count workbook

Acceptance: the data source, row counts, date range, table meanings, and current SQL/Python/Excel baseline are recorded.

### Day 2: basic SQL, eight to ten business questions

Required task: practice `SELECT`, filters, aggregation, `CASE WHEN`, `JOIN`, dates, `COUNT(DISTINCT)`, and ranking.

Script output: ten query result sheets covering scale, ratings, DAU, content, users, rating levels, genres, segments, high-rated content, and monthly activity.

Acceptance: at least eight to ten independent SQL questions are completed and interpretable.

### Day 3: advanced SQL

Required task: use CTEs, a subquery, window functions, date arithmetic, ranking, retention, and continuous-date analysis.

Script output: user statistics, content ranks, DAU day-over-day changes, D7 retention, active streaks, and users above average activity.

Acceptance: the queries explain not only how many records exist, but how user and content behaviour changes over time.

### Day 4: quality, funnel, and monitoring logic

Required task: identify nulls, invalid values, orphan keys, duplicates, calculate a simple activity funnel, and create seven-day rolling mean/standard deviation thresholds.

Script output: quality checks, funnel counts, daily metrics, rolling baseline, and anomaly dates.

Acceptance: every flagged problem has a check method, and every daily metric has a definition.

### Day 5: Excel dashboard

Required task: produce a usable daily dashboard rather than only formulas. The workbook contains KPI cards, a pivot-style monthly summary, `XLOOKUP`, `SUMIFS`, conditional formatting, and charts.

Acceptance: open `ml_day05_content_dashboard.xlsx` in Excel, recalculate formulas if necessary, and explain what each visual is used to monitor.

### Day 6: Python cleaning and EDA

Required task: use pandas, NumPy, Matplotlib, and Seaborn; check missing values, duplicate rows, invalid/outlier values, and explain the business meaning of each chart.

Script output: DAU trend, content ranking, user activity, rating distribution charts, EDA workbook, SQL quality results, and a bounded pandas cleaning sample check.

Acceptance: every chart has a written interpretation; the project does not load all 25 million ratings into pandas at once.

### Day 7: review, conclusion, and R reproduction

Required task: write the metric dictionary and one-page conclusion, distinguish observed facts from hypotheses, state data limitations, and reproduce the DAU chart with `dplyr` and `ggplot2`.

Acceptance: the conclusion is suitable as the starting point for Day 8 business questions and does not claim MovieLens results are real-company results.

## First-week acceptance against the monthly target

- More than 30 SQL statements are available across `sql/day01_schema.sql` through `sql/day07_review.sql`.
- SQL includes joins, CTEs, window functions, Top N, retention, funnel, deduplication, and anomaly detection.
- Python creates a reproducible DuckDB model and a structured EDA output.
- Excel contains a monitoring dashboard, not only a raw data sheet.
- R reproduces one chart as a secondary skill.
- Day 7 outputs provide the metric definitions and evidence needed for Week 2.
