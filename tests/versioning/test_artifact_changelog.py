"""Tests for artifact_changelog module."""
from openamp_foundry.versioning.artifact_changelog import (
    CHANGE_TYPES,
    ARTIFACT_CHANGELOG,
    ChangelogEntry,
    get_changelog_entries,
    validate_changelog,
    changelog_summary,
)


def test_has_at_least_5_entries():
    assert len(ARTIFACT_CHANGELOG) >= 5


def test_all_entries_pass_validation():
    errors = validate_changelog()
    assert errors == [], f"Validation errors: {errors}"


def test_get_changelog_entries_no_filter():
    entries = get_changelog_entries()
    assert len(entries) == len(ARTIFACT_CHANGELOG)


def test_get_changelog_entries_filters_by_artifact_name():
    entries = get_changelog_entries(artifact_name="benchmark_card")
    assert all(e.artifact_name == "benchmark_card" for e in entries)
    assert len(entries) >= 1


def test_get_changelog_entries_breaking_only():
    entries = get_changelog_entries(breaking_only=True)
    assert all(e.breaking for e in entries)


def test_get_changelog_entries_change_type():
    entries = get_changelog_entries(change_type="added")
    assert all(e.change_type == "added" for e in entries)
    assert len(entries) >= 1


def test_validate_changelog_catches_empty_artifact_name():
    bad_entry = ChangelogEntry(
        version="1.0.0",
        date="2026-01-01",
        artifact_name="",
        change_type="added",
        description="test",
    )
    original = list(ARTIFACT_CHANGELOG)
    ARTIFACT_CHANGELOG.append(bad_entry)
    try:
        errors = validate_changelog()
        assert any("empty artifact_name" in err for err in errors)
    finally:
        ARTIFACT_CHANGELOG.clear()
        ARTIFACT_CHANGELOG.extend(original)


def test_validate_changelog_catches_invalid_change_type():
    bad_entry = ChangelogEntry(
        version="1.0.0",
        date="2026-01-01",
        artifact_name="test",
        change_type="invalid_type",
        description="test",
    )
    original = list(ARTIFACT_CHANGELOG)
    ARTIFACT_CHANGELOG.append(bad_entry)
    try:
        errors = validate_changelog()
        assert any("invalid change_type" in err for err in errors)
    finally:
        ARTIFACT_CHANGELOG.clear()
        ARTIFACT_CHANGELOG.extend(original)


def test_validate_changelog_catches_invalid_version():
    bad_entry = ChangelogEntry(
        version="not-a-version",
        date="2026-01-01",
        artifact_name="test",
        change_type="added",
        description="test",
    )
    original = list(ARTIFACT_CHANGELOG)
    ARTIFACT_CHANGELOG.append(bad_entry)
    try:
        errors = validate_changelog()
        assert any("invalid version format" in err for err in errors)
    finally:
        ARTIFACT_CHANGELOG.clear()
        ARTIFACT_CHANGELOG.extend(original)


def test_changelog_summary_total_correct():
    summary = changelog_summary()
    assert summary["total"] == len(ARTIFACT_CHANGELOG)


def test_changelog_summary_dry_lab_only():
    summary = changelog_summary()
    assert summary["dry_lab_only"] is True


def test_changelog_summary_breaking_changes():
    summary = changelog_summary()
    expected = sum(1 for e in ARTIFACT_CHANGELOG if e.breaking)
    assert summary["breaking_changes"] == expected


def test_changelog_summary_artifacts_covered_sorted():
    summary = changelog_summary()
    assert summary["artifacts_covered"] == sorted(summary["artifacts_covered"])
    assert len(summary["artifacts_covered"]) >= 1
