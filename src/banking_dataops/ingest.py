"""Load synthetic CSV datasets into PostgreSQL."""

from __future__ import annotations

import csv
from pathlib import Path

from banking_dataops.config import Settings, load_settings
from banking_dataops.db import connect, execute_sql_file, reset_tables

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"


def create_schema(settings: Settings | None = None) -> None:
    """Create target database schema."""

    execute_sql_file(SQL_DIR / "00_schema.sql", settings=settings)


def _load_csv(table_name: str, csv_path: Path, settings: Settings | None = None) -> int:
    """Load a CSV file using PostgreSQL COPY and return loaded row count."""

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        row_count = sum(1 for _ in csv.DictReader(file))

    with (
        connect(settings) as connection,
        connection.cursor() as cursor,
        csv_path.open("r", encoding="utf-8") as file,
        cursor.copy(f"COPY {table_name} FROM STDIN WITH CSV HEADER") as copy,
    ):
        for line in file:
            copy.write(line)

    return row_count


def load_customers(data_dir: Path, settings: Settings | None = None) -> int:
    """Load synthetic customers."""

    return _load_csv("customers", data_dir / "synthetic_customers.csv", settings=settings)


def load_accounts(data_dir: Path, settings: Settings | None = None) -> int:
    """Load synthetic accounts."""

    return _load_csv("accounts", data_dir / "synthetic_accounts.csv", settings=settings)


def load_transactions(data_dir: Path, settings: Settings | None = None) -> int:
    """Load synthetic transactions."""

    return _load_csv("transactions", data_dir / "synthetic_transactions.csv", settings=settings)


def ingest_all(settings: Settings | None = None) -> dict[str, int]:
    """Create schema, reset tables and load all synthetic datasets."""

    runtime = settings or load_settings()
    data_dir = runtime.data_dir

    create_schema(runtime)
    reset_tables(runtime)

    return {
        "customers": load_customers(data_dir, runtime),
        "accounts": load_accounts(data_dir, runtime),
        "transactions": load_transactions(data_dir, runtime),
    }


def print_ingestion_summary(loaded: dict[str, int]) -> None:
    """Print loaded row counts."""

    for table_name, row_count in loaded.items():
        print(f"{table_name}: loaded={row_count}")


def main() -> None:
    """CLI entry point."""

    print_ingestion_summary(ingest_all())


if __name__ == "__main__":
    main()
