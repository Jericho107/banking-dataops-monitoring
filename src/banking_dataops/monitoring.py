"""Monitoring helpers for dashboard and operational summaries."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from banking_dataops.config import Settings
from banking_dataops.db import fetch_dataframe


@dataclass(frozen=True)
class QualitySummary:
    """Aggregated quality status for dashboard and CLI output."""

    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int = 0

    @property
    def overall_status(self) -> str:
        """Return PASS if no checks failed, WARN if only warnings, otherwise FAIL."""

        if self.failed_checks > 0:
            return "FAIL"
        if self.warning_checks > 0:
            return "WARN"
        return "PASS"


def summarize_quality_status(statuses: list[str]) -> QualitySummary:
    """Summarize PASS/WARN/FAIL statuses."""

    normalized = [status.upper() for status in statuses]
    return QualitySummary(
        total_checks=len(normalized),
        passed_checks=normalized.count("PASS"),
        failed_checks=normalized.count("FAIL"),
        warning_checks=normalized.count("WARN"),
    )


def load_latest_quality_results(settings: Settings | None = None) -> pd.DataFrame:
    """Load latest persisted quality results."""

    return fetch_dataframe(
        """
        SELECT control_id, check_name, status, failed_rows, severity, executed_at
        FROM quality_check_results
        ORDER BY control_id
        """,
        settings=settings,
    )


def load_reconciliation_summary(settings: Settings | None = None) -> pd.DataFrame:
    """Load latest source-to-target reconciliation result rows."""

    return fetch_dataframe(
        """
        SELECT
            reconciliation_name,
            status,
            source_count,
            target_count,
            count_delta,
            source_total,
            target_total,
            amount_delta,
            missing_in_target,
            unexpected_in_target,
            amount_mismatch_count,
            source_duplicate_ids,
            target_duplicate_ids,
            executed_at
        FROM reconciliation_results
        ORDER BY executed_at DESC
        LIMIT 20
        """,
        settings=settings,
    )


def load_transaction_volume(settings: Settings | None = None) -> pd.DataFrame:
    """Load daily transaction volume and amounts."""

    return fetch_dataframe(
        """
        SELECT
            booking_date,
            COUNT(*) AS transaction_count,
            ROUND(SUM(amount_chf), 2) AS total_amount_chf
        FROM transactions
        GROUP BY booking_date
        ORDER BY booking_date
        """,
        settings=settings,
    )


def load_status_summary(settings: Settings | None = None) -> pd.DataFrame:
    """Load transaction status distribution."""

    return fetch_dataframe(
        """
        SELECT
            status,
            COUNT(*) AS transaction_count,
            ROUND(SUM(amount_chf), 2) AS total_amount_chf
        FROM transactions
        GROUP BY status
        ORDER BY status
        """,
        settings=settings,
    )


def load_channel_summary(settings: Settings | None = None) -> pd.DataFrame:
    """Load transaction channel summary."""

    return fetch_dataframe(
        """
        SELECT
            channel,
            COUNT(*) AS transaction_count,
            ROUND(AVG(risk_score), 4) AS avg_risk_score
        FROM transactions
        GROUP BY channel
        ORDER BY transaction_count DESC
        """,
        settings=settings,
    )


def load_suspicious_transactions(
    limit: int = 50,
    settings: Settings | None = None,
) -> pd.DataFrame:
    """Load suspicious transactions sample."""

    return fetch_dataframe(
        f"""
        SELECT
            transaction_id,
            account_id,
            event_timestamp,
            amount_chf,
            channel,
            country,
            risk_score,
            status,
            is_suspicious
        FROM transactions
        WHERE is_suspicious
        ORDER BY risk_score DESC, event_timestamp DESC
        LIMIT {int(limit)}
        """,
        settings=settings,
    )
