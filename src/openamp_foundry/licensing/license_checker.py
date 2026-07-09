"""Data license checker — validates license declarations for external data sources.

Prevents hidden legal risk by requiring explicit license declarations
before external data can influence pipeline outputs.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

# Licenses approved for use in pipeline outputs (not exhaustive — extend via governance review)
APPROVED_LICENSES: set[str] = {
    "CC0-1.0",          # Public domain dedication
    "CC-BY-4.0",        # Creative Commons Attribution
    "CC-BY-SA-4.0",     # CC Attribution-ShareAlike
    "MIT",              # MIT License
    "Apache-2.0",       # Apache 2.0
    "GPL-3.0",          # GNU GPL v3 (copyleft)
    "LGPL-2.1",         # GNU LGPL v2.1
    "BSD-2-Clause",     # BSD 2-clause
    "BSD-3-Clause",     # BSD 3-clause
    "ODbL-1.0",         # Open Database License
    "PDDL-1.0",         # Public Domain Dedication and License
}

# Licenses that require extra review before use in released outputs
RESTRICTED_LICENSES: set[str] = {
    "CC-BY-NC-4.0",     # Non-commercial only
    "CC-BY-NC-SA-4.0",  # Non-commercial + ShareAlike
    "custom",           # Custom license — needs human review
    "proprietary",      # Proprietary — human review mandatory
}

# Licenses that are blocked from pipeline outputs
BLOCKED_LICENSES: set[str] = {
    "unknown",          # Unknown license — cannot use
    "unlicensed",       # No license declared — cannot use
    "all-rights-reserved",  # Copyright, no reuse
}

VALID_USE_CONTEXTS: set[str] = {
    "training", "scoring", "benchmarking", "reporting", "publication", "internal"
}


@dataclass
class DataLicenseDeclaration:
    source_id: str
    source_name: str
    license_id: str
    use_context: str
    attribution_required: bool
    commercial_use_allowed: bool
    redistribution_allowed: bool
    modifications_allowed: bool
    human_review_required: bool
    notes: str = ""
    dry_lab_only: bool = True


@dataclass
class LicenseCheckResult:
    source_id: str
    license_id: str
    use_context: str
    passed: bool
    status: str  # "approved", "restricted", "blocked", "unknown_license"
    errors: list[str]
    warnings: list[str]
    dry_lab_only: bool = True


def check_data_license(decl: DataLicenseDeclaration) -> LicenseCheckResult:
    """Validate a single data license declaration."""
    errors: list[str] = []
    warnings: list[str] = []

    if not decl.source_id:
        errors.append("source_id must not be empty")
    if not decl.source_name:
        errors.append("source_name must not be empty")
    if not decl.license_id:
        errors.append("license_id must not be empty")
    if decl.use_context not in VALID_USE_CONTEXTS:
        errors.append(f"use_context={decl.use_context!r} not in {sorted(VALID_USE_CONTEXTS)}")
    if not decl.dry_lab_only:
        errors.append("dry_lab_only must be True")

    if decl.license_id in BLOCKED_LICENSES:
        errors.append(f"license_id={decl.license_id!r} is blocked; cannot use in pipeline")
        status = "blocked"
    elif decl.license_id in RESTRICTED_LICENSES:
        warnings.append(
            f"license_id={decl.license_id!r} is restricted; human review required before release"
        )
        if not decl.human_review_required:
            errors.append(
                "human_review_required must be True for restricted licenses"
            )
        status = "restricted"
    elif decl.license_id in APPROVED_LICENSES:
        status = "approved"
        if decl.use_context == "publication" and not decl.redistribution_allowed:
            errors.append("redistribution_allowed must be True for publication use context")
    else:
        errors.append(
            f"license_id={decl.license_id!r} not in approved, restricted, or blocked lists; "
            "add to APPROVED_LICENSES after governance review"
        )
        status = "unknown_license"

    return LicenseCheckResult(
        source_id=decl.source_id or "<unknown>",
        license_id=decl.license_id,
        use_context=decl.use_context,
        passed=len(errors) == 0,
        status=status,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def check_license_batch(
    declarations: list[DataLicenseDeclaration],
) -> dict[str, Any]:
    """Check a list of declarations and return summary."""
    results = [check_data_license(d) for d in declarations]
    passed = [r for r in results if r.passed]
    failed = [r for r in results if not r.passed]
    blocked = [r for r in results if r.status == "blocked"]
    return {
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "blocked": len(blocked),
        "any_blocked": len(blocked) > 0,
        "all_passed": len(failed) == 0,
        "results": [vars(r) for r in results],
        "dry_lab_only": True,
    }
