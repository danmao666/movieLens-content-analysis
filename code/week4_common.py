from pathlib import Path

import pandas as pd

from common import DB_PATH, OUTPUT_DIR, connect, require_tables


PROJECT_DIR = Path(__file__).resolve().parents[1]
PORTFOLIO_DIR = PROJECT_DIR / "portfolio"


def connect_week4():
    return connect()


def require_week4_tables(connection, *table_names: str) -> None:
    require_tables(connection, *table_names)


def save_excel(sheets: dict, filename: str) -> Path:
    output_path = OUTPUT_DIR / filename
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output_path


def read_output_csv(filename: str) -> pd.DataFrame:
    path = OUTPUT_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def project_facts(connection) -> dict:
    scale = connection.sql("""
        SELECT
            COUNT(*) AS behavior_count,
            COUNT(DISTINCT user_id) AS user_count,
            COUNT(DISTINCT content_id) AS content_count,
            MIN(event_date) AS first_date,
            MAX(event_date) AS last_date
        FROM behavior_fact
    """).df().iloc[0].to_dict()
    latest = connection.sql("""
        SELECT *
        FROM week2_daily_metrics
        ORDER BY date_day DESC
        LIMIT 1
    """).df().iloc[0].to_dict()
    top_content = connection.sql("""
        SELECT
            c.title,
            COUNT(DISTINCT b.user_id) AS active_users,
            COUNT(*) AS behavior_count,
            ROUND(AVG(b.rating), 2) AS avg_rating
        FROM behavior_fact b
        JOIN content_dim c ON b.content_id = c.content_id
        GROUP BY c.content_id, c.title
        HAVING COUNT(*) >= 100
        ORDER BY active_users DESC
        LIMIT 1
    """).df().iloc[0].to_dict()
    return {
        "scale": scale,
        "latest": latest,
        "top_content": top_content,
    }


def model_facts() -> dict:
    logistic = read_output_csv("ml_day16_logistic_metrics.csv")
    pytorch = read_output_csv("ml_day17_pytorch_metrics.csv")
    comparison = read_output_csv("ml_day18_model_comparison.csv")
    spark = read_output_csv("ml_day20_spark_status.csv")
    result = {}
    if not logistic.empty:
        result["logistic"] = logistic.iloc[0].to_dict()
    if not pytorch.empty:
        result["pytorch"] = pytorch.iloc[0].to_dict()
    if not comparison.empty:
        result["comparison"] = comparison.to_dict("records")
    if not spark.empty:
        result["spark"] = spark.iloc[0].to_dict()
    return result


def write_portfolio_file(filename: str, content: str) -> Path:
    PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)
    path = PORTFOLIO_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path
