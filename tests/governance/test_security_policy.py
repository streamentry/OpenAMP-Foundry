"""Tests for security_policy.py — Phase J J6."""
import pytest
from openamp_foundry.governance.security_policy import (
    VulnerabilityReport,
    SecurityReportValidationResult,
    VALID_SEVERITY_LEVELS,
    VALID_VULNERABILITY_CATEGORIES,
    validate_vulnerability_report,
    validate_report_dict,
)


def _valid_report(**overrides) -> VulnerabilityReport:
    defaults = dict(
        report_id="SEC-2026-001",
        severity="high",
        category="code_vulnerability",
        description="Path traversal via --output flag allows reading arbitrary files",
        affected_version="v0.7.3",
        reporter_handle="security-researcher",
        report_date="2026-07-09",
        status="acknowledged",
        dry_lab_only=True,
    )
    defaults.update(overrides)
    return VulnerabilityReport(**defaults)


def test_valid_report_passes():
    result = validate_vulnerability_report(_valid_report())
    assert result.passed
    assert result.errors == []


def test_report_id_not_starting_with_SEC_fails():
    result = validate_vulnerability_report(_valid_report(report_id="BUG-2026-001"))
    assert not result.passed
    assert any("SEC-" in e for e in result.errors)


def test_empty_report_id_fails():
    result = validate_vulnerability_report(_valid_report(report_id=""))
    assert not result.passed
    assert any("report_id" in e for e in result.errors)


def test_invalid_severity_fails():
    result = validate_vulnerability_report(_valid_report(severity="extreme"))
    assert not result.passed
    assert any("severity" in e for e in result.errors)


def test_invalid_category_fails():
    result = validate_vulnerability_report(_valid_report(category="phishing"))
    assert not result.passed
    assert any("category" in e for e in result.errors)


def test_empty_description_fails():
    result = validate_vulnerability_report(_valid_report(description=""))
    assert not result.passed
    assert any("description" in e for e in result.errors)


def test_empty_affected_version_fails():
    result = validate_vulnerability_report(_valid_report(affected_version=""))
    assert not result.passed
    assert any("affected_version" in e for e in result.errors)


def test_empty_reporter_handle_fails():
    result = validate_vulnerability_report(_valid_report(reporter_handle=""))
    assert not result.passed
    assert any("reporter_handle" in e for e in result.errors)


def test_invalid_date_format_fails():
    result = validate_vulnerability_report(_valid_report(report_date="09-07-2026"))
    assert not result.passed
    assert any("report_date" in e for e in result.errors)


def test_invalid_status_fails():
    result = validate_vulnerability_report(_valid_report(status="wontfix"))
    assert not result.passed
    assert any("status" in e for e in result.errors)


def test_dry_lab_only_false_fails():
    result = validate_vulnerability_report(_valid_report(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


def test_critical_severity_received_produces_warning():
    result = validate_vulnerability_report(_valid_report(severity="critical", status="received"))
    assert result.passed
    assert any("critical" in w for w in result.warnings)


def test_safety_guardrail_bypass_produces_warning():
    result = validate_vulnerability_report(_valid_report(category="safety_guardrail_bypass"))
    assert result.passed
    assert any("safety guardrail" in w for w in result.warnings)


def test_validate_report_dict_passes_with_valid_dict():
    d = dict(
        report_id="SEC-2026-001",
        severity="medium",
        category="dependency_vulnerability",
        description="CVE-2026-1234 in requests library",
        affected_version="v0.7.3",
        reporter_handle="anonymous",
        report_date="2026-07-09",
        status="under_review",
    )
    result = validate_report_dict(d)
    assert result.passed
    assert result.dry_lab_only is True


def test_validate_report_dict_fails_with_missing_fields():
    result = validate_report_dict({"report_id": "SEC-2026-001"})
    assert not result.passed
    assert any("Missing" in e for e in result.errors)


def test_all_results_have_dry_lab_only_true():
    result = validate_vulnerability_report(_valid_report())
    assert result.dry_lab_only is True
    result2 = validate_vulnerability_report(_valid_report(dry_lab_only=False))
    assert result2.dry_lab_only is True


def test_valid_severity_levels_has_4_entries():
    assert len(VALID_SEVERITY_LEVELS) == 4
    assert "critical" in VALID_SEVERITY_LEVELS
    assert "high" in VALID_SEVERITY_LEVELS
    assert "medium" in VALID_SEVERITY_LEVELS
    assert "low" in VALID_SEVERITY_LEVELS


def test_valid_vulnerability_categories_has_5_entries():
    assert len(VALID_VULNERABILITY_CATEGORIES) == 5
    assert "code_vulnerability" in VALID_VULNERABILITY_CATEGORIES
    assert "secret_leakage" in VALID_VULNERABILITY_CATEGORIES
    assert "dependency_vulnerability" in VALID_VULNERABILITY_CATEGORIES
    assert "safety_guardrail_bypass" in VALID_VULNERABILITY_CATEGORIES
    assert "dual_use_risk" in VALID_VULNERABILITY_CATEGORIES
