from pathlib import Path

import duckdb

from common import DB_PATH, OUTPUT_DIR, connect, require_tables


WEEK2_DB = DB_PATH


def connect_week2():
    """Open the shared Week 1/Week 2 DuckDB database."""
    return connect()


def require_week2_tables(connection, *table_names: str) -> None:
    require_tables(connection, *table_names)


def save_excel(sheets: dict, filename: str) -> Path:
    """Write a mapping of sheet names to DataFrames into days/."""
    output_path = OUTPUT_DIR / filename
    with __import__("pandas").ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, frame in sheets.items():
            frame.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output_path


def as_posix_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")
