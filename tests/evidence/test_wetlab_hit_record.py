"""Tests for Phase Q Q2 wet-lab hit record schema (WHR-)."""

from __future__ import annotations

import math

import pytest

from openamp_foundry.evidence.wetlab_hit_record import (
    VALID_EXPERIMENT_TYPES,
    VALID_INTERPRETATIONS,
    VALID_PROOF_LADDER_LEVELS,
    MAX_NOTES_LEN,
    WetlabHitRecord,
    WHRValidationResult,
    build_wetlab_hit_record,
    format_wetlab_hit_record,
    validate_wetlab_hit_record,
)


def _make_valid_record(**overrides) -> WetlabHitRecord:
    defaults = dict(
        whr_id="WHR-0001",
        candidate_id="AMPF-000001",
        sequence="KWKLFKKIEK",
        experiment_date="2026-07-10",
        experiment_type="mic_broth_dilution",
        result_value=4.0,
        result_unit="µg/mL",
        interpretation="active",
        assay_lab="Partner Lab A",
        assay_method="CLSI broth microdilution",
        dry_lab_only=False,
        limitations=["Single replicate only.", "Tested against E. coli ATCC 25922 only."],
        notes="",
        related_bsp_id="BSP-0001",
        related_psc_id="PSC-0001",
        proof_ladder_level="single_assay_hit",
    )
    defaults.update(overrides)
    return WetlabHitRecord(**defaults)


class TestWHRConstants:
    def test_valid_experiment_types_is_frozenset(self):
        assert isinstance(VALID_EXPERIMENT_TYPES, frozenset)

    def test_mic_broth_dilution_in_types(self):
        assert "mic_broth_dilution" in VALID_EXPERIMENT_TYPES

    def test_hemolysis_assay_in_types(self):
        assert "hemolysis_assay" in VALID_EXPERIMENT_TYPES

    def test_valid_interpretations_is_frozenset(self):
        assert isinstance(VALID_INTERPRETATIONS, frozenset)

    def test_active_in_interpretations(self):
        assert "active" in VALID_INTERPRETATIONS

    def test_inactive_in_interpretations(self):
        assert "inactive" in VALID_INTERPRETATIONS

    def test_inconclusive_in_interpretations(self):
        assert "inconclusive" in VALID_INTERPRETATIONS

    def test_interpretations_has_three_values(self):
        assert len(VALID_INTERPRETATIONS) == 3

    def test_valid_proof_ladder_levels_is_frozenset(self):
        assert isinstance(VALID_PROOF_LADDER_LEVELS, frozenset)

    def test_single_assay_hit_in_levels(self):
        assert "single_assay_hit" in VALID_PROOF_LADDER_LEVELS

    def test_max_notes_len_positive(self):
        assert MAX_NOTES_LEN > 0

    def test_experiment_types_has_ten_values(self):
        assert len(VALID_EXPERIMENT_TYPES) == 10


class TestWetlabHitRecordDataclass:
    def test_valid_record_created(self):
        record = _make_valid_record()
        assert record.whr_id == "WHR-0001"

    def test_dry_lab_only_false(self):
        record = _make_valid_record()
        assert record.dry_lab_only is False

    def test_sequence_field_set(self):
        record = _make_valid_record()
        assert record.sequence == "KWKLFKKIEK"

    def test_interpretation_field_set(self):
        record = _make_valid_record()
        assert record.interpretation == "active"

    def test_limitations_is_list(self):
        record = _make_valid_record()
        assert isinstance(record.limitations, list)

    def test_result_value_is_float(self):
        record = _make_valid_record(result_value=4.0)
        assert isinstance(record.result_value, float)


