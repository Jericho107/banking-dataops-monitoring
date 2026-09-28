from datetime import UTC, datetime

from banking_dataops.quality_checks import (
    QualityCheckResult,
    get_quality_checks,
    has_blocking_failures,
    status_from_failed_rows,
)


def test_status_from_failed_rows() -> None:
    assert status_from_failed_rows(0) == "PASS"
    assert status_from_failed_rows(1) == "FAIL"
    assert status_from_failed_rows(1, warn_only=True) == "WARN"


def test_quality_checks_are_configured() -> None:
    checks = get_quality_checks()

    assert len(checks) >= 7
    assert len({check.control_id for check in checks}) == len(checks)

    for check in checks:
        assert check.control_id.startswith("CTRL-")
        assert check.check_name
        assert check.severity in {"high", "medium", "low"}
        assert "SELECT" in check.query.upper()


def test_blocking_failure_detection() -> None:
    now = datetime.now(UTC)
    passing = QualityCheckResult("CTRL-001", "nulls", "PASS", 0, "high", now)
    warning = QualityCheckResult("CTRL-007", "freshness", "WARN", 1, "low", now)
    failing = QualityCheckResult("CTRL-003", "amounts", "FAIL", 1, "high", now)

    assert not has_blocking_failures([passing, warning])
    assert has_blocking_failures([passing, failing])
