from pathlib import Path

import duckdb
import pandas as pd

from common import DATA_DIR, DB_PATH, OUTPUT_DIR


def quote_identifier(identifier: str) -> str:
    """Quote a DuckDB identifier safely for a generated COUNT query."""
    return '"' + identifier.replace('"', '""') + '"'


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB database not found: {DB_PATH}")
    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Dataset directory not found: {DATA_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        tables = connection.sql("""
            SELECT
                table_schema,
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name
        """).df()

        columns = connection.sql("""
            SELECT
                table_schema,
                table_name,
                ordinal_position,
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name, ordinal_position
        """).df()

        row_counts = []
        for row in tables.itertuples(index=False):
            if row.table_schema != "main":
                continue
            table_identifier = quote_identifier(row.table_name)
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table_identifier}"
            ).fetchone()[0]
            row_counts.append(
                {
                    "table_schema": row.table_schema,
                    "table_name": row.table_name,
                    "table_type": row.table_type,
                    "row_count": count,
                }
            )
        table_summary = pd.DataFrame(row_counts)

        raw_files = []
        for csv_path in sorted(DATA_DIR.glob("*.csv")):
            header = connection.execute(
                f"DESCRIBE SELECT * FROM read_csv_auto('{csv_path.as_posix()}')"
            ).fetchall()
            for position, item in enumerate(header, start=1):
                raw_files.append(
                    {
                        "file_name": csv_path.name,
                        "ordinal_position": position,
                        "column_name": item[0],
                        "data_type": item[1],
                    }
                )
        raw_columns = pd.DataFrame(raw_files)

        output = OUTPUT_DIR / "ml_all_tables_and_columns.xlsx"
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            table_summary.to_excel(writer, sheet_name="db_tables", index=False)
            columns.to_excel(writer, sheet_name="db_columns", index=False)
            raw_columns.to_excel(writer, sheet_name="csv_columns", index=False)

            for table_name in tables["table_name"]:
                table_columns = columns[
                    columns["table_name"] == table_name
                ].copy()
                sheet_name = "t_" + "".join(
                    character
                    for character in str(table_name)
                    if character.isalnum() or character == "_"
                )
                table_columns.to_excel(
                    writer,
                    sheet_name=sheet_name[:31] or "table_columns",
                    index=False,
                )

        print("=== DuckDB tables ===")
        print(table_summary.to_string(index=False))
        print("\n=== DuckDB columns ===")
        print(columns.to_string(index=False))
        print("\n=== Raw CSV columns ===")
        print(raw_columns.to_string(index=False))
        print(f"\nSaved: {output}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
