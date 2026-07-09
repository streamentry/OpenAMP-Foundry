"""Security policy validator — validates security vulnerability reports.

Ensures all required fields are present before a vulnerability report
enters the formal review queue.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_SEVERITY_LEVELS: set[str] = {
    "critical", "high", "medium", "low"
}

VALID_REPORT_STATUSES: set[str] = {
    "received", "acknowledged", "under_review", "patched", "disclosed", "not_applicable"
}

VALID_VULNERABILITY_CATEGORIES: set[str] = {
    "code_vulnerability", "secret_leakage", "dependency_vulnerability",
    "safety_guardrail_bypass", "dual_use_risk"
}


@dataclass
class VulnerabilityReport:
    report_id: str              # e.g. "SEC-2026-001"
    severity: str               # from VALID_SEVERITY_LEVELS
    category: str               # from VALID_VULNERABILITY_CATEGORIES
    description: str            # must not be empty
    affected_version: str       # must not be empty
    reporter_handle: str        # GitHub handle or "anonymous"
    report_date: str            # YYYY-MM-DD
    status: str                 # from VALID_REPORT_STATUSES
    dry_lab_only: bool = True


@dataclass
class SecurityReportValidationResult:
    report_id: str
    severity: str
    passed: bool
    errors: list
    warnings: list
    dry_lab_only: bool = True


def validate_vulnerability_report(r: VulnerabilityReport) -> SecurityReportValidationResult:
    errors: list = []
    warnings: list = []

    if not r.report_id or not r.report_id.startswith("SEC-"):
        errors.append("report_id must not be empty and must start with 'SEC-'")
    if r.severity not in VALID_SEVERITY_LEVELS:
        errors.append(f"severity={r.severity!r} not in {sorted(VALID_SEVERITY_LEVELS)}")
    if r.category not in VALID_VULNERABILITY_CATEGORIES:
        errors.append(f"category={r.category!r} not in {sorted(VALID_VULNERABILITY_CATEGORIES)}")
    if not r.description:
        errors.append("description must not be empty")
    if not r.affected_version:
        errors.append("affected_version must not be empty")
    if not r.reporter_handle:
        errors.append("reporter_handle must not be empty")
    if not r.report_date or len(r.report_date) != 10 or r.report_date[4] != "-":
        errors.append("report_date must be in YYYY-MM-DD format")
    if r.status not in VALID_REPORT_STATUSES:
        errors.append(f"status={r.status!r} not in {sorted(VALID_REPORT_STATUSES)}")
    if not r.dry_lab_only:
        errors.append("dry_lab_only must be True")

    if r.severity == "critical" and r.status == "received":
        warnings.append("critical severity report is still 'received' — acknowledge within 48 hours")
    if r.category == "safety_guardrail_bypass":
        warnings.append("safety guardrail bypass reports require immediate maintainer review")

    return SecurityReportValidationResult(
        report_id=r.report_id or "<unknown>",
        severity=r.severity,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_report_dict(d: dict) -> SecurityReportValidationResult:
    required = [
        "report_id", "severity", "category", "description",
        "affected_version", "reporter_handle", "report_date", "status",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return SecurityReportValidationResult(
            report_id=d.get("report_id", "<unknown>"),
            severity=d.get("severity", "<unknown>"),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            warnings=[],
            dry_lab_only=True,
        )
    r = VulnerabilityReport(
        report_id=d.get("report_id", ""),
        severity=d.get("severity", ""),
        category=d.get("category", ""),
        description=d.get("description", ""),
        affected_version=d.get("affected_version", ""),
        reporter_handle=d.get("reporter_handle", ""),
        report_date=d.get("report_date", ""),
        status=d.get("status", ""),
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_vulnerability_report(r)
