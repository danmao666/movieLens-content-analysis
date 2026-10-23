-- The Python version is portable and uses the project-relative dataset path:
--     python code/day01_setup.py
--
-- The statements below are also runnable directly in DuckDB after replacing
-- the two CSV paths if the project is moved to another computer.

CREATE OR REPLACE TABLE content_dim AS
SELECT
    CAST(movieId AS INTEGER) AS content_id,
    title,
    genres
FROM read_csv_auto(
    'C:/Users/17860/Desktop/date analysis/dataset/ml-25m/movies.csv'
);

CREATE OR REPLACE TABLE behavior_fact AS
SELECT
    CAST(userId AS INTEGER) AS user_id,
    CAST(movieId AS INTEGER) AS content_id,
    CAST(rating AS DOUBLE) AS rating,
    to_timestamp(CAST("timestamp" AS BIGINT)) AS event_ts,
    CAST(
        to_timestamp(CAST("timestamp" AS BIGINT)) AS DATE
    ) AS event_date
FROM read_csv_auto(
    'C:/Users/17860/Desktop/date analysis/dataset/ml-25m/ratings.csv'
);

CREATE OR REPLACE TABLE user_dim AS
SELECT
    user_id,
    MIN(event_date) AS first_active_date,
    MAX(event_date) AS last_active_date,
    COUNT(*) AS behavior_count,
    COUNT(DISTINCT content_id) AS content_count
FROM behavior_fact
GROUP BY user_id;

CREATE OR REPLACE TABLE date_dim AS
SELECT
    CAST(day_value AS DATE) AS date_day,
    date_part('year', day_value) AS year,
    date_part('month', day_value) AS month,
    date_part('week', day_value) AS week,
    date_part('dayofweek', day_value) AS weekday
FROM generate_series(
    (SELECT MIN(event_date) FROM behavior_fact),
    (SELECT MAX(event_date) FROM behavior_fact),
    INTERVAL '1 day'
) AS t(day_value);
