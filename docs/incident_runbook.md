# Incident Runbook — Banking DataOps Monitoring

## Trigger conditions

An investigation is required when:

- a high-severity data-quality control fails;
- source-to-target reconciliation returns `FAIL`;
- the pipeline cannot ingest or query PostgreSQL;
- the dashboard cannot read persisted control evidence;
- CI detects a regression.

## First question

Determine whether the failure is:

1. **source quality** — the synthetic source itself violates a rule;
2. **ingestion** — source data did not reach the target correctly;
3. **target mutation** — target data changed after ingestion;
4. **runtime** — PostgreSQL/container/process failure;
5. **control logic** — the validation code or contract is wrong.

## Reconciliation triage

Inspect the latest result:

```sql
SELECT *
FROM reconciliation_results
ORDER BY executed_at DESC
LIMIT 5;
```

Interpretation:

| Signal | Likely direction |
|---|---|
| `count_delta < 0` | target is missing rows |
| `count_delta > 0` | target contains unexpected rows |
| `missing_in_target > 0` | source IDs did not reach target |
| `unexpected_in_target > 0` | target contains IDs absent from source |
| `amount_mismatch_count > 0` | shared IDs were materially altered |
| `amount_delta != 0` | source/target financial totals diverge |

## Quality triage

```sql
SELECT *
FROM quality_check_results
ORDER BY executed_at DESC, control_id;
```

Then rerun the control query associated with the failed ID.

## Recovery

Because the environment is synthetic and disposable:

```bash
make ingest
make quality
make reconcile
```

If the source itself is invalid:

```bash
make generate
make ingest
make quality
make reconcile
```

## Incident note

Record:

- failed control/reconciliation;
- observed evidence;
- source and target scope;
- root cause;
- corrective action;
- preventive control or test;
- final recovery evidence.

## Boundary

Do not copy real operational data into this repository or its incident notes.
