import argparse

import pandas as pd

from common import DATA_DIR, OUTPUT_DIR


CONCEPTS = """# Day 20: Hadoop and Spark Concepts

## Hadoop architecture

- HDFS stores large files across nodes with replication.
- YARN manages cluster resources and schedules jobs.
- MapReduce is an older batch computation model built around map and reduce phases.
- Spark can use Hadoop storage and resource managers while executing transformations in memory when practical.

## Spark DataFrame concepts

- `select`, `withColumn`, and `filter` are transformations.
- `groupBy` and `join` can create a shuffle when data must be redistributed.
- Window functions calculate ranks or running values over partitions.
- `repartition` changes the physical partition layout and can cause a shuffle.
- `coalesce` reduces partitions without a full redistribution in common cases.
- The number of partitions should be selected based on data size, cluster resources, and downstream work.

## This exercise

The PySpark script reads MovieLens ratings and movies, calculates daily activity, joins content metadata, ranks content by active users within each date, reports partition counts, and saves a physical-plan explanation. The full ratings file is intentionally processed by Spark rather than loaded into pandas.

If PySpark is unavailable, the script still writes this concepts file and a dependency status file. Install PySpark before claiming the Spark execution requirement is complete.
"""


def write_missing_dependency_outputs():
    (OUTPUT_DIR / "ml_day20_spark_concepts.md").write_text(
        CONCEPTS,
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "component": "pyspark",
                "status": "missing",
                "next_step": "python -m pip install pyspark",
            },
            {
                "component": "spark_execution",
                "status": "not_run",
                "next_step": "rerun code/day20_pyspark_metrics.py",
            },
        ]
    ).to_csv(
        OUTPUT_DIR / "ml_day20_spark_status.csv",
        index=False,
        encoding="utf-8-sig",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="Process all ratings. The default local run uses a reproducible 2%% sample.",
    )
    parser.add_argument(
        "--sample-fraction",
        type=float,
        default=0.02,
        help="Fraction of ratings used for the local run when --full is absent.",
    )
    args = parser.parse_args()

    try:
        from pyspark.sql import SparkSession, Window
        from pyspark import StorageLevel
        from pyspark.sql.functions import (
            col,
            count,
            countDistinct,
            desc,
            from_unixtime,
            row_number,
            to_date,
        )
        from pyspark.sql.types import (
            DoubleType,
            LongType,
            StructField,
            StructType,
        )
    except ImportError:
        write_missing_dependency_outputs()
        print(
            "PySpark is not installed. Wrote the Day 20 concepts and status files."
        )
        return

    spark = (
        SparkSession.builder
        .appName("MovieLensWeek3Metrics")
        .master("local[2]")
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.default.parallelism", "4")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")
    try:
        rating_schema = StructType(
            [
                StructField("userId", LongType(), False),
                StructField("movieId", LongType(), False),
                StructField("rating", DoubleType(), False),
                StructField("timestamp", LongType(), False),
            ]
        )
        raw_ratings = (
            spark.read.option("header", True)
            .schema(rating_schema)
            .csv(str(DATA_DIR / "ratings.csv"))
        )
        if args.full:
            ratings = raw_ratings
            sample_mode = "full dataset"
        else:
            fraction = min(max(args.sample_fraction, 0.001), 1.0)
            ratings = raw_ratings.sample(
                withReplacement=False,
                fraction=fraction,
                seed=42,
            )
            sample_mode = f"reproducible sample fraction={fraction}"
        ratings = (
            ratings.withColumn(
                "event_date",
                to_date(from_unixtime(col("timestamp"))),
            )
            .repartition(4)
            .persist(StorageLevel.MEMORY_AND_DISK)
        )
        ratings_rows = ratings.count()
        movies = spark.read.option("header", True).option(
            "inferSchema", True
        ).csv(str(DATA_DIR / "movies.csv"))

        daily = ratings.groupBy("event_date").agg(
            countDistinct("userId").alias("dau"),
            count("userId").alias("behavior_count"),
            countDistinct("movieId").alias("active_content_count"),
        )
        content_daily = ratings.groupBy("event_date", "movieId").agg(
            countDistinct("userId").alias("active_users"),
            count("userId").alias("behavior_count"),
        )
        content_daily = (
            content_daily.alias("activity")
            .join(
                movies.alias("movie"),
                col("activity.movieId") == col("movie.movieId"),
                "left",
            )
            .select(
                col("activity.event_date"),
                col("activity.movieId"),
                col("activity.active_users"),
                col("activity.behavior_count"),
                col("movie.title"),
                col("movie.genres"),
            )
        )
        window = Window.partitionBy("event_date").orderBy(
            desc("active_users"),
            col("movieId"),
        )
        top_content = content_daily.withColumn(
            "content_rank",
            row_number().over(window),
        ).filter(col("content_rank") <= 10)

        daily_sample = daily.orderBy("event_date").limit(10000)
        content_sample = top_content.orderBy(
            "event_date", "content_rank"
        ).limit(10000)
        daily_pd = daily_sample.toPandas()
        content_pd = content_sample.toPandas()
        daily_pd.to_csv(
            OUTPUT_DIR / "ml_day20_spark_daily_metrics.csv",
            index=False,
            encoding="utf-8-sig",
        )
        content_pd.to_csv(
            OUTPUT_DIR / "ml_day20_spark_top_content.csv",
            index=False,
            encoding="utf-8-sig",
        )

        partition_info = pd.DataFrame(
            [
                {
                    "stage": "ratings_input",
                    "partitions": ratings.rdd.getNumPartitions(),
                },
                {
                    "stage": "daily_grouped",
                    "partitions": daily.rdd.getNumPartitions(),
                },
                {
                    "stage": "content_repartition_by_date",
                    "partitions": content_daily.repartition(
                        "event_date"
                    ).rdd.getNumPartitions(),
                },
            ]
        )
        partition_info.to_csv(
            OUTPUT_DIR / "ml_day20_spark_partitions.csv",
            index=False,
            encoding="utf-8-sig",
        )
        plan = daily._jdf.queryExecution().toString()
        (OUTPUT_DIR / "ml_day20_spark_physical_plan.txt").write_text(
            plan,
            encoding="utf-8",
        )
        status = pd.DataFrame(
            [
                {
                    "component": "pyspark",
                    "status": "completed",
                    "spark_version": spark.version,
                    "ratings_rows": ratings_rows,
                    "daily_rows": daily.count(),
                    "sample_mode": sample_mode,
                }
            ]
        )
        status.to_csv(
            OUTPUT_DIR / "ml_day20_spark_status.csv",
            index=False,
            encoding="utf-8-sig",
        )
        (OUTPUT_DIR / "ml_day20_spark_concepts.md").write_text(
            CONCEPTS,
            encoding="utf-8",
        )
        print("Saved Day 20 PySpark metrics and execution artifacts.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
