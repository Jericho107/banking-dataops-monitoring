"""Streamlit dashboard for Banking DataOps Monitoring."""

from __future__ import annotations

import sys
from pathlib import Path

import psycopg
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from banking_dataops.monitoring import (
    load_channel_summary,
    load_latest_quality_results,
    load_reconciliation_summary,
    load_status_summary,
    load_suspicious_transactions,
    load_transaction_volume,
    summarize_quality_status,
)

st.set_page_config(page_title="Banking DataOps Monitoring", layout="wide")

st.title("Banking DataOps Monitoring")
st.caption("Synthetic regulated-data monitoring dashboard — public technical evidence only")
st.info("Synthetic data only. Do not load real banking, insurance, health, client or employer data.")

try:
    quality = load_latest_quality_results()
    reconciliation = load_reconciliation_summary()
    volume = load_transaction_volume()
    status = load_status_summary()
    channel = load_channel_summary()
    suspicious = load_suspicious_transactions()
except psycopg.Error as exc:  # pragma: no cover - dashboard runtime path
    st.error("Database is not ready or schema is missing.")
    st.markdown(
        """
        Run the local setup first:

        ```bash
        make up
        make generate
        make ingest
        make quality
        make reconcile
        ```
        """
    )
    st.code(str(exc))
    st.stop()

st.subheader("Data quality status")
if quality.empty:
    st.warning("No quality checks have been executed yet. Run `make quality`.")
else:
    summary = summarize_quality_status(quality["status"].tolist())
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Checks", summary.total_checks)
    col2.metric("Passed", summary.passed_checks)
    col3.metric("Warnings", summary.warning_checks)
    col4.metric("Failed", summary.failed_checks)
    st.dataframe(quality, use_container_width=True)

st.subheader("Transaction volume by booking date")
if not volume.empty:
    st.line_chart(volume.set_index("booking_date")["transaction_count"])
    st.dataframe(volume, use_container_width=True)

st.subheader("Source-to-target integrity")
if reconciliation.empty:
    st.warning("No reconciliation results found. Run `make reconcile`.")
else:
    latest = reconciliation.iloc[0]
    integrity_issues = (
        int(latest["missing_in_target"])
        + int(latest["unexpected_in_target"])
        + int(latest["amount_mismatch_count"])
    )
    rec1, rec2, rec3, rec4 = st.columns(4)
    rec1.metric("Reconciliation", str(latest["status"]))
    rec2.metric("Count delta", int(latest["count_delta"]))
    rec3.metric("Amount delta (CHF)", f'{float(latest["amount_delta"]):,.2f}')
    rec4.metric("Transaction issues", integrity_issues)
    st.dataframe(reconciliation, use_container_width=True)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Status distribution")
    st.dataframe(status, use_container_width=True)
with col_b:
    st.subheader("Channel summary")
    st.dataframe(channel, use_container_width=True)

st.subheader("Suspicious / high-risk transaction sample")
st.dataframe(suspicious, use_container_width=True)

st.subheader("Operational notes")
st.code("make generate && make up && make ingest && make quality && make reconcile && make dashboard")
