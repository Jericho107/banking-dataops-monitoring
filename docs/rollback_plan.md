# Rollback and Recovery Plan

## Scope

This plan applies only to the local synthetic environment.

The project has no production rollback claim.

## Preferred recovery

The source CSV is reproducible when generated with the same seed and explicit anchor, and the PostgreSQL target is disposable. Recovery therefore means rebuilding the target from the source and re-running controls.

```bash
make ingest
make quality
make reconcile
```

Expected final state: reconciliation `PASS`.

## Full reset

When schema, volume or container state is uncertain:

```bash
make reset
```

The reset:

1. removes the local PostgreSQL volume;
2. starts PostgreSQL and waits for its health check;
3. regenerates seeded synthetic source data;
4. ingests the source;
5. runs quality controls;
6. runs source-to-target reconciliation.

## Recovery acceptance criteria

- PostgreSQL is healthy;
- ingestion completes;
- no high-severity quality control fails;
- reconciliation status is `PASS`;
- no missing, unexpected or amount-mismatched transaction remains.

## Boundary

A real production system would require versioned migrations, backup/restore strategy, change approval and recovery-point/recovery-time objectives. Those are outside this case study.
