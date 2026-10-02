from decimal import Decimal
from pathlib import Path

from banking_dataops.reconciliation import (
    ReconciliationSnapshot,
    build_snapshot,
    compare_snapshots,
    load_source_snapshot,
)


def _record(
    transaction_id: str,
    amount: object = "10.00",
    channel: str = "web",
) -> dict[str, object]:
    return {
        "transaction_id": transaction_id,
        "account_id": "ACC-00001-01",
        "source_system": "core_banking",
        "event_timestamp": "2026-09-01T10:00:00+00:00",
        "booking_date": "2026-09-01",
        "amount_chf": amount,
        "currency": "CHF",
        "channel": channel,
        "merchant_category": "services",
        "country": "CH",
        "risk_score": "0.1200",
        "status": "posted",
        "is_suspicious": "False",
        "created_at": "2026-10-01T00:00:00+00:00",
    }


def _snapshot(records: list[dict[str, object]]) -> ReconciliationSnapshot:
    return build_snapshot(records)


def test_matching_snapshots_pass() -> None:
    source = _snapshot([_record("TX-1", "10.00"), _record("TX-2", "20.00")])
    target = _snapshot([_record("TX-1", Decimal("10.00")), _record("TX-2", Decimal("20.00"))])

    result = compare_snapshots(source, target)

    assert result.status == "PASS"
    assert result.count_delta == 0
    assert result.amount_delta == Decimal("0.00")
    assert result.missing_in_target == 0
    assert result.unexpected_in_target == 0
    assert result.amount_mismatch_count == 0
    assert result.row_mismatch_count == 0


def test_missing_target_transaction_fails() -> None:
    source = _snapshot([_record("TX-1"), _record("TX-2")])
    target = _snapshot([_record("TX-1")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.count_delta == -1
    assert result.missing_in_target == 1


def test_silent_amount_mutation_fails_even_when_id_exists() -> None:
    source = _snapshot([_record("TX-1", "10.00"), _record("TX-2", "20.00")])
    target = _snapshot([_record("TX-1", "11.00"), _record("TX-2", "20.00")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.amount_mismatch_count == 1
    assert result.row_mismatch_count == 1
    assert result.amount_delta == Decimal("1.00")


def test_non_financial_mutation_fails_with_unchanged_totals() -> None:
    source = _snapshot([_record("TX-1", "10.00", "web")])
    target = _snapshot([_record("TX-1", "10.00", "branch")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.amount_delta == Decimal("0.00")
    assert result.amount_mismatch_count == 0
    assert result.row_mismatch_count == 1


def test_unexpected_target_transaction_fails() -> None:
    source = _snapshot([_record("TX-1")])
    target = _snapshot([_record("TX-1"), _record("TX-X", "5.00")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.unexpected_in_target == 1


def test_duplicate_source_identifier_fails() -> None:
    source = _snapshot([_record("TX-1"), _record("TX-1")])
    target = _snapshot([_record("TX-1")])

    result = compare_snapshots(source, target)

    assert result.status == "FAIL"
    assert result.source_duplicate_ids == 1


def test_load_source_snapshot_reads_full_csv_controls(tmp_path: Path) -> None:
    path = tmp_path / "transactions.csv"
    path.write_text(
        "transaction_id,account_id,source_system,event_timestamp,booking_date,amount_chf,"
        "currency,channel,merchant_category,country,risk_score,status,is_suspicious,created_at\n"
        "TX-1,ACC-00001-01,core_banking,2026-09-01T10:00:00+00:00,2026-09-01,10.25,"
        "CHF,web,services,CH,0.1200,posted,False,2026-10-01T00:00:00+00:00\n"
        "TX-2,ACC-00001-01,core_banking,2026-09-01T11:00:00+00:00,2026-09-01,20.75,"
        "CHF,mobile,services,CH,0.2200,posted,False,2026-10-01T00:00:00+00:00\n",
        encoding="utf-8",
    )

    snapshot = load_source_snapshot(path)

    assert snapshot.row_count == 2
    assert snapshot.total_amount_chf == Decimal("31.00")
    assert snapshot.transaction_ids == frozenset({"TX-1", "TX-2"})
    assert len(snapshot.row_hash_by_id["TX-1"]) == 64
