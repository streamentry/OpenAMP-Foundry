"""Tests for preprint evidence bundle schema (Phase L L1)."""

import pytest
from openamp_foundry.evidence.preprint_bundle import (
    MAX_TITLE_LENGTH,
    MINIMUM_ARTIFACTS,
    RECOMMENDED_ARTIFACT_COUNT,
    VALID_EVIDENCE_LEVELS,
    PreprintBundleEntry,
    PreprintBundleResult,
    validate_preprint_bundle,
    validate_preprint_bundle_dict,
)


def _valid_entry(**kwargs) -> PreprintBundleEntry:
    defaults = dict(
        bundle_id="BND-001",
        batch_id="BATCH-001",
        pipeline_version="0.8.4",
        submission_date="2026-07-09",
        title="Computational nomination of AMP candidates from the OpenAMP Foundry",
        artifact_ids=["SEL-001", "PRI-001", "PKG-001", "UQ-001", "CAL-001"],
        evidence_level=4,
        preprint_doi="10.1101/2026.07.09.000001",
        contact_email="research@openamp.org",
        release_approved=True,
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return PreprintBundleEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_minimum_artifacts_is_three():
    assert MINIMUM_ARTIFACTS == 3


def test_recommended_artifact_count_is_five():
    assert RECOMMENDED_ARTIFACT_COUNT == 5


def test_max_title_length_is_300():
    assert MAX_TITLE_LENGTH == 300


def test_valid_evidence_levels_range():
    assert VALID_EVIDENCE_LEVELS == {1, 2, 3, 4, 5, 6}


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_preprint_bundle(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_true():
    result = validate_preprint_bundle(_valid_entry())
    assert result.dry_lab_only is True


def test_result_artifact_count():
    result = validate_preprint_bundle(_valid_entry())
    assert result.artifact_count == 5


def test_result_fields_match():
    result = validate_preprint_bundle(_valid_entry())
    assert result.bundle_id == "BND-001"
    assert result.batch_id == "BATCH-001"


def test_valid_minimum_artifacts():
    result = validate_preprint_bundle(
        _valid_entry(artifact_ids=["SEL-001", "PRI-001", "PKG-001"])
    )
    assert result.passed


def test_valid_all_evidence_levels():
    for level in VALID_EVIDENCE_LEVELS - {1, 2}:
        result = validate_preprint_bundle(_valid_entry(evidence_level=level))
        assert result.passed, f"evidence_level {level} should be valid"


def test_valid_empty_doi():
    result = validate_preprint_bundle(_valid_entry(preprint_doi=""))
    assert result.passed


# ── bundle_id validation ──────────────────────────────────────────────────────


def test_bundle_id_missing_prefix_fails():
    result = validate_preprint_bundle(_valid_entry(bundle_id="001"))
    assert not result.passed
    assert any("BND-" in e for e in result.errors)


def test_bundle_id_wrong_prefix_fails():
    result = validate_preprint_bundle(_valid_entry(bundle_id="UQ-001"))
    assert not result.passed


def test_bundle_id_correct_prefix_passes():
    result = validate_preprint_bundle(_valid_entry(bundle_id="BND-XYZ-99"))
    assert result.passed


# ── date validation ───────────────────────────────────────────────────────────


def test_invalid_date_fails():
    result = validate_preprint_bundle(_valid_entry(submission_date="07/09/2026"))
    assert not result.passed
    assert any("YYYY-MM-DD" in e for e in result.errors)


# ── title validation ──────────────────────────────────────────────────────────


def test_empty_title_fails():
    result = validate_preprint_bundle(_valid_entry(title=""))
    assert not result.passed
    assert any("title" in e for e in result.errors)


def test_title_too_long_fails():
    result = validate_preprint_bundle(_valid_entry(title="X" * 301))
    assert not result.passed
    assert any("300" in e for e in result.errors)


def test_title_exactly_300_passes():
    result = validate_preprint_bundle(_valid_entry(title="X" * 300))
    assert result.passed


# ── artifact_ids validation ───────────────────────────────────────────────────


def test_too_few_artifacts_fails():
    result = validate_preprint_bundle(
        _valid_entry(artifact_ids=["SEL-001", "PRI-001"])
    )
    assert not result.passed
    assert any("at least" in e for e in result.errors)


def test_exactly_minimum_artifacts_passes():
    result = validate_preprint_bundle(
        _valid_entry(artifact_ids=["SEL-001", "PRI-001", "PKG-001"])
    )
    assert result.passed


# ── evidence_level validation ─────────────────────────────────────────────────


def test_invalid_evidence_level_fails():
    result = validate_preprint_bundle(_valid_entry(evidence_level=7))
    assert not result.passed
    assert any("evidence_level" in e for e in result.errors)


def test_evidence_level_zero_fails():
    result = validate_preprint_bundle(_valid_entry(evidence_level=0))
    assert not result.passed


# ── release_approved constraint ───────────────────────────────────────────────


def test_release_not_approved_fails():
    result = validate_preprint_bundle(_valid_entry(release_approved=False))
    assert not result.passed
    assert any("release_approved" in e for e in result.errors)


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_preprint_bundle(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_low_evidence_level_warns():
    result = validate_preprint_bundle(_valid_entry(evidence_level=2))
    assert result.passed
    assert any("low" in w or "scrutiny" in w for w in result.warnings)


def test_evidence_level_1_warns():
    result = validate_preprint_bundle(_valid_entry(evidence_level=1))
    assert result.passed
    assert result.warnings


def test_empty_doi_warns():
    result = validate_preprint_bundle(_valid_entry(preprint_doi=""))
    assert result.passed
    assert any("DOI" in w or "doi" in w.lower() for w in result.warnings)


def test_few_artifacts_warns():
    result = validate_preprint_bundle(
        _valid_entry(artifact_ids=["SEL-001", "PRI-001", "PKG-001"])
    )
    assert result.passed
    assert any("artifact" in w for w in result.warnings)


def test_full_bundle_no_warnings():
    result = validate_preprint_bundle(_valid_entry())
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        bundle_id="BND-D01",
        batch_id="BATCH-D01",
        pipeline_version="0.8.4",
        submission_date="2026-07-09",
        title="Test bundle",
        artifact_ids=["SEL-001", "PRI-001", "PKG-001", "UQ-001", "CAL-001"],
        evidence_level=4,
        preprint_doi="10.1101/test",
        contact_email="test@example.com",
        release_approved=True,
        dry_lab_only=True,
    )
    result = validate_preprint_bundle_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        bundle_id="BND-D02",
        batch_id="BATCH-D02",
        pipeline_version="0.8.4",
        submission_date="2026-07-09",
        title="Test bundle",
        artifact_ids=["SEL-001", "PRI-001", "PKG-001"],
        evidence_level=4,
        preprint_doi="",
        # missing contact_email
        release_approved=True,
    )
    result = validate_preprint_bundle_dict(d)
    assert not result.passed
    assert any("contact_email" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_true():
    d = dict(
        bundle_id="BND-D03",
        batch_id="BATCH-D03",
        pipeline_version="0.8.4",
        submission_date="2026-07-09",
        title="Test bundle",
        artifact_ids=["SEL-001", "PRI-001", "PKG-001", "UQ-001", "CAL-001"],
        evidence_level=4,
        preprint_doi="10.1101/test",
        contact_email="test@example.com",
        release_approved=True,
    )
    result = validate_preprint_bundle_dict(d)
    assert result.passed
    assert result.dry_lab_only is True
