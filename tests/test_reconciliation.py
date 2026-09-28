from decimal import Decimal
from pathlib import Path

from banking_dataops.reconciliation import (
    ReconciliationSnapshot,
    build_snapshot,
    compare_snapshots,
    load_source_snapshot,
)


def _snapshot(records: list[tuple[str, object]]) -> ReconciliationSnapshot:
    return build_snapshot(records)


def test_matching_snapshots_pass() -> None:
    source = _snapshot([("TX-1", "10.00"), ("TX-2", "20.00")])
    target = _snapshot([("TX-1", Decimal("10.00")), ("TX-2", Decimal("20.00"))])

    result = compare_snapshots(source, target)

    assert result.status == "PASS"
    assert result.count_delta == 0
    assert result.amount_delta == Decimal("0.00")
    assert result.missing_in_target == 0
    assert result.unexpected_in_target == 0
    assert result.amount_mismatch_count == 0


def test_missing_target_transaction_fails() -> None:
    source = _snapshot([("TX-1", "10.00"), ("TX-2", "20.00")])
    target = _snapshot([("TX-1", "10.00")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.count_delta == -1
    assert result.missing_in_target == 1


def test_silent_amount_mutation_fails_even_when_id_exists() -> None:
    source = _snapshot([("TX-1", "10.00"), ("TX-2", "20.00")])
    target = _snapshot([("TX-1", "11.00"), ("TX-2", "20.00")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.amount_mismatch_count == 1
    assert result.amount_delta == Decimal("1.00")


def test_unexpected_target_transaction_fails() -> None:
    source = _snapshot([("TX-1", "10.00")])
    target = _snapshot([("TX-1", "10.00"), ("TX-X", "5.00")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.unexpected_in_target == 1


def test_duplicate_source_identifier_fails() -> None:
    source = _snapshot([("TX-1", "10.00"), ("TX-1", "10.00")])
    target = _snapshot([("TX-1", "10.00")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.source_duplicate_ids == 1


def test_load_source_snapshot_reads_csv_controls(tmp_path: Path) -> None:
    path = tmp_path / "transactions.csv"
    path.write_text(
        "transaction_id,amount_chf\nTX-1,10.25\nTX-2,20.75\n",
        encoding="utf-8",
    )

    snapshot = load_source_snapshot(path)

    assert snapshot.row_count == 2
    assert snapshot.total_amount_chf == Decimal("31.00")
    assert snapshot.transaction_ids == frozenset({"TX-1", "TX-2"})
