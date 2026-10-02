# Validation

## Validation objective

Validation must prove all three states:

1. clean source and target reconcile successfully;
2. silent non-financial target drift is detected even when row counts and financial totals remain unchanged;
3. silent amount mutation is detected.

A pipeline that proves only the happy path is insufficient.

## Static checks

```bash
python -m compileall -q src tests dashboard
ruff check .
pytest -q
```

## Clean DataOps flow

```bash
docker compose up -d
python -m banking_dataops.generate_synthetic_data \
  --output-dir data \
  --customers 25 \
  --transactions 300 \
  --seed 42 \
  --anchor 2026-09-01T00:00:00+00:00
python -m banking_dataops.ingest
python -m banking_dataops.quality_checks
python -m banking_dataops.reconciliation
```

Expected status: `PASS`, including `row_mismatch_count = 0`.

## Reverse test A — non-financial drift

Change the target without changing the source or amount:

```sql
UPDATE transactions
SET channel = CASE WHEN channel = 'web' THEN 'branch' ELSE 'web' END
WHERE transaction_id = (
    SELECT MIN(transaction_id)
    FROM transactions
);
```

Expected behavior:

- reconciliation status = `FAIL`;
- `amount_delta = 0`;
- `amount_mismatch_count = 0`;
- `row_mismatch_count >= 1`;
- process exit code is non-zero.

## Reverse test B — financial drift

```sql
UPDATE transactions
SET amount_chf = amount_chf + 1
WHERE transaction_id = (
    SELECT MIN(transaction_id)
    FROM transactions
);
```

Expected behavior:

- reconciliation status = `FAIL`;
- `amount_delta != 0`;
- `amount_mismatch_count >= 1`;
- `row_mismatch_count >= 1`;
- process exit code is non-zero.

## Recovery

After either failure:

```bash
python -m banking_dataops.ingest
python -m banking_dataops.quality_checks
python -m banking_dataops.reconciliation
```

Expected status: `PASS`.

## CI

`.github/workflows/ci.yml` automates:

- install;
- compile;
- Ruff;
- pytest;
- deterministic seeded source generation;
- PostgreSQL ingestion;
- data-quality controls;
- clean full-row reconciliation;
- non-financial mutation and expected failure;
- recovery;
- financial mutation and expected failure;
- final recovery;
- persisted evidence verification.

## Boundary

This validates a synthetic technical case study. It does not certify production readiness, regulatory compliance or production-scale performance.