class TestValidateWetlabHitRecord:
    def test_valid_record_passes(self):
        result = validate_wetlab_hit_record(_make_valid_record())
        assert result.valid is True

    def test_valid_record_no_violations(self):
        result = validate_wetlab_hit_record(_make_valid_record())
        assert result.violations == []

    def test_dry_lab_only_true_fails(self):
        record = _make_valid_record(dry_lab_only=True)
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_dry_lab_only_true_violation_message(self):
        record = _make_valid_record(dry_lab_only=True)
        result = validate_wetlab_hit_record(record)
        assert any("dry_lab_only must be False" in v for v in result.violations)

    def test_toy_candidate_id_fails(self):
        record = _make_valid_record(candidate_id="TOY-0001")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_toy_candidate_id_violation_message(self):
        record = _make_valid_record(candidate_id="TOY-0001")
        result = validate_wetlab_hit_record(record)
        assert any("TOY-" in v for v in result.violations)

    def test_bad_whr_id_fails(self):
        record = _make_valid_record(whr_id="NOTAWHR")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_empty_sequence_fails(self):
        record = _make_valid_record(sequence="")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_invalid_sequence_characters_fails(self):
        record = _make_valid_record(sequence="KWKLFKK123")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_invalid_experiment_type_fails(self):
        record = _make_valid_record(experiment_type="fake_assay")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_negative_result_value_fails(self):
        record = _make_valid_record(result_value=-1.0)
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_nan_result_value_fails(self):
        record = _make_valid_record(result_value=float("nan"))
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_inf_result_value_fails(self):
        record = _make_valid_record(result_value=float("inf"))
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_zero_result_value_passes(self):
        record = _make_valid_record(result_value=0.0)
        result = validate_wetlab_hit_record(record)
        assert result.valid is True

    def test_empty_result_unit_fails(self):
        record = _make_valid_record(result_unit="")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_invalid_interpretation_fails(self):
        record = _make_valid_record(interpretation="confirmed_active")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_empty_assay_lab_fails(self):
        record = _make_valid_record(assay_lab="")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_empty_assay_method_fails(self):
        record = _make_valid_record(assay_method="")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_empty_limitations_fails(self):
        record = _make_valid_record(limitations=[])
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_empty_limitations_violation_message(self):
        record = _make_valid_record(limitations=[])
        result = validate_wetlab_hit_record(record)
        assert any("limitations must be non-empty" in v for v in result.violations)

    def test_invalid_proof_ladder_level_fails(self):
        record = _make_valid_record(proof_ladder_level="clinical_validated")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_notes_too_long_fails(self):
        record = _make_valid_record(notes="x" * (MAX_NOTES_LEN + 1))
        result = validate_wetlab_hit_record(record)
        assert result.valid is False

    def test_notes_at_max_passes(self):
        record = _make_valid_record(notes="x" * MAX_NOTES_LEN)
        result = validate_wetlab_hit_record(record)
        assert result.valid is True

    def test_returns_whr_validation_result(self):
        result = validate_wetlab_hit_record(_make_valid_record())
        assert isinstance(result, WHRValidationResult)

    def test_whr_id_in_result_when_valid(self):
        result = validate_wetlab_hit_record(_make_valid_record())
        assert result.whr_id == "WHR-0001"

    def test_all_valid_interpretations_pass(self):
        for interp in VALID_INTERPRETATIONS:
            record = _make_valid_record(interpretation=interp)
            result = validate_wetlab_hit_record(record)
            assert result.valid, f"Expected VALID for interpretation={interp}, got {result.violations}"

    def test_all_valid_experiment_types_pass(self):
        for exp_type in VALID_EXPERIMENT_TYPES:
            record = _make_valid_record(experiment_type=exp_type)
            result = validate_wetlab_hit_record(record)
            assert result.valid, f"Expected VALID for experiment_type={exp_type}, got {result.violations}"

    def test_all_valid_proof_ladder_levels_pass(self):
        for level in VALID_PROOF_LADDER_LEVELS:
            record = _make_valid_record(proof_ladder_level=level)
            result = validate_wetlab_hit_record(record)
            assert result.valid, f"Expected VALID for proof_ladder_level={level}, got {result.violations}"

    def test_empty_experiment_date_fails(self):
        record = _make_valid_record(experiment_date="")
        result = validate_wetlab_hit_record(record)
        assert result.valid is False


