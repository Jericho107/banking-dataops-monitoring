# Monitoring Plan

## Objective

Monitoring exposes whether the synthetic target is usable and whether it still matches its source.

## Monitored dimensions

| Dimension | Signal | Evidence |
|---|---|---|
| Data freshness | latest target event timestamp | quality control CTRL-007 |
| Quality status | PASS/WARN/FAIL by control | `quality_check_results` |
| Source/target integrity | reconciliation status | `reconciliation_results.status` |
| Count integrity | target minus source row delta | `count_delta` |
| Financial control total | target minus source amount delta | `amount_delta` |
| Transaction completeness | missing source IDs in target | `missing_in_target` |
| Unexpected target data | IDs not present in source | `unexpected_in_target` |
| Silent mutation | same ID with different amount | `amount_mismatch_count` |
| Synthetic risk visibility | suspicious transaction sample | dashboard query |

## Dashboard responsibilities

The Streamlit layer displays persisted evidence. It does not recalculate source/target reconciliation.

Current sections:

- data-quality status;
- latest control results;
- transaction volume;
- reconciliation evidence;
- transaction-status distribution;
- channel summary;
- suspicious/high-risk synthetic sample.

## Alert semantics

This public case study does not implement production paging or alert routing.

The key machine-readable signal is the reconciliation CLI exit code:

- `0` when reconciliation passes;
- non-zero when reconciliation fails.

That allows CI or a future orchestrator to stop downstream execution.

## Future production path

A production implementation would likely add:

- scheduled orchestration;
- structured logs;
- metrics export;
- alert routing;
- run IDs and lineage IDs;
- service-level objectives;
- retention policy for control evidence;
- OpenTelemetry or equivalent tracing.

Those capabilities are explicitly future scope rather than current claims.
