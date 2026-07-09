"""Tests for post-experiment calibration intake schema (Phase K K4)."""

import pytest
from openamp_foundry.evidence.calibration_intake import (
    VALID_ASSAY_TYPES,
    VALID_OUTCOME_VALUES,
    CalibrationIntakeEntry,
    CalibrationIntakeResult,
    validate_calibration_intake,
    validate_calibration_intake_dict,
)


def _valid_entry(**kwargs) -> CalibrationIntakeEntry:
    defaults = dict(
        intake_id="CAL-001",
        batch_id="BATCH-001",
        candidate_id="AMP-001",
        pipeline_version="0.8.1",
        assay_type="mic_assay",
        predicted_outcome="active",
        observed_outcome="active",
        predicted_confidence=0.85,
        intake_date="2026-07-09",
        reviewer="alice",
        dry_lab_only=False,
    )
    defaults.update(kwargs)
    return CalibrationIntakeEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_valid_assay_types_contains_mic():
    assert "mic_assay" in VALID_ASSAY_TYPES


def test_valid_assay_types_contains_hemolysis():
    assert "hemolysis_assay" in VALID_ASSAY_TYPES


def test_valid_outcome_values_contains_active():
    assert "active" in VALID_OUTCOME_VALUES


def test_valid_outcome_values_contains_inconclusive():
    assert "inconclusive" in VALID_OUTCOME_VALUES


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_calibration_intake(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_is_false():
    result = validate_calibration_intake(_valid_entry())
    assert result.dry_lab_only is False


def test_result_fields_match_entry():
    entry = _valid_entry()
    result = validate_calibration_intake(entry)
    assert result.intake_id == "CAL-001"
    assert result.candidate_id == "AMP-001"


def test_prediction_correct_true_when_match():
    result = validate_calibration_intake(
        _valid_entry(predicted_outcome="active", observed_outcome="active")
    )
    assert result.prediction_correct is True


def test_prediction_correct_false_when_mismatch():
    result = validate_calibration_intake(
        _valid_entry(predicted_outcome="active", observed_outcome="inactive")
    )
    assert result.prediction_correct is False


def test_valid_with_all_assay_types():
    for assay in VALID_ASSAY_TYPES:
        result = validate_calibration_intake(_valid_entry(assay_type=assay))
        assert result.passed, f"assay_type '{assay}' should be valid"


def test_valid_with_all_outcome_values():
    for outcome in VALID_OUTCOME_VALUES - {"inconclusive"}:
        result = validate_calibration_intake(
            _valid_entry(predicted_outcome=outcome, observed_outcome=outcome)
        )
        assert result.passed, f"outcome '{outcome}' should be valid"


# ── intake_id validation ──────────────────────────────────────────────────────


def test_intake_id_missing_prefix_fails():
    result = validate_calibration_intake(_valid_entry(intake_id="001"))
    assert not result.passed
    assert any("CAL-" in e for e in result.errors)


def test_intake_id_wrong_prefix_fails():
    result = validate_calibration_intake(_valid_entry(intake_id="PKG-001"))
    assert not result.passed


def test_intake_id_correct_prefix_passes():
    result = validate_calibration_intake(_valid_entry(intake_id="CAL-XYZ-99"))
    assert result.passed


# ── assay_type validation ─────────────────────────────────────────────────────


def test_invalid_assay_type_fails():
    result = validate_calibration_intake(_valid_entry(assay_type="unknown_assay"))
    assert not result.passed
    assert any("assay_type" in e for e in result.errors)


# ── outcome validation ────────────────────────────────────────────────────────


def test_invalid_predicted_outcome_fails():
    result = validate_calibration_intake(_valid_entry(predicted_outcome="maybe"))
    assert not result.passed
    assert any("predicted_outcome" in e for e in result.errors)


def test_invalid_observed_outcome_fails():
    result = validate_calibration_intake(_valid_entry(observed_outcome="unknown"))
    assert not result.passed
    assert any("observed_outcome" in e for e in result.errors)


# ── confidence validation ─────────────────────────────────────────────────────


def test_confidence_above_1_fails():
    result = validate_calibration_intake(_valid_entry(predicted_confidence=1.1))
    assert not result.passed


def test_confidence_negative_fails():
    result = validate_calibration_intake(_valid_entry(predicted_confidence=-0.1))
    assert not result.passed


def test_confidence_0_passes():
    result = validate_calibration_intake(_valid_entry(predicted_confidence=0.0))
    assert result.passed


def test_confidence_1_passes():
    result = validate_calibration_intake(_valid_entry(predicted_confidence=1.0))
    assert result.passed


# ── date validation ───────────────────────────────────────────────────────────


def test_invalid_date_fails():
    result = validate_calibration_intake(_valid_entry(intake_date="07-09-2026"))
    assert not result.passed
    assert any("YYYY-MM-DD" in e for e in result.errors)


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_true_fails():
    result = validate_calibration_intake(_valid_entry(dry_lab_only=True))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_high_confidence_misprediction_warns():
    result = validate_calibration_intake(
        _valid_entry(
            predicted_outcome="active",
            observed_outcome="inactive",
            predicted_confidence=0.95,
        )
    )
    assert result.passed
    assert any("High-confidence" in w or "misprediction" in w for w in result.warnings)


def test_inconclusive_observed_warns():
    result = validate_calibration_intake(
        _valid_entry(
            predicted_outcome="active",
            observed_outcome="inconclusive",
        )
    )
    assert result.passed
    assert any("inconclusive" in w for w in result.warnings)


def test_correct_prediction_no_warnings():
    result = validate_calibration_intake(
        _valid_entry(predicted_outcome="active", observed_outcome="active", predicted_confidence=0.95)
    )
    assert result.passed
    assert result.warnings == []


def test_low_confidence_mismatch_no_warning():
    result = validate_calibration_intake(
        _valid_entry(
            predicted_outcome="active",
            observed_outcome="inactive",
            predicted_confidence=0.70,
        )
    )
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        intake_id="CAL-D01",
        batch_id="BATCH-D01",
        candidate_id="AMP-D01",
        pipeline_version="0.8.1",
        assay_type="mic_assay",
        predicted_outcome="active",
        observed_outcome="active",
        predicted_confidence=0.85,
        intake_date="2026-07-09",
        reviewer="alice",
        dry_lab_only=False,
    )
    result = validate_calibration_intake_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        intake_id="CAL-D02",
        batch_id="BATCH-D02",
        candidate_id="AMP-D02",
        pipeline_version="0.8.1",
        assay_type="mic_assay",
        predicted_outcome="active",
        observed_outcome="active",
        predicted_confidence=0.85,
        # missing intake_date
        reviewer="alice",
    )
    result = validate_calibration_intake_dict(d)
    assert not result.passed
    assert any("intake_date" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_false():
    d = dict(
        intake_id="CAL-D03",
        batch_id="BATCH-D03",
        candidate_id="AMP-D03",
        pipeline_version="0.8.1",
        assay_type="mic_assay",
        predicted_outcome="active",
        observed_outcome="active",
        predicted_confidence=0.85,
        intake_date="2026-07-09",
        reviewer="alice",
    )
    result = validate_calibration_intake_dict(d)
    assert result.passed
    assert result.dry_lab_only is False
