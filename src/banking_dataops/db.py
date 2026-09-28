"""Database helpers for PostgreSQL-backed DataOps workflows."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd
import psycopg
from psycopg.rows import dict_row

from banking_dataops.config import Settings, load_settings


def connect(settings: Settings | None = None) -> psycopg.Connection:
    """Open a PostgreSQL connection."""

    return psycopg.connect((settings or load_settings()).dsn)


def split_sql_statements(sql_text: str) -> list[str]:
    """Split simple SQL files into executable statements.

    This is intentionally minimal and sufficient for this repository's SQL files.
    It is not a general SQL parser.
    """

    return [statement.strip() for statement in sql_text.split(";") if statement.strip()]


def execute_sql_file(path: Path, settings: Settings | None = None) -> None:
    """Execute all statements from a SQL file inside one transaction."""

    statements = split_sql_statements(path.read_text(encoding="utf-8"))
    with connect(settings) as connection, connection.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)
        connection.commit()


def execute_sql_files(paths: Iterable[Path], settings: Settings | None = None) -> None:
    """Execute a sequence of SQL files."""

    for path in paths:
        execute_sql_file(path, settings=settings)


def fetch_dataframe(query: str, settings: Settings | None = None) -> pd.DataFrame:
    """Return a SQL query as a pandas DataFrame."""

    with connect(settings) as connection:
        return pd.read_sql_query(query, connection)


def fetch_rows(query: str, settings: Settings | None = None) -> list[dict[str, object]]:
    """Return SQL rows as dictionaries."""

    with (
        psycopg.connect((settings or load_settings()).dsn, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(query)
        return list(cursor.fetchall())


def execute_query(query: str, settings: Settings | None = None) -> None:
    """Execute one SQL query."""

    with connect(settings) as connection, connection.cursor() as cursor:
        cursor.execute(query)
        connection.commit()


def reset_tables(settings: Settings | None = None) -> None:
    """Truncate project tables in dependency-safe order."""

    query = """
    TRUNCATE TABLE
        incident_reports,
        reconciliation_results,
        quality_check_results,
        transactions,
        accounts,
        customers
    RESTART IDENTITY CASCADE
    """
    execute_query(query, settings=settings)
