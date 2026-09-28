# Technical Case Study — Banking DataOps Monitoring

## Control problem

A target data store can look healthy while silently diverging from its source.

A simple row-count dashboard is insufficient if:

- a transaction disappears;
- an unexpected transaction appears;
- an amount changes after ingestion;
- duplicates enter the source;
- aggregate totals happen to hide transaction-level differences.

This case study implements a compact control system that treats the source CSV and PostgreSQL target as distinct states and makes divergence observable.

## Decision

The operational decision is binary:

> **Is the target state trustworthy enough to continue downstream processing?**

The reconciliation command therefore fails closed when the contract is broken.

## Control contract

The target must match the source on:

- row count;
- total amount;
- transaction-ID membership;
- per-transaction amount;
- duplicate-ID absence.

## Technical implementation

```text
deterministic synthetic generator
        ↓
CSV source
        ↓
PostgreSQL ingestion
        ↓
quality controls
        +
source/target reconciliation
        ↓
persisted evidence
        ↓
Streamlit monitoring
        ↓
CI reverse test
```

## Reverse test

The CI workflow deliberately changes one target transaction by CHF 1.00 while leaving the source untouched.

The repository is considered correct only if:

1. clean reconciliation passes;
2. mutated target reconciliation fails;
3. source reload restores a passing state.

This converts the core claim from documentation into executable evidence.

## What this demonstrates

- relational modelling;
- deterministic test-data generation;
- PostgreSQL ingestion;
- SQL and Python control design;
- source-to-target reconciliation;
- transaction-level failure detection;
- persisted operational evidence;
- testing and CI;
- operational runbook thinking.

## What it does not claim

- bank-grade infrastructure;
- regulatory certification;
- production scale;
- real banking integrations;
- real fraud or credit decisioning;
- production observability.

## Evidence

See [docs/proof_matrix.md](docs/proof_matrix.md) for the claim-by-claim mapping.
