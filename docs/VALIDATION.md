# Validation

## Validation objective

Validation must prove both sides of the main claim:

1. a clean source and target reconcile successfully;
2. a silent target mutation is detected as a failure.

A pipeline that only proves the happy path is insufficient.

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
  --seed 42
python -m banking_dataops.ingest
python -m banking_dataops.quality_checks
python -m banking_dataops.reconciliation
```

Expected reconciliation status: `PASS`.

## Failure injection

Change the target without changing the source:

```sql
UPDATE transactions
SET amount_chf = amount_chf + 1
WHERE transaction_id = (
    SELECT MIN(transaction_id)
    FROM transactions
);
```

Then run:

```bash
python -m banking_dataops.reconciliation
```

Expected behavior:

- reconciliation status = `FAIL`;
- `amount_delta` != 0;
- `amount_mismatch_count` >= 1;
- process exit code is non-zero.

## Recovery

```bash
python -m banking_dataops.ingest
python -m banking_dataops.quality_checks
python -m banking_dataops.reconciliation
```

Expected reconciliation status: `PASS`.

## CI

`.github/workflows/ci.yml` automates:

- install;
- compile;
- Ruff;
- pytest;
- deterministic source generation;
- PostgreSQL ingestion;
- data-quality controls;
- clean reconciliation;
- silent target mutation;
- expected reconciliation failure;
- source reload;
- successful reconciliation recovery.

## Boundary

This validates a synthetic technical case study. It does not certify production readiness, regulatory compliance or production-scale performance.
