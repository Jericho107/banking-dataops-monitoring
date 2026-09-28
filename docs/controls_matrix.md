# Controls Matrix

| ID | Control | Risk covered | Evidence | Severity | Execution |
|---|---|---|---|---|---|
| CTRL-001 | Critical fields not null | incomplete operational records | Python + SQL control | high | every quality run |
| CTRL-002 | Transaction ID uniqueness | duplicate processing | Python + SQL control | high | every quality run |
| CTRL-003 | Amount validity | impossible/out-of-policy values | Python + SQL control | high | every quality run |
| CTRL-004 | Referential integrity | orphan transactions | Python + SQL control | high | every quality run |
| CTRL-005 | Risk-score range | malformed analytical feature | Python + SQL control | medium | every quality run |
| CTRL-006 | Status validity | unexpected lifecycle state | Python + SQL control | medium | every quality run |
| CTRL-007 | Freshness | stale target data | Python + SQL control | low | every quality run |
| CTRL-008 | Source-to-target reconciliation | silent loss, insertion, duplication or amount mutation | `reconciliation.py` | high | every reconciliation run |
| CTRL-009 | Suspicious transaction visibility | hidden risk concentration in synthetic data | `monitoring.py` | medium | dashboard query |
| CTRL-010 | Public-data boundary | accidental publication of private data | repository policy + review | high | every public release |

## CTRL-008 acceptance criteria

The reconciliation control passes only when:

- count delta = 0;
- amount delta = 0.00;
- missing in target = 0;
- unexpected in target = 0;
- amount mismatch count = 0;
- source duplicate ID count = 0;
- target duplicate ID count = 0.

The CI reverse test mutates the target independently from the source and requires this control to fail.
