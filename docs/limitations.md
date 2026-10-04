# Limitations

This repository demonstrates a synthetic transaction-control and reconciliation system.

- All customer, account and transaction records are synthetic.
- The implementation does not connect to a real core-banking, payment, fraud, sanctions or regulatory system.
- Full-row reconciliation validates governed transaction fields after canonical normalisation; it is not a regulatory certification or audit opinion.
- The workflow demonstrates deterministic integrity controls rather than production throughput, resilience or high-availability performance.
- Production alerting, enterprise observability, secrets management and incident integrations are outside scope.
- The recovery flow restores a synthetic source state and is not a bank disaster-recovery design.
- No realised operational saving, compliance outcome or risk reduction is claimed.
