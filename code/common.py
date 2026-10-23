from pathlib import Path

import duckdb


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "dataset" / "ml-25m"
OUTPUT_DIR = PROJECT_DIR / "days"
DB_PATH = PROJECT_DIR / "content_platform.duckdb"


def connect():
    """Open the shared DuckDB database used by all week-one scripts."""
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found: {DATA_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(DB_PATH))
    connection.execute("SET TimeZone='UTC'")
    return connection


def csv_sql_path(filename: str) -> str:
    """Return a CSV path safe to interpolate into a DuckDB SQL string."""
    path = (DATA_DIR / filename).resolve().as_posix()
    return path.replace("'", "''")


def require_tables(connection, *table_names: str) -> None:
    """Fail early with a useful message when an earlier day was skipped."""
    existing = {
        row[0]
        for row in connection.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'main'"
        ).fetchall()
    }
    missing = [name for name in table_names if name not in existing]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Missing table(s): {names}. Run code/day01_setup.py first."
        )
