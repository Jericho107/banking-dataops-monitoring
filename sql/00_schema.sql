CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_segment TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    account_type TEXT NOT NULL,
    currency TEXT NOT NULL,
    opened_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id),
    source_system TEXT NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    booking_date DATE NOT NULL,
    amount_chf NUMERIC(18, 2) NOT NULL,
    currency TEXT NOT NULL,
    channel TEXT NOT NULL,
    merchant_category TEXT NOT NULL,
    country TEXT NOT NULL,
    risk_score NUMERIC(5, 4) NOT NULL,
    status TEXT NOT NULL,
    is_suspicious BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS quality_check_results (
    check_id TEXT PRIMARY KEY,
    control_id TEXT NOT NULL,
    check_name TEXT NOT NULL,
    status TEXT NOT NULL,
    failed_rows INTEGER NOT NULL,
    severity TEXT NOT NULL,
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reconciliation_results (
    reconciliation_id TEXT PRIMARY KEY,
    reconciliation_name TEXT NOT NULL,
    source_count INTEGER,
    target_count INTEGER,
    count_delta INTEGER,
    source_total NUMERIC(18,2),
    target_total NUMERIC(18,2),
    amount_delta NUMERIC(18,2),
    missing_in_target INTEGER NOT NULL DEFAULT 0,
    unexpected_in_target INTEGER NOT NULL DEFAULT 0,
    amount_mismatch_count INTEGER NOT NULL DEFAULT 0,
    row_mismatch_count INTEGER NOT NULL DEFAULT 0,
    source_duplicate_ids INTEGER NOT NULL DEFAULT 0,
    target_duplicate_ids INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'PASS',
    executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE reconciliation_results
    ADD COLUMN IF NOT EXISTS missing_in_target INTEGER NOT NULL DEFAULT 0;
ALTER TABLE reconciliation_results
    ADD COLUMN IF NOT EXISTS unexpected_in_target INTEGER NOT NULL DEFAULT 0;
ALTER TABLE reconciliation_results
    ADD COLUMN IF NOT EXISTS amount_mismatch_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE reconciliation_results
    ADD COLUMN IF NOT EXISTS row_mismatch_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE reconciliation_results
    ADD COLUMN IF NOT EXISTS source_duplicate_ids INTEGER NOT NULL DEFAULT 0;
ALTER TABLE reconciliation_results
    ADD COLUMN IF NOT EXISTS target_duplicate_ids INTEGER NOT NULL DEFAULT 0;
ALTER TABLE reconciliation_results
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'PASS';

CREATE TABLE IF NOT EXISTS incident_reports (
    incident_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    failed_control TEXT,
    summary TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_source_system ON transactions(source_system);
CREATE INDEX IF NOT EXISTS idx_transactions_booking_date ON transactions(booking_date);
CREATE INDEX IF NOT EXISTS idx_transactions_channel ON transactions(channel);
CREATE INDEX IF NOT EXISTS idx_transactions_is_suspicious ON transactions(is_suspicious);
CREATE INDEX IF NOT EXISTS idx_transactions_event_timestamp ON transactions(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
