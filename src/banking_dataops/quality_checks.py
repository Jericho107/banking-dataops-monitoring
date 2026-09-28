"""SQL-backed data-quality checks for the Banking DataOps Monitoring project."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from banking_dataops.config import Settings, load_settings
from banking_dataops.db import connect


@dataclass(frozen=True)
class QualityCheck:
    """A single SQL-backed data-quality check."""

    control_id: str
    check_name: str
    severity: str
    query: str
    warn_only: bool = False


@dataclass(frozen=True)
class QualityCheckResult:
    """Result of a single quality check."""

    control_id: str
    check_name: str
    status: str
    failed_rows: int
    severity: str
    executed_at: datetime


def status_from_failed_rows(failed_rows: int, warn_only: bool = False) -> str:
    """Return PASS/WARN/FAIL from failed-row count."""

    if failed_rows == 0:
        return "PASS"
    return "WARN" if warn_only else "FAIL"


def get_quality_checks() -> list[QualityCheck]:
    """Return configured quality checks."""

    return [
        QualityCheck(
            "CTRL-001",
            "critical_nulls",
            "high",
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE transaction_id IS NULL
               OR account_id IS NULL
               OR event_timestamp IS NULL
               OR amount_chf IS NULL
            """,
        ),
        QualityCheck(
            "CTRL-002",
            "duplicate_transactions",
            "high",
            """
            SELECT COUNT(*)
            FROM (
                SELECT transaction_id
                FROM transactions
                GROUP BY transaction_id
                HAVING COUNT(*) > 1
            ) duplicates
            """,
        ),
        QualityCheck(
            "CTRL-003",
            "invalid_amounts",
            "high",
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE amount_chf <= 0
               OR amount_chf > 1000000
            """,
        ),
        QualityCheck(
            "CTRL-004",
            "orphan_transactions",
            "high",
            """
            SELECT COUNT(*)
            FROM transactions t
            LEFT JOIN accounts a ON t.account_id = a.account_id
            WHERE a.account_id IS NULL
            """,
        ),
        QualityCheck(
            "CTRL-005",
            "invalid_risk_score",
            "medium",
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE risk_score < 0
               OR risk_score > 1
            """,
        ),
        QualityCheck(
            "CTRL-006",
            "invalid_status",
            "medium",
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE status NOT IN ('posted', 'pending', 'rejected')
            """,
        ),
        QualityCheck(
            "CTRL-007",
            "stale_data",
            "low",
            """
            SELECT CASE
                WHEN MAX(event_timestamp) < CURRENT_TIMESTAMP - INTERVAL '60 days'
                THEN 1
                ELSE 0
            END
            FROM transactions
            """,
            warn_only=True,
        ),
    ]


def run_quality_checks(settings: Settings | None = None) -> list[QualityCheckResult]:
    """Run all quality checks and persist latest results."""

    runtime = settings or load_settings()
    results: list[QualityCheckResult] = []
    executed_at = datetime.now(UTC)

    with connect(runtime) as connection:
        with connection.cursor() as cursor:
            for check in get_quality_checks():
                cursor.execute(check.query)
                failed_rows = int(cursor.fetchone()[0] or 0)
                result = QualityCheckResult(
                    control_id=check.control_id,
                    check_name=check.check_name,
                    status=status_from_failed_rows(failed_rows, check.warn_only),
                    failed_rows=failed_rows,
                    severity=check.severity,
                    executed_at=executed_at,
                )
                results.append(result)
                cursor.execute(
                    """
                    INSERT INTO quality_check_results
                        (check_id, control_id, check_name, status, failed_rows, severity, executed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (check_id)
                    DO UPDATE SET
                        control_id = EXCLUDED.control_id,
                        check_name = EXCLUDED.check_name,
                        status = EXCLUDED.status,
                        failed_rows = EXCLUDED.failed_rows,
                        severity = EXCLUDED.severity,
                        executed_at = EXCLUDED.executed_at
                    """,
                    (
                        check.control_id,
                        result.control_id,
                        result.check_name,
                        result.status,
                        result.failed_rows,
                        result.severity,
                        result.executed_at,
                    ),
                )

            failed = [result for result in results if result.status == "FAIL"]
            for result in failed:
                cursor.execute(
                    """
                    INSERT INTO incident_reports
                        (incident_id, title, severity, status, failed_control, summary, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (incident_id) DO NOTHING
                    """,
                    (
                        f"INC-{uuid4().hex[:12].upper()}",
                        f"Failed data control: {result.check_name}",
                        result.severity,
                        "open",
                        result.control_id,
                        f"{result.control_id} failed with {result.failed_rows} row(s).",
                        result.executed_at,
                    ),
                )

        connection.commit()

    return results


def has_blocking_failures(results: list[QualityCheckResult]) -> bool:
    """Return whether any quality control has failed."""

    return any(result.status == "FAIL" for result in results)


def print_quality_results(results: list[QualityCheckResult]) -> None:
    """Print a CLI-friendly quality summary."""

    for result in results:
        print(
            f"{result.control_id} | {result.status} | {result.severity} | "
            f"{result.check_name} | failed={result.failed_rows}"
        )


def main() -> None:
    """CLI entry point that fails closed when a control fails."""

    results = run_quality_checks()
    print_quality_results(results)
    if has_blocking_failures(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
