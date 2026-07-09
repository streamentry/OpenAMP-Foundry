"""Maintainer rotation validator — validates maintainer rotation plan entries.

Ensures the bus-factor plan has required fields and minimum coverage.
Dry-lab only.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

VALID_ROLES: set[str] = {
    "primary_maintainer", "secondary_maintainer", "external_advisor", "contributor"
}

VALID_STATUSES: set[str] = {
    "active", "on_leave", "emeritus", "departing"
}

CRITICAL_ROLES: set[str] = {
    "primary_maintainer", "secondary_maintainer"
}


@dataclass
class MaintainerEntry:
    github_handle: str
    role: str              # from VALID_ROLES
    backup_handle: str     # GitHub handle of backup (required for critical roles)
    responsibilities: list[str]   # must not be empty
    status: str            # from VALID_STATUSES
    dry_lab_only: bool = True


@dataclass
class RotationPlanValidationResult:
    passed: bool
    errors: list[str]
    warnings: list[str]
    maintainer_count: int
    critical_role_coverage: dict[str, int]
    bus_factor_sufficient: bool
    dry_lab_only: bool = True


def validate_maintainer_entry(entry: MaintainerEntry) -> list[str]:
    errors: list[str] = []
    if not entry.github_handle:
        errors.append("github_handle must not be empty")
    if entry.role not in VALID_ROLES:
        errors.append(f"role={entry.role!r} not in {sorted(VALID_ROLES)}")
    if entry.role in CRITICAL_ROLES and not entry.backup_handle:
        errors.append(f"backup_handle required for role={entry.role!r}")
    if not entry.responsibilities:
        errors.append("responsibilities must not be empty")
    if entry.status not in VALID_STATUSES:
        errors.append(f"status={entry.status!r} not in {sorted(VALID_STATUSES)}")
    if not entry.dry_lab_only:
        errors.append("dry_lab_only must be True")
    return errors


def validate_rotation_plan(entries: list[MaintainerEntry]) -> RotationPlanValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not entries:
        errors.append("rotation plan must have at least one maintainer entry")
        return RotationPlanValidationResult(
            passed=False,
            errors=errors,
            warnings=warnings,
            maintainer_count=0,
            critical_role_coverage={},
            bus_factor_sufficient=False,
            dry_lab_only=True,
        )

    for entry in entries:
        entry_errors = validate_maintainer_entry(entry)
        errors.extend(entry_errors)

    active_entries = [e for e in entries if e.status == "active"]
    critical_coverage: dict[str, int] = {role: 0 for role in CRITICAL_ROLES}
    for entry in active_entries:
        if entry.role in CRITICAL_ROLES:
            critical_coverage[entry.role] = critical_coverage.get(entry.role, 0) + 1

    bus_factor_ok = True
    for role in CRITICAL_ROLES:
        count = critical_coverage.get(role, 0)
        if count == 0:
            errors.append(f"no active maintainer with role={role!r}")
            bus_factor_ok = False
        elif count == 1:
            warnings.append(f"only 1 active {role} — bus factor risk; add a backup")

    return RotationPlanValidationResult(
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        maintainer_count=len(entries),
        critical_role_coverage=critical_coverage,
        bus_factor_sufficient=bus_factor_ok,
        dry_lab_only=True,
    )


def validate_rotation_plan_dict(d: dict[str, Any]) -> RotationPlanValidationResult:
    required_entry_fields = [
        "github_handle", "role", "backup_handle", "responsibilities", "status"
    ]
    if "entries" not in d:
        return RotationPlanValidationResult(
            passed=False,
            errors=["Missing required key: 'entries'"],
            warnings=[],
            maintainer_count=0,
            critical_role_coverage={},
            bus_factor_sufficient=False,
            dry_lab_only=True,
        )
    entries_raw = d["entries"]
    if not isinstance(entries_raw, list):
        return RotationPlanValidationResult(
            passed=False,
            errors=["'entries' must be a list"],
            warnings=[],
            maintainer_count=0,
            critical_role_coverage={},
            bus_factor_sufficient=False,
            dry_lab_only=True,
        )

    entries: list[MaintainerEntry] = []
    parse_errors: list[str] = []
    for i, raw in enumerate(entries_raw):
        missing = [f for f in required_entry_fields if f not in raw]
        if missing:
            parse_errors.append(f"entry[{i}] missing fields: {missing}")
            continue
        entries.append(MaintainerEntry(
            github_handle=raw.get("github_handle", ""),
            role=raw.get("role", ""),
            backup_handle=raw.get("backup_handle", ""),
            responsibilities=raw.get("responsibilities", []),
            status=raw.get("status", ""),
            dry_lab_only=raw.get("dry_lab_only", True),
        ))

    if parse_errors:
        return RotationPlanValidationResult(
            passed=False,
            errors=parse_errors,
            warnings=[],
            maintainer_count=0,
            critical_role_coverage={},
            bus_factor_sufficient=False,
            dry_lab_only=True,
        )

    return validate_rotation_plan(entries)
