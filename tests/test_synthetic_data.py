from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from banking_dataops.generate_synthetic_data import SyntheticConfig, generate

FIXED_ANCHOR = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def test_generate_synthetic_data_files(tmp_path: Path) -> None:
    generate(
        SyntheticConfig(
            customers=3,
            accounts_per_customer=2,
            transactions=25,
            anchor_time=FIXED_ANCHOR,
        ),
        tmp_path,
    )

    customers = tmp_path / "synthetic_customers.csv"
    accounts = tmp_path / "synthetic_accounts.csv"
    transactions = tmp_path / "synthetic_transactions.csv"

    assert customers.exists()
    assert accounts.exists()
    assert transactions.exists()

    assert len(pd.read_csv(customers)) == 3
    assert len(pd.read_csv(accounts)) == 6
    frame = pd.read_csv(transactions)
    assert len(frame) == 25

    expected_columns = {
        "transaction_id",
        "account_id",
        "source_system",
        "event_timestamp",
        "booking_date",
        "amount_chf",
        "currency",
        "channel",
        "merchant_category",
        "country",
        "risk_score",
        "status",
        "is_suspicious",
        "created_at",
    }
    assert expected_columns.issubset(frame.columns)
    assert set(frame["status"]).issubset({"posted", "pending", "rejected"})


def test_same_seed_and_anchor_produce_identical_source_files(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    config = SyntheticConfig(
        customers=4,
        accounts_per_customer=2,
        transactions=40,
        seed=7,
        anchor_time=FIXED_ANCHOR,
    )
    generate(config, first)
    generate(config, second)

    for filename in [
        "synthetic_customers.csv",
        "synthetic_accounts.csv",
        "synthetic_transactions.csv",
    ]:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()
