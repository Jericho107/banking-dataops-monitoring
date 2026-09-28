"""Seeded synthetic regulated-data generator.

The generated data is fake and safe for public GitHub. Supplying the same
seed and anchor timestamp produces byte-for-byte equivalent CSV content.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
import random


@dataclass(frozen=True)
class SyntheticConfig:
    """Synthetic data generation configuration."""

    customers: int = 100
    accounts_per_customer: int = 2
    transactions: int = 1500
    seed: int = 42
    anchor_time: datetime | None = None


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"No rows to write for {path}")

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _normalized_anchor(anchor_time: datetime | None) -> datetime:
    """Return an aware UTC anchor, defaulting to the current UTC time."""

    if anchor_time is None:
        return datetime.now(UTC)
    if anchor_time.tzinfo is None:
        raise ValueError("anchor_time must include timezone information")
    return anchor_time.astimezone(UTC)


def parse_anchor(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into an aware UTC datetime."""

    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise argparse.ArgumentTypeError("anchor must include a timezone offset or Z")
    return parsed.astimezone(UTC)


def generate(config: SyntheticConfig, output_dir: Path) -> None:
    """Generate synthetic customers, accounts and transactions CSV files."""

    rng = random.Random(config.seed)
    anchor = _normalized_anchor(config.anchor_time)

    customer_segments = ["retail", "premium", "sme"]
    countries = ["CH", "FR", "DE", "IT", "AT"]
    channels = ["web", "mobile", "branch", "api"]
    categories = ["grocery", "travel", "health", "utilities", "electronics", "services"]
    source_systems = ["core_banking", "card_processor", "payments_gateway"]

    customers: list[dict[str, object]] = []
    accounts: list[dict[str, object]] = []
    created_anchor = anchor - timedelta(days=120)

    for index in range(config.customers):
        customer_id = f"CUST-{index + 1:05d}"
        customer_created = created_anchor + timedelta(days=rng.randint(0, 90))
        customers.append(
            {
                "customer_id": customer_id,
                "customer_segment": rng.choice(customer_segments),
                "country": rng.choice(countries),
                "created_at": customer_created.isoformat(),
            }
        )

        for account_index in range(config.accounts_per_customer):
            accounts.append(
                {
                    "account_id": f"ACC-{index + 1:05d}-{account_index + 1:02d}",
                    "customer_id": customer_id,
                    "account_type": rng.choice(["current", "savings"]),
                    "currency": "CHF",
                    "opened_at": (
                        customer_created + timedelta(days=rng.randint(0, 20))
                    ).isoformat(),
                }
            )

    transactions: list[dict[str, object]] = []
    base_time = anchor - timedelta(days=30)

    for index in range(config.transactions):
        account = rng.choice(accounts)
        timestamp = base_time + timedelta(minutes=rng.randint(0, 30 * 24 * 60))
        amount = round(rng.lognormvariate(4.0, 0.8), 2)

        if index % 137 == 0:
            amount = round(rng.uniform(50000, 125000), 2)

        base_risk = rng.random() ** 2
        risk_score = round(min(0.9999, base_risk + (0.35 if amount > 50000 else 0)), 4)
        status = rng.choices(["posted", "pending", "rejected"], weights=[86, 9, 5])[0]

        transactions.append(
            {
                "transaction_id": f"TX-{index + 1:08d}",
                "account_id": account["account_id"],
                "source_system": rng.choice(source_systems),
                "event_timestamp": timestamp.isoformat(),
                "booking_date": timestamp.date().isoformat(),
                "amount_chf": amount,
                "currency": "CHF",
                "channel": rng.choice(channels),
                "merchant_category": rng.choice(categories),
                "country": rng.choice(countries),
                "risk_score": risk_score,
                "status": status,
                "is_suspicious": risk_score > 0.85,
                "created_at": anchor.isoformat(),
            }
        )

    _write_csv(output_dir / "synthetic_customers.csv", customers)
    _write_csv(output_dir / "synthetic_accounts.csv", accounts)
    _write_csv(output_dir / "synthetic_transactions.csv", transactions)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Generate synthetic regulated-data CSV files.")
    parser.add_argument("--output-dir", default="data")
    parser.add_argument("--customers", type=int, default=100)
    parser.add_argument("--accounts-per-customer", type=int, default=2)
    parser.add_argument("--transactions", type=int, default=1500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--anchor",
        type=parse_anchor,
        default=None,
        help="Optional ISO-8601 anchor. Same seed + anchor produces the same CSV content.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entry point."""

    args = parse_args()
    config = SyntheticConfig(
        customers=args.customers,
        accounts_per_customer=args.accounts_per_customer,
        transactions=args.transactions,
        seed=args.seed,
        anchor_time=args.anchor,
    )
    generate(config, Path(args.output_dir))
    print(
        "Generated synthetic data: "
        f"{config.customers} customers, "
        f"{config.customers * config.accounts_per_customer} accounts, "
        f"{config.transactions} transactions"
    )


if __name__ == "__main__":
    main()
