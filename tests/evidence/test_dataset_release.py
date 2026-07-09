"""Tests for dataset release package checker (Phase L L5)."""

import pytest
from openamp_foundry.evidence.dataset_release import (
    MINIMUM_DATA_SOURCES,
    VALID_LICENSE_IDENTIFIERS,
    DatasetReleaseEntry,
    DatasetReleaseResult,
    validate_dataset_release,
    validate_dataset_release_dict,
)


def _valid_entry(**kwargs) -> DatasetReleaseEntry:
    defaults = dict(
        release_id="DSR-001",
        dataset_name="OpenAMP Wave 0.5 Candidates",
        dataset_version="1.0.0",
        release_date="2026-07-09",
        license_identifier="CC-BY-4.0",
        data_sources=["UniProt AMP database", "APD3", "in-house pipeline"],
        contains_sequences=True,
        contains_activity_data=False,
        dual_use_assessed=True,
        usage_policy_url="https://openamp.example.org/data-policy",
        contact_email="data@openamp.example.org",
        release_approved=True,
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return DatasetReleaseEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_minimum_data_sources_is_one():
    assert MINIMUM_DATA_SOURCES == 1


def test_valid_license_identifiers_count():
    assert len(VALID_LICENSE_IDENTIFIERS) == 5


def test_cc_by_in_valid_licenses():
    assert "CC-BY-4.0" in VALID_LICENSE_IDENTIFIERS


def test_cc0_in_valid_licenses():
    assert "CC0-1.0" in VALID_LICENSE_IDENTIFIERS


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_dataset_release(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_true():
    result = validate_dataset_release(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_match():
    result = validate_dataset_release(_valid_entry())
    assert result.release_id == "DSR-001"
    assert result.dataset_name == "OpenAMP Wave 0.5 Candidates"


def test_valid_all_licenses():
    for lic in VALID_LICENSE_IDENTIFIERS - {"CC-BY-NC-4.0"}:
        result = validate_dataset_release(_valid_entry(license_identifier=lic))
        assert result.passed, f"license '{lic}' should be valid"


def test_valid_with_activity_data():
    result = validate_dataset_release(
        _valid_entry(contains_activity_data=True, dual_use_assessed=True)
    )
    assert result.passed


def test_valid_single_data_source():
    result = validate_dataset_release(_valid_entry(data_sources=["UniProt AMP database"]))
    assert result.passed


# ── release_id validation ─────────────────────────────────────────────────────


def test_release_id_missing_prefix_fails():
    result = validate_dataset_release(_valid_entry(release_id="001"))
    assert not result.passed
    assert any("DSR-" in e for e in result.errors)


def test_release_id_wrong_prefix_fails():
    result = validate_dataset_release(_valid_entry(release_id="CMP-001"))
    assert not result.passed


def test_release_id_correct_prefix_passes():
    result = validate_dataset_release(_valid_entry(release_id="DSR-XYZ-99"))
    assert result.passed


# ── date validation ───────────────────────────────────────────────────────────


def test_invalid_date_fails():
    result = validate_dataset_release(_valid_entry(release_date="09-07-2026"))
    assert not result.passed
    assert any("YYYY-MM-DD" in e for e in result.errors)


# ── license validation ────────────────────────────────────────────────────────


def test_invalid_license_fails():
    result = validate_dataset_release(_valid_entry(license_identifier="GPL-3.0"))
    assert not result.passed
    assert any("license_identifier" in e for e in result.errors)


# ── dual_use_assessed constraint ──────────────────────────────────────────────


def test_dual_use_not_assessed_fails():
    result = validate_dataset_release(_valid_entry(dual_use_assessed=False))
    assert not result.passed
    assert any("dual_use_assessed" in e for e in result.errors)


# ── release_approved constraint ───────────────────────────────────────────────


def test_release_not_approved_fails():
    result = validate_dataset_release(_valid_entry(release_approved=False))
    assert not result.passed
    assert any("release_approved" in e for e in result.errors)


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_dataset_release(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── empty field constraints ───────────────────────────────────────────────────


def test_empty_dataset_name_fails():
    result = validate_dataset_release(_valid_entry(dataset_name=""))
    assert not result.passed


def test_empty_usage_policy_url_fails():
    result = validate_dataset_release(_valid_entry(usage_policy_url=""))
    assert not result.passed


def test_empty_contact_email_fails():
    result = validate_dataset_release(_valid_entry(contact_email=""))
    assert not result.passed


# ── data_sources validation ───────────────────────────────────────────────────


def test_empty_data_sources_fails():
    result = validate_dataset_release(_valid_entry(data_sources=[]))
    assert not result.passed
    assert any("data_sources" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_nc_license_warns():
    result = validate_dataset_release(_valid_entry(license_identifier="CC-BY-NC-4.0"))
    assert result.passed
    assert any("non-commercial" in w or "NC" in w for w in result.warnings)


def test_single_source_warns():
    result = validate_dataset_release(_valid_entry(data_sources=["UniProt"]))
    assert result.passed
    assert any("one data source" in w or "provenance" in w for w in result.warnings)


def test_multiple_sources_no_warning():
    result = validate_dataset_release(_valid_entry())
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        release_id="DSR-D01",
        dataset_name="Test Dataset",
        dataset_version="0.1.0",
        release_date="2026-07-09",
        license_identifier="CC-BY-4.0",
        data_sources=["source_a", "source_b"],
        contains_sequences=True,
        contains_activity_data=False,
        dual_use_assessed=True,
        usage_policy_url="https://example.org/policy",
        contact_email="test@example.org",
        release_approved=True,
        dry_lab_only=True,
    )
    result = validate_dataset_release_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        release_id="DSR-D02",
        dataset_name="Test",
        dataset_version="0.1.0",
        release_date="2026-07-09",
        license_identifier="CC-BY-4.0",
        data_sources=["source_a"],
        contains_sequences=True,
        contains_activity_data=False,
        dual_use_assessed=True,
        usage_policy_url="https://example.org",
        # missing contact_email
        release_approved=True,
    )
    result = validate_dataset_release_dict(d)
    assert not result.passed
    assert any("contact_email" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_true():
    d = dict(
        release_id="DSR-D03",
        dataset_name="Test",
        dataset_version="0.1.0",
        release_date="2026-07-09",
        license_identifier="MIT",
        data_sources=["source_a", "source_b"],
        contains_sequences=False,
        contains_activity_data=False,
        dual_use_assessed=True,
        usage_policy_url="https://example.org",
        contact_email="test@example.org",
        release_approved=True,
    )
    result = validate_dataset_release_dict(d)
    assert result.passed
    assert result.dry_lab_only is True
