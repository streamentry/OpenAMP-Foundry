"""Tests for Phase Q Q3 post-experiment calibration update schema (PCU-)."""

from __future__ import annotations

import math

import pytest

from openamp_foundry.evidence.post_experiment_calibration_update import (
    VALID_CALIBRATION_TRIGGER_TYPES,
    VALID_UPDATE_DIRECTIONS,
    MAX_NOTES_LEN,
    MAX_RATIONALE_LEN,
    PostExperimentCalibrationUpdate,
    PCUValidationResult,
    build_post_experiment_calibration_update,
    format_post_experiment_calibration_update,
    validate_post_experiment_calibration_update,
)


def _make_valid_record(**overrides) -> PostExperimentCalibrationUpdate:
    defaults = dict(
        pcu_id="PCU-0001",
        update_date="2026-07-10",
        n_whr_records=2,
        whr_ids=["WHR-0001", "WHR-0002"],
        trigger_type="hit_rate_above_baseline",
        update_direction="expand_candidate_pool",
        update_magnitude=0.15,
        rationale="Hit rate exceeded baseline by 2x in first pilot batch.",
        limitations=[
            "Based on single pilot batch only.",
            "E. coli ATCC 25922 only; no clinical isolates tested.",
        ],
        human_reviewed=True,
        dry_lab_only=False,
        reviewer_id="LAB-REVIEWER-001",
        related_ccs_id="CCS-0001",
        notes="",
        prediction_error_before=0.18,
        prediction_error_after=0.12,
    )
    defaults.update(overrides)
    return PostExperimentCalibrationUpdate(**defaults)


class TestPCUConstants:
    def test_valid_update_directions_is_frozenset(self):
        assert isinstance(VALID_UPDATE_DIRECTIONS, frozenset)

    def test_increase_threshold_in_directions(self):
        assert "increase_threshold" in VALID_UPDATE_DIRECTIONS

    def test_no_change_in_directions(self):
        assert "no_change" in VALID_UPDATE_DIRECTIONS

    def test_valid_trigger_types_is_frozenset(self):
        assert isinstance(VALID_CALIBRATION_TRIGGER_TYPES, frozenset)

    def test_hit_rate_above_baseline_in_triggers(self):
        assert "hit_rate_above_baseline" in VALID_CALIBRATION_TRIGGER_TYPES

    def test_insufficient_data_in_triggers(self):
        assert "insufficient_data" in VALID_CALIBRATION_TRIGGER_TYPES

    def test_max_rationale_len_positive(self):
        assert MAX_RATIONALE_LEN > 0

    def test_max_notes_len_positive(self):
        assert MAX_NOTES_LEN > 0

    def test_update_directions_has_five_values(self):
        assert len(VALID_UPDATE_DIRECTIONS) == 5

    def test_trigger_types_has_seven_values(self):
        assert len(VALID_CALIBRATION_TRIGGER_TYPES) == 7


class TestPCUDataclass:
    def test_valid_record_created(self):
        record = _make_valid_record()
        assert record.pcu_id == "PCU-0001"

    def test_dry_lab_only_false(self):
        record = _make_valid_record()
        assert record.dry_lab_only is False

    def test_human_reviewed_true(self):
        record = _make_valid_record()
        assert record.human_reviewed is True

    def test_n_whr_records_set(self):
        record = _make_valid_record()
        assert record.n_whr_records == 2

    def test_whr_ids_is_list(self):
        record = _make_valid_record()
        assert isinstance(record.whr_ids, list)

    def test_limitations_is_list(self):
        record = _make_valid_record()
        assert isinstance(record.limitations, list)


