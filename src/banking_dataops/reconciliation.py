"""Source-to-target reconciliation for the synthetic transaction flow."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pandas as pd

from banking_dataops.config import Settings, load_settings
from banking_dataops.db import connect, fetch_dataframe

CENT = Decimal("0.01")


@dataclass(frozen=True)
class ReconciliationSnapshot:
    """Control totals and transaction-level evidence for one data state."""

    row_count: int
    total_amount_chf: Decimal
    transaction_ids: frozenset[str]
    duplicate_ids: frozenset[str]
    amount_by_id: dict[str, Decimal]


@dataclass(frozen=True)
class ReconciliationResult:
    """Comparison result between the source file and PostgreSQL target."""

    reconciliation_name: str
    source_count: int
    target_count: int
    count_delta: int
    source_total: Decimal
    target_total: Decimal
    amount_delta: Decimal
    missing_in_target: int
    unexpected_in_target: int
    amount_mismatch_count: int
    source_duplicate_ids: int
    target_duplicate_ids: int
    status: str


@dataclass(frozen=True)
class SourceSystemSummary:
    """Target-side operational summary by synthetic source system."""

    source_system: str
    transaction_count: int
    total_amount_chf: Decimal


SOURCE_SYSTEM_QUERY = """
SELECT
    source_system,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_chf), 2) AS total_amount_chf,
    MIN(event_timestamp) AS first_event_timestamp,
    MAX(event_timestamp) AS last_event_timestamp
FROM transactions
GROUP BY source_system
ORDER BY source_system
"""

DAILY_RECONCILIATION_QUERY = """
SELECT
    booking_date,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_chf), 2) AS total_amount_chf,
    COUNT(*) FILTER (WHERE is_suspicious) AS suspicious_count
FROM transactions
GROUP BY booking_date
ORDER BY booking_date
"""

CHANNEL_SUMMARY_QUERY = """
SELECT
    channel,
    COUNT(*) AS transaction_count,
    ROUND(AVG(risk_score), 4) AS avg_risk_score,
    COUNT(*) FILTER (WHERE status <> 'posted') AS non_posted_count
FROM transactions
GROUP BY channel
ORDER BY transaction_count DESC
"""

STATUS_SUMMARY_QUERY = """
SELECT
    status,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_chf), 2) AS total_amount_chf
FROM transactions
GROUP BY status
ORDER BY status
"""

SUSPICIOUS_SUMMARY_QUERY = """
SELECT
    is_suspicious,
    COUNT(*) AS transaction_count,
    ROUND(SUM(amount_chf), 2) AS total_amount_chf,
    ROUND(AVG(risk_score), 4) AS avg_risk_score
