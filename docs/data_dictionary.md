# Data Dictionary — Banking DataOps Monitoring

## customers

| Column | Type | Description | Quality rule |
|---|---|---|---|
| customer_id | TEXT | synthetic customer identifier | required, unique |
| customer_segment | TEXT | retail, premium or sme | required |
| country | TEXT | synthetic domicile country | required |
| created_at | TIMESTAMP | synthetic creation timestamp | required |

## accounts

| Column | Type | Description | Quality rule |
|---|---|---|---|
| account_id | TEXT | synthetic account identifier | required, unique |
| customer_id | TEXT | related synthetic customer | required, FK to customers |
| account_type | TEXT | current or savings | required |
| currency | TEXT | account currency | required |
| opened_at | TIMESTAMP | synthetic opening timestamp | required |

## transactions

| Column | Type | Description | Quality rule |
|---|---|---|---|
| transaction_id | TEXT | synthetic transaction identifier | required, unique |
| account_id | TEXT | related synthetic account | required, FK to accounts |
| source_system | TEXT | synthetic source feed | required |
| event_timestamp | TIMESTAMP | transaction event time | required |
| booking_date | DATE | booking date | required |
| amount_chf | NUMERIC(18,2) | synthetic CHF amount | > 0 and <= 1,000,000 |
| currency | TEXT | transaction currency | required |
| channel | TEXT | synthetic channel | required |
| merchant_category | TEXT | synthetic merchant category | required |
| country | TEXT | synthetic transaction country | required |
| risk_score | NUMERIC(5,4) | synthetic risk score | 0–1 |
| status | TEXT | posted, pending or rejected | controlled domain |
| is_suspicious | BOOLEAN | synthetic anomaly flag | required |
| created_at | TIMESTAMP | generated load timestamp | required |

## quality_check_results

| Column | Type | Description |
|---|---|---|
| check_id | TEXT | persisted control-result identifier |
| control_id | TEXT | documented control ID |
| check_name | TEXT | control name |
| status | TEXT | PASS, WARN or FAIL |
| failed_rows | INTEGER | number of failing rows |
| severity | TEXT | high, medium or low |
| executed_at | TIMESTAMP | execution timestamp |

## reconciliation_results

| Column | Type | Description |
|---|---|---|
| reconciliation_id | TEXT | unique reconciliation-run identifier |
| reconciliation_name | TEXT | reconciliation contract name |
| source_count | INTEGER | source CSV row count |
| target_count | INTEGER | PostgreSQL target row count |
| count_delta | INTEGER | target count minus source count |
| source_total | NUMERIC(18,2) | source amount total |
| target_total | NUMERIC(18,2) | target amount total |
| amount_delta | NUMERIC(18,2) | target total minus source total |
| missing_in_target | INTEGER | source IDs absent from target |
| unexpected_in_target | INTEGER | target IDs absent from source |
| amount_mismatch_count | INTEGER | shared IDs with different amounts |
| source_duplicate_ids | INTEGER | duplicated IDs detected in source snapshot |
| target_duplicate_ids | INTEGER | duplicated IDs detected in target snapshot |
| status | TEXT | PASS or FAIL |
| executed_at | TIMESTAMP | execution timestamp |

## incident_reports

| Column | Type | Description |
|---|---|---|
| incident_id | TEXT | generated incident identifier |
| title | TEXT | incident title |
| severity | TEXT | severity classification |
| status | TEXT | incident lifecycle status |
| failed_control | TEXT | related control ID |
| summary | TEXT | synthetic incident summary |
| created_at | TIMESTAMP | creation timestamp |

## Data boundary

Every dataset in this repository is synthetic. Reproducing the project does not require real banking, customer, employer or client information.
