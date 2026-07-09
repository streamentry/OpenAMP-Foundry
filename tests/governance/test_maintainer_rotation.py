"""Tests for maintainer rotation plan validator."""
from __future__ import annotations

from openamp_foundry.governance.maintainer_rotation import (
    CRITICAL_ROLES,
    MaintainerEntry,
    VALID_ROLES,
    validate_maintainer_entry,
    validate_rotation_plan,
    validate_rotation_plan_dict,
)


def _valid_primary() -> MaintainerEntry:
    return MaintainerEntry(
        github_handle="lead-maintainer",
        role="primary_maintainer",
        backup_handle="backup-maintainer",
        responsibilities=["releases", "safety-policy", "final-approvals"],
        status="active",
    )


def _valid_secondary() -> MaintainerEntry:
    return MaintainerEntry(
        github_handle="backup-maintainer",
        role="secondary_maintainer",
        backup_handle="lead-maintainer",
        responsibilities=["day-to-day-reviews", "issue-triage"],
        status="active",
    )


def test_valid_plan_passes():
    entries = [_valid_primary(), _valid_secondary()]
    result = validate_rotation_plan(entries)
    assert result.passed


def test_empty_entries_fails():
    result = validate_rotation_plan([])
    assert not result.passed
    assert any("at least one maintainer" in e for e in result.errors)


def test_empty_github_handle_fails():
    entry = _valid_primary()
    entry.github_handle = ""
    errors = validate_maintainer_entry(entry)
    assert any("github_handle must not be empty" in e for e in errors)


def test_invalid_role_fails():
    entry = _valid_primary()
    entry.role = "not_a_valid_role"
    errors = validate_maintainer_entry(entry)
    assert any("not in" in e for e in errors)


def test_critical_role_without_backup_fails():
    entry = _valid_primary()
    entry.backup_handle = ""
    errors = validate_maintainer_entry(entry)
    assert any("backup_handle required" in e for e in errors)


def test_empty_responsibilities_fails():
    entry = _valid_primary()
    entry.responsibilities = []
    errors = validate_maintainer_entry(entry)
    assert any("responsibilities must not be empty" in e for e in errors)


def test_invalid_status_fails():
    entry = _valid_primary()
    entry.status = "invalid_status"
    errors = validate_maintainer_entry(entry)
    assert any("not in" in e for e in errors)


def test_dry_lab_only_false_fails():
    entry = _valid_primary()
    entry.dry_lab_only = False
    errors = validate_maintainer_entry(entry)
    assert any("dry_lab_only must be True" in e for e in errors)


def test_no_active_primary_maintainer_fails():
    entries = [_valid_secondary()]
    result = validate_rotation_plan(entries)
    assert not result.passed
    assert any("no active maintainer with role='primary_maintainer'" in e for e in result.errors)


def test_no_active_secondary_maintainer_fails():
    entries = [_valid_primary()]
    result = validate_rotation_plan(entries)
    assert not result.passed
    assert any("no active maintainer with role='secondary_maintainer'" in e for e in result.errors)


def test_single_primary_produces_warning():
    entry = _valid_primary()
    entry.status = "active"
    sec = _valid_secondary()
    result = validate_rotation_plan([entry, sec])
    assert result.passed
    assert any("only 1 active primary_maintainer" in w for w in result.warnings)


def test_single_secondary_produces_warning():
    # Two primary maintainers, only one secondary -> warning on secondary
    entries = [
        MaintainerEntry(
            github_handle="lead-maintainer",
            role="primary_maintainer",
            backup_handle="backup-maintainer",
            responsibilities=["releases"],
            status="active",
        ),
        MaintainerEntry(
            github_handle="co-maintainer",
            role="primary_maintainer",
            backup_handle="lead-maintainer",
            responsibilities=["benchmarks"],
            status="active",
        ),
        _valid_secondary(),
    ]
    result = validate_rotation_plan(entries)
    assert result.passed
    assert any("only 1 active secondary_maintainer" in w for w in result.warnings)


def test_validate_dict_missing_entries_key_fails():
    result = validate_rotation_plan_dict({})
    assert not result.passed
    assert any("Missing required key" in e for e in result.errors)


def test_validate_dict_passes_with_valid_dict():
    d = {
        "entries": [
            {
                "github_handle": "lead-maintainer",
                "role": "primary_maintainer",
                "backup_handle": "backup-maintainer",
                "responsibilities": ["releases", "safety-policy"],
                "status": "active",
            },
            {
                "github_handle": "backup-maintainer",
                "role": "secondary_maintainer",
                "backup_handle": "lead-maintainer",
                "responsibilities": ["day-to-day-reviews"],
                "status": "active",
            },
        ]
    }
    result = validate_rotation_plan_dict(d)
    assert result.passed


def test_validate_dict_missing_entry_fields_fails():
    d = {
        "entries": [
            {
                "github_handle": "lead-maintainer",
                # missing role, backup_handle, responsibilities, status
            },
        ]
    }
    result = validate_rotation_plan_dict(d)
    assert not result.passed
    assert any("missing fields" in e for e in result.errors)


def test_all_results_have_dry_lab_only_true():
    entries = [_valid_primary(), _valid_secondary()]
    result = validate_rotation_plan(entries)
    assert result.dry_lab_only is True


def test_valid_roles_has_4_entries():
    assert len(VALID_ROLES) == 4


def test_critical_roles_has_2_entries():
    assert len(CRITICAL_ROLES) == 2


# Additional tests to ensure coverage
def test_contributor_valid():
    entry = MaintainerEntry(
        github_handle="contributor-user",
        role="contributor",
        backup_handle="",
        responsibilities=["submit-PRs"],
        status="active",
    )
    errors = validate_maintainer_entry(entry)
    assert not errors


def test_on_leave_status_valid():
    entry = _valid_primary()
    entry.status = "on_leave"
    errors = validate_maintainer_entry(entry)
    assert not errors


def test_emeritus_status_valid():
    entry = _valid_primary()
    entry.status = "emeritus"
    errors = validate_maintainer_entry(entry)
    assert not errors