class TestValidatePCU:
    def test_valid_record_passes(self):
        result = validate_post_experiment_calibration_update(_make_valid_record())
        assert result.valid is True

    def test_valid_record_no_violations(self):
        result = validate_post_experiment_calibration_update(_make_valid_record())
        assert result.violations == []

    def test_dry_lab_only_true_fails(self):
        record = _make_valid_record(dry_lab_only=True)
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_dry_lab_only_true_violation_message(self):
        record = _make_valid_record(dry_lab_only=True)
        result = validate_post_experiment_calibration_update(record)
        assert any("dry_lab_only must be False" in v for v in result.violations)

    def test_human_reviewed_false_fails(self):
        record = _make_valid_record(human_reviewed=False)
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_human_reviewed_false_violation_message(self):
        record = _make_valid_record(human_reviewed=False)
        result = validate_post_experiment_calibration_update(record)
        assert any("human_reviewed must be True" in v for v in result.violations)

    def test_bad_pcu_id_fails(self):
        record = _make_valid_record(pcu_id="NOTAPCU")
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_n_whr_records_zero_fails(self):
        record = _make_valid_record(n_whr_records=0, whr_ids=[])
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_n_whr_records_mismatch_fails(self):
        record = _make_valid_record(n_whr_records=3, whr_ids=["WHR-0001"])
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_empty_whr_ids_fails(self):
        record = _make_valid_record(n_whr_records=0, whr_ids=[])
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_empty_update_date_fails(self):
        record = _make_valid_record(update_date="")
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_invalid_trigger_type_fails(self):
        record = _make_valid_record(trigger_type="unknown_trigger")
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_invalid_update_direction_fails(self):
        record = _make_valid_record(update_direction="random_direction")
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_update_magnitude_negative_fails(self):
        record = _make_valid_record(update_magnitude=-0.1)
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_update_magnitude_above_one_fails(self):
        record = _make_valid_record(update_magnitude=1.1)
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_update_magnitude_zero_passes(self):
        record = _make_valid_record(update_magnitude=0.0, update_direction="no_change")
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is True

    def test_update_magnitude_one_passes(self):
        record = _make_valid_record(update_magnitude=1.0)
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is True

    def test_update_magnitude_nan_fails(self):
        record = _make_valid_record(update_magnitude=float("nan"))
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_empty_rationale_fails(self):
        record = _make_valid_record(rationale="")
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_rationale_too_long_fails(self):
        record = _make_valid_record(rationale="x" * (MAX_RATIONALE_LEN + 1))
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_empty_limitations_fails(self):
        record = _make_valid_record(limitations=[])
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_negative_prediction_error_before_fails(self):
        record = _make_valid_record(prediction_error_before=-0.1)
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_negative_prediction_error_after_fails(self):
        record = _make_valid_record(prediction_error_after=-0.1)
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_notes_too_long_fails(self):
        record = _make_valid_record(notes="x" * (MAX_NOTES_LEN + 1))
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is False

    def test_all_valid_directions_pass(self):
        for direction in VALID_UPDATE_DIRECTIONS:
            record = _make_valid_record(update_direction=direction)
            result = validate_post_experiment_calibration_update(record)
            assert result.valid, f"Expected VALID for direction={direction}, got {result.violations}"

    def test_all_valid_trigger_types_pass(self):
        for trigger in VALID_CALIBRATION_TRIGGER_TYPES:
            record = _make_valid_record(trigger_type=trigger)
            result = validate_post_experiment_calibration_update(record)
            assert result.valid, f"Expected VALID for trigger_type={trigger}, got {result.violations}"

    def test_returns_pcu_validation_result(self):
        result = validate_post_experiment_calibration_update(_make_valid_record())
        assert isinstance(result, PCUValidationResult)

    def test_pcu_id_in_result(self):
        result = validate_post_experiment_calibration_update(_make_valid_record())
        assert result.pcu_id == "PCU-0001"


class TestBuildPCU:
    def test_build_returns_record(self):
        record = build_post_experiment_calibration_update(
            pcu_id="PCU-0001",
            update_date="2026-07-10",
            whr_ids=["WHR-0001"],
            trigger_type="hit_rate_above_baseline",
            update_direction="expand_candidate_pool",
            update_magnitude=0.1,
            rationale="Hit rate exceeded baseline.",
            limitations=["Single batch only."],
        )
        assert isinstance(record, PostExperimentCalibrationUpdate)

    def test_build_enforces_dry_lab_only_false(self):
        record = build_post_experiment_calibration_update(
            pcu_id="PCU-0001",
            update_date="2026-07-10",
            whr_ids=["WHR-0001"],
            trigger_type="hit_rate_above_baseline",
            update_direction="no_change",
            update_magnitude=0.0,
            rationale="No change warranted.",
            limitations=["Insufficient data."],
        )
        assert record.dry_lab_only is False

    def test_build_enforces_human_reviewed_true(self):
        record = build_post_experiment_calibration_update(
            pcu_id="PCU-0002",
            update_date="2026-07-10",
            whr_ids=["WHR-0001", "WHR-0002"],
            trigger_type="safety_signal_observed",
            update_direction="restrict_candidate_pool",
            update_magnitude=0.2,
            rationale="Safety signal observed.",
            limitations=["Limited n=2 observations."],
        )
        assert record.human_reviewed is True

    def test_build_sets_n_whr_records_from_list(self):
        record = build_post_experiment_calibration_update(
            pcu_id="PCU-0003",
            update_date="2026-07-10",
            whr_ids=["WHR-0001", "WHR-0002", "WHR-0003"],
            trigger_type="scheduled_review",
            update_direction="no_change",
            update_magnitude=0.0,
            rationale="Scheduled review.",
            limitations=["Insufficient data."],
        )
        assert record.n_whr_records == 3

    def test_build_validates_successfully(self):
        record = build_post_experiment_calibration_update(
            pcu_id="PCU-0004",
            update_date="2026-07-10",
            whr_ids=["WHR-0001"],
            trigger_type="novel_family_detected",
            update_direction="expand_candidate_pool",
            update_magnitude=0.05,
            rationale="Novel family detected in pilot batch.",
            limitations=["Single batch observation."],
        )
        result = validate_post_experiment_calibration_update(record)
        assert result.valid is True


class TestFormatPCU:
    def test_format_returns_string(self):
        record = _make_valid_record()
        output = format_post_experiment_calibration_update(record)
        assert isinstance(output, str)

    def test_format_contains_pcu_id(self):
        record = _make_valid_record()
        output = format_post_experiment_calibration_update(record)
        assert "PCU-0001" in output

    def test_format_contains_trigger_type(self):
        record = _make_valid_record()
        output = format_post_experiment_calibration_update(record)
        assert "hit_rate_above_baseline" in output

    def test_format_contains_human_reviewed(self):
        record = _make_valid_record()
        output = format_post_experiment_calibration_update(record)
        assert "human_reviewed" in output

    def test_format_valid_shows_valid(self):
        record = _make_valid_record()
        output = format_post_experiment_calibration_update(record)
        assert "VALID" in output

    def test_format_invalid_shows_invalid(self):
        record = _make_valid_record(human_reviewed=False)
        output = format_post_experiment_calibration_update(record)
        assert "INVALID" in output or "VIOLATION" in output