FROM transactions
GROUP BY is_suspicious
ORDER BY is_suspicious DESC
"""

TARGET_TRANSACTION_QUERY = """
SELECT transaction_id, amount_chf
FROM transactions
ORDER BY transaction_id
"""


def _amount(value: object) -> Decimal:
    """Normalize a numeric value to cents."""

    return Decimal(str(value)).quantize(CENT)


def build_snapshot(records: list[tuple[str, object]]) -> ReconciliationSnapshot:
    """Build deterministic control totals from transaction ID / amount records."""

    normalized = [(str(transaction_id), _amount(amount)) for transaction_id, amount in records]
    identifiers = [transaction_id for transaction_id, _ in normalized]
    counts = Counter(identifiers)
    duplicates = frozenset(
        transaction_id for transaction_id, count in counts.items() if count > 1
    )

    amount_by_id: dict[str, Decimal] = {}
    for transaction_id, amount in normalized:
        amount_by_id[transaction_id] = amount

    return ReconciliationSnapshot(
        row_count=len(normalized),
        total_amount_chf=sum((amount for _, amount in normalized), Decimal("0.00")),
        transaction_ids=frozenset(identifiers),
        duplicate_ids=duplicates,
        amount_by_id=amount_by_id,
    )


def load_source_snapshot(csv_path: Path) -> ReconciliationSnapshot:
    """Read source transaction controls directly from the generated CSV."""

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing source transaction file: {csv_path}")

    records: list[tuple[str, object]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            records.append((row["transaction_id"], row["amount_chf"]))

    return build_snapshot(records)


def load_target_snapshot(settings: Settings | None = None) -> ReconciliationSnapshot:
    """Read target transaction controls from PostgreSQL."""

    frame = fetch_dataframe(TARGET_TRANSACTION_QUERY, settings=settings)
    records = [
        (str(row["transaction_id"]), row["amount_chf"])
        for _, row in frame.iterrows()
    ]
    return build_snapshot(records)


def compare_snapshots(
    source: ReconciliationSnapshot,
    target: ReconciliationSnapshot,
) -> ReconciliationResult:
    """Compare source and target at aggregate and transaction-ID level."""

    missing = source.transaction_ids - target.transaction_ids
    unexpected = target.transaction_ids - source.transaction_ids
    shared = source.transaction_ids & target.transaction_ids
    amount_mismatches = sum(
        source.amount_by_id[transaction_id] != target.amount_by_id[transaction_id]
        for transaction_id in shared
    )

    count_delta = target.row_count - source.row_count
    amount_delta = (target.total_amount_chf - source.total_amount_chf).quantize(CENT)

    passed = all(
        [
            count_delta == 0,
            amount_delta == Decimal("0.00"),
            not missing,
            not unexpected,
            amount_mismatches == 0,
            not source.duplicate_ids,
            not target.duplicate_ids,
        ]
    )

    return ReconciliationResult(
        reconciliation_name="transactions_csv_to_postgresql",
        source_count=source.row_count,
        target_count=target.row_count,
        count_delta=count_delta,
        source_total=source.total_amount_chf,
        target_total=target.total_amount_chf,
        amount_delta=amount_delta,
        missing_in_target=len(missing),
        unexpected_in_target=len(unexpected),
        amount_mismatch_count=amount_mismatches,
        source_duplicate_ids=len(source.duplicate_ids),
        target_duplicate_ids=len(target.duplicate_ids),
        status="PASS" if passed else "FAIL",
    )


def source_system_summary(settings: Settings | None = None) -> list[SourceSystemSummary]:
    """Return target-side transaction counts and totals by source system."""

    frame = fetch_dataframe(SOURCE_SYSTEM_QUERY, settings=settings)
    return [
        SourceSystemSummary(
            source_system=str(row["source_system"]),
            transaction_count=int(row["transaction_count"]),
            total_amount_chf=_amount(row["total_amount_chf"]),
        )
        for _, row in frame.iterrows()
    ]


def persist_reconciliation(
    result: ReconciliationResult,
    settings: Settings | None = None,
) -> None:
    """Persist one source-to-target reconciliation result."""

    runtime = settings or load_settings()
    with connect(runtime) as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO reconciliation_results
                (
                    reconciliation_id,
                    reconciliation_name,
                    source_count,
                    target_count,
                    count_delta,
                    source_total,
                    target_total,
                    amount_delta,
                    missing_in_target,
                    unexpected_in_target,
                    amount_mismatch_count,
                    source_duplicate_ids,
                    target_duplicate_ids,
                    status
                )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                f"REC-{uuid4().hex[:12].upper()}",
                result.reconciliation_name,
                result.source_count,
                result.target_count,
                result.count_delta,
                result.source_total,
                result.target_total,
                result.amount_delta,
                result.missing_in_target,
                result.unexpected_in_target,
                result.amount_mismatch_count,
                result.source_duplicate_ids,
                result.target_duplicate_ids,
                result.status,
            ),
        )
        connection.commit()


def run_reconciliation(settings: Settings | None = None) -> dict[str, pd.DataFrame]:
    """Reconcile the source CSV against PostgreSQL and build supporting summaries."""

    runtime = settings or load_settings()
    source = load_source_snapshot(runtime.data_dir / "synthetic_transactions.csv")
    target = load_target_snapshot(runtime)
    result = compare_snapshots(source, target)
    persist_reconciliation(result, runtime)

    return {
        "reconciliation": pd.DataFrame([asdict(result)]),
        "source_system": fetch_dataframe(SOURCE_SYSTEM_QUERY, runtime),
        "daily": fetch_dataframe(DAILY_RECONCILIATION_QUERY, runtime),
        "channel": fetch_dataframe(CHANNEL_SUMMARY_QUERY, runtime),
        "status": fetch_dataframe(STATUS_SUMMARY_QUERY, runtime),
        "suspicious": fetch_dataframe(SUSPICIOUS_SUMMARY_QUERY, runtime),
    }


def print_reconciliation_summary(summary: dict[str, pd.DataFrame]) -> None:
    """Print a CLI-friendly reconciliation summary."""

    for name, frame in summary.items():
        print(f"\n## {name}")
        print(frame.to_string(index=False))


def main() -> None:
    """CLI entry point that fails closed when reconciliation fails."""

    summary = run_reconciliation()
    print_reconciliation_summary(summary)
    status = str(summary["reconciliation"].iloc[0]["status"])
    if status != "PASS":
        print("Source-to-target reconciliation failed.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