class TestBuildWetlabHitRecord:
    def test_build_returns_record(self):
        record = build_wetlab_hit_record(
            whr_id="WHR-0001",
            candidate_id="AMPF-000001",
            sequence="KWKLFKKIEK",
            experiment_date="2026-07-10",
            experiment_type="mic_broth_dilution",
            result_value=4.0,
            result_unit="µg/mL",
            interpretation="active",
            assay_lab="Lab A",
            assay_method="CLSI",
            limitations=["Single replicate."],
        )
        assert isinstance(record, WetlabHitRecord)

    def test_build_enforces_dry_lab_only_false(self):
        record = build_wetlab_hit_record(
            whr_id="WHR-0001",
            candidate_id="AMPF-000001",
            sequence="KWKLFKKIEK",
            experiment_date="2026-07-10",
            experiment_type="mic_broth_dilution",
            result_value=4.0,
            result_unit="µg/mL",
            interpretation="active",
            assay_lab="Lab A",
            assay_method="CLSI",
            limitations=["Single replicate."],
        )
        assert record.dry_lab_only is False

    def test_build_default_proof_ladder_level(self):
        record = build_wetlab_hit_record(
            whr_id="WHR-0002",
            candidate_id="AMPF-000002",
            sequence="FLPKLKKLLK",
            experiment_date="2026-07-10",
            experiment_type="disk_diffusion",
            result_value=12.0,
            result_unit="mm",
            interpretation="active",
            assay_lab="Lab B",
            assay_method="Kirby-Bauer",
            limitations=["Single organism tested."],
        )
        assert record.proof_ladder_level == "single_assay_hit"

    def test_build_with_notes(self):
        record = build_wetlab_hit_record(
            whr_id="WHR-0003",
            candidate_id="AMPF-000003",
            sequence="GIKCKILKKLR",
            experiment_date="2026-07-10",
            experiment_type="kill_curve",
            result_value=8.0,
            result_unit="µg/mL",
            interpretation="inconclusive",
            assay_lab="Lab C",
            assay_method="time-kill",
            limitations=["Single replicate."],
            notes="Borderline result.",
        )
        assert record.notes == "Borderline result."

    def test_build_validates_successfully(self):
        record = build_wetlab_hit_record(
            whr_id="WHR-0004",
            candidate_id="AMPF-000004",
            sequence="RRWQWRMKKLG",
            experiment_date="2026-07-10",
            experiment_type="hemolysis_assay",
            result_value=2.5,
            result_unit="%",
            interpretation="active",
            assay_lab="Lab D",
            assay_method="RBC lysis assay",
            limitations=["RBC donor variability not controlled."],
        )
        result = validate_wetlab_hit_record(record)
        assert result.valid is True


class TestFormatWetlabHitRecord:
    def test_format_returns_string(self):
        record = _make_valid_record()
        output = format_wetlab_hit_record(record)
        assert isinstance(output, str)

    def test_format_contains_whr_id(self):
        record = _make_valid_record()
        output = format_wetlab_hit_record(record)
        assert "WHR-0001" in output

    def test_format_contains_candidate_id(self):
        record = _make_valid_record()
        output = format_wetlab_hit_record(record)
        assert "AMPF-000001" in output

    def test_format_contains_interpretation(self):
        record = _make_valid_record()
        output = format_wetlab_hit_record(record)
        assert "active" in output

    def test_format_contains_dry_lab_status(self):
        record = _make_valid_record()
        output = format_wetlab_hit_record(record)
        assert "dry_lab_only" in output

    def test_format_valid_record_shows_valid(self):
        record = _make_valid_record()
        output = format_wetlab_hit_record(record)
        assert "VALID" in output

    def test_format_invalid_record_shows_invalid(self):
        record = _make_valid_record(dry_lab_only=True)
        output = format_wetlab_hit_record(record)
        assert "INVALID" in output or "VIOLATION" in output
