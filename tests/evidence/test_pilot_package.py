"""Tests for pilot package completeness checker (Phase K K3)."""

import pytest
from openamp_foundry.evidence.pilot_package import (
    MANDATORY_ARTIFACT_TYPES,
    MINIMUM_REQUIRED_ARTIFACTS,
    READINESS_SCORE_THRESHOLD,
    VALID_ARTIFACT_TYPES,
    PilotPackageEntry,
    PilotPackageResult,
    validate_pilot_package,
    validate_pilot_package_dict,
)


def _valid_entry(**kwargs) -> PilotPackageEntry:
    defaults = dict(
        package_id="PKG-001",
        batch_id="BATCH-001",
        submission_date="2026-07-09",
        pipeline_version="0.8.1",
        included_artifacts=[
            "selection_rationale",
            "batch_priority",
            "evidence_certificate",
        ],
        missing_artifacts=[],
        reviewer="alice",
        approver="bob",
        completeness_score=1.0,
        ready_to_submit=True,
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return PilotPackageEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_minimum_required_artifacts_is_three():
    assert MINIMUM_REQUIRED_ARTIFACTS == 3


def test_readiness_score_threshold_is_0_80():
    assert READINESS_SCORE_THRESHOLD == 0.80


def test_mandatory_artifact_types_present():
    assert "selection_rationale" in MANDATORY_ARTIFACT_TYPES
    assert "batch_priority" in MANDATORY_ARTIFACT_TYPES
    assert "evidence_certificate" in MANDATORY_ARTIFACT_TYPES


def test_valid_artifact_types_superset_of_mandatory():
    assert MANDATORY_ARTIFACT_TYPES.issubset(VALID_ARTIFACT_TYPES)


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_pilot_package(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_has_dry_lab_only_true():
    result = validate_pilot_package(_valid_entry())
    assert result.dry_lab_only is True


def test_result_fields_match_entry():
    entry = _valid_entry()
    result = validate_pilot_package(entry)
    assert result.package_id == "PKG-001"
    assert result.batch_id == "BATCH-001"


def test_valid_with_optional_artifacts():
    entry = _valid_entry(
        included_artifacts=[
            "selection_rationale",
            "batch_priority",
            "evidence_certificate",
            "model_card",
            "safety_assessment",
        ],
        completeness_score=1.0,
    )
    result = validate_pilot_package(entry)
    assert result.passed
    assert result.errors == []


def test_valid_not_ready_to_submit():
    entry = _valid_entry(
        completeness_score=0.75,
        ready_to_submit=False,
    )
    result = validate_pilot_package(entry)
    assert result.passed
    assert result.errors == []


# ── package_id validation ─────────────────────────────────────────────────────


def test_package_id_missing_prefix_fails():
    result = validate_pilot_package(_valid_entry(package_id="001"))
    assert not result.passed
    assert any("PKG-" in e for e in result.errors)


def test_package_id_wrong_prefix_fails():
    result = validate_pilot_package(_valid_entry(package_id="BAT-001"))
    assert not result.passed


def test_package_id_correct_prefix_passes():
    result = validate_pilot_package(_valid_entry(package_id="PKG-XYZ-99"))
    assert result.passed


# ── date validation ───────────────────────────────────────────────────────────


def test_invalid_date_format_fails():
    result = validate_pilot_package(_valid_entry(submission_date="09-07-2026"))
    assert not result.passed
    assert any("YYYY-MM-DD" in e for e in result.errors)


def test_valid_date_passes():
    result = validate_pilot_package(_valid_entry(submission_date="2026-01-01"))
    assert result.passed


# ── included_artifacts validation ─────────────────────────────────────────────


def test_too_few_artifacts_fails():
    result = validate_pilot_package(
        _valid_entry(
            included_artifacts=["selection_rationale", "batch_priority"],
            missing_artifacts=["evidence_certificate"],
        )
    )
    assert not result.passed
    assert any("at least" in e for e in result.errors)


def test_missing_mandatory_artifact_fails():
    result = validate_pilot_package(
        _valid_entry(
            included_artifacts=[
                "selection_rationale",
                "batch_priority",
                "benchmark_card",
            ]
        )
    )
    assert not result.passed
    assert any("mandatory" in e for e in result.errors)


# ── completeness_score and ready_to_submit ────────────────────────────────────


def test_score_below_threshold_with_ready_true_fails():
    result = validate_pilot_package(
        _valid_entry(completeness_score=0.70, ready_to_submit=True)
    )
    assert not result.passed
    assert any("ready_to_submit" in e for e in result.errors)


def test_score_at_threshold_ready_true_passes():
    result = validate_pilot_package(
        _valid_entry(completeness_score=0.80, ready_to_submit=True)
    )
    assert result.passed


def test_score_out_of_range_fails():
    result = validate_pilot_package(_valid_entry(completeness_score=1.5))
    assert not result.passed


def test_score_negative_fails():
    result = validate_pilot_package(_valid_entry(completeness_score=-0.1))
    assert not result.passed


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_pilot_package(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_missing_artifacts_list_triggers_warning():
    result = validate_pilot_package(
        _valid_entry(
            missing_artifacts=["uncertainty_report"],
            completeness_score=0.85,
            ready_to_submit=True,
        )
    )
    assert result.passed
    assert any("missing" in w for w in result.warnings)


def test_score_below_90_triggers_warning():
    result = validate_pilot_package(
        _valid_entry(completeness_score=0.85, ready_to_submit=True)
    )
    assert result.passed
    assert any("0.85" in w or "0.90" in w for w in result.warnings)


def test_same_reviewer_approver_triggers_warning():
    result = validate_pilot_package(_valid_entry(reviewer="alice", approver="alice"))
    assert result.passed
    assert any("same person" in w for w in result.warnings)


def test_perfect_score_no_warnings():
    result = validate_pilot_package(_valid_entry())
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        package_id="PKG-D01",
        batch_id="BATCH-D01",
        submission_date="2026-07-09",
        pipeline_version="0.8.1",
        included_artifacts=["selection_rationale", "batch_priority", "evidence_certificate"],
        missing_artifacts=[],
        reviewer="alice",
        approver="bob",
        completeness_score=1.0,
        ready_to_submit=True,
        dry_lab_only=True,
    )
    result = validate_pilot_package_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        package_id="PKG-D02",
        batch_id="BATCH-D02",
        submission_date="2026-07-09",
        pipeline_version="0.8.1",
        included_artifacts=["selection_rationale", "batch_priority", "evidence_certificate"],
        missing_artifacts=[],
        reviewer="alice",
        # missing approver
        completeness_score=1.0,
        ready_to_submit=True,
    )
    result = validate_pilot_package_dict(d)
    assert not result.passed
    assert any("approver" in e for e in result.errors)


def test_dict_inherits_dry_lab_only_default():
    d = dict(
        package_id="PKG-D03",
        batch_id="BATCH-D03",
        submission_date="2026-07-09",
        pipeline_version="0.8.1",
        included_artifacts=["selection_rationale", "batch_priority", "evidence_certificate"],
        missing_artifacts=[],
        reviewer="alice",
        approver="bob",
        completeness_score=1.0,
        ready_to_submit=True,
    )
    result = validate_pilot_package_dict(d)
    assert result.passed
    assert result.dry_lab_only is True
