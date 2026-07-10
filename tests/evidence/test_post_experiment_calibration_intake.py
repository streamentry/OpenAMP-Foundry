"""Tests for PostExperimentCalibrationIntake (PCI-) schema — Phase K K4."""

import pytest
from openamp_foundry.evidence.post_experiment_calibration_intake import (
    HIT_RATE_TOLERANCE,
    LOW_HIT_RATE_THRESHOLD,
    NOTES_MAX_LENGTH,
    PCI_PREFIX,
    RATIONALE_MAX_LENGTH,
    PostExperimentCalibrationIntake,
    PostExperimentCalibrationIntakeResult,
    validate,
    validate_dict,
)


def _make(**kwargs) -> PostExperimentCalibrationIntake:
    defaults = dict(
        pci_id="PCI-001",
        pipeline_version="v0.10.19",
        batch_id="BATCH-007",
        experiment_date="2026-07-10",
        candidates_tested=10,
        candidates_with_results=10,
        predicted_active_count=4,
        observed_active_count=3,
        prediction_hit_rate=0.3,
        calibration_update_warranted=True,
        calibration_update_rationale="Hit rate 0.30 vs predicted 0.40; update calibration with 3 confirmed actives.",
        data_quality_confirmed=True,
        notes="",
    )
    defaults.update(kwargs)
    return PostExperimentCalibrationIntake(**defaults)


# --- Baseline valid ---

class TestValidBaseline:
    def test_valid_record_passes(self):
        r = validate(_make())
        assert r.valid
        assert r.errors == []

    def test_valid_returns_result_type(self):
        r = validate(_make())
        assert isinstance(r, PostExperimentCalibrationIntakeResult)

    def test_valid_with_notes(self):
        r = validate(_make(notes="Reviewed by calibration team."))
        assert r.valid

    def test_valid_no_update_needed(self):
        r = validate(_make(
            observed_active_count=4,
            prediction_hit_rate=0.4,
            calibration_update_warranted=False,
            calibration_update_rationale="Hit rate 0.40 matches prediction; no update needed.",
        ))
        assert r.valid

    def test_valid_high_hit_rate(self):
        r = validate(_make(
            observed_active_count=8,
            prediction_hit_rate=0.8,
            calibration_update_warranted=False,
            calibration_update_rationale="Hit rate matches model prediction well.",
        ))
        assert r.valid

    def test_valid_zero_active(self):
        r = validate(_make(
            observed_active_count=0,
            prediction_hit_rate=0.0,
            calibration_update_warranted=True,
            calibration_update_rationale="No actives found; model overestimated activity.",
        ))
        assert r.valid


# --- pci_id validation ---

class TestPciIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(pci_id="CIR-001"))
        assert not r.valid
        assert any("pci_id" in e for e in r.errors)

    def test_empty_id(self):
        r = validate(_make(pci_id=""))
        assert not r.valid

    def test_lowercase_prefix(self):
        r = validate(_make(pci_id="pci-001"))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(pci_id="PCI-999"))
        assert r.valid


# --- pipeline_version validation ---

class TestPipelineVersionValidation:
    def test_empty_fails(self):
        r = validate(_make(pipeline_version=""))
        assert not r.valid
        assert any("pipeline_version" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(pipeline_version="   "))
        assert not r.valid

    def test_valid(self):
        r = validate(_make(pipeline_version="v2.0.0"))
        assert r.valid


# --- batch_id validation ---

class TestBatchIdValidation:
    def test_empty_fails(self):
        r = validate(_make(batch_id=""))
        assert not r.valid
        assert any("batch_id" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(batch_id="  "))
        assert not r.valid

    def test_valid(self):
        r = validate(_make(batch_id="BATCH-999"))
        assert r.valid


# --- experiment_date validation ---

class TestExperimentDateValidation:
    def test_valid_date(self):
        r = validate(_make(experiment_date="2026-01-15"))
        assert r.valid

    def test_invalid_format(self):
        r = validate(_make(experiment_date="10/07/2026"))
        assert not r.valid
        assert any("experiment_date" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(experiment_date=""))
        assert not r.valid

    def test_partial_date_fails(self):
        r = validate(_make(experiment_date="2026-07"))
        assert not r.valid

    def test_text_date_fails(self):
        r = validate(_make(experiment_date="July 2026"))
        assert not r.valid


# --- candidates_tested validation ---

class TestCandidatesTestedValidation:
    def test_zero_fails(self):
        r = validate(_make(candidates_tested=0, candidates_with_results=0))
        assert not r.valid
        assert any("candidates_tested" in e for e in r.errors)

    def test_negative_fails(self):
        r = validate(_make(candidates_tested=-1, candidates_with_results=0))
        assert not r.valid

    def test_one_passes(self):
        r = validate(_make(
            candidates_tested=1,
            candidates_with_results=1,
            observed_active_count=1,
            prediction_hit_rate=1.0,
        ))
        assert r.valid


# --- candidates_with_results validation ---

class TestCandidatesWithResultsValidation:
    def test_zero_fails(self):
        r = validate(_make(candidates_with_results=0))
        assert not r.valid
        assert any("candidates_with_results" in e for e in r.errors)

    def test_exceeds_tested_fails(self):
        r = validate(_make(candidates_tested=5, candidates_with_results=6))
        assert not r.valid
        assert any("exceed" in e for e in r.errors)

    def test_partial_results_valid(self):
        r = validate(_make(
            candidates_tested=10,
            candidates_with_results=8,
            observed_active_count=3,
            prediction_hit_rate=0.375,
        ))
        assert r.valid


# --- observed_active_count validation ---

class TestObservedActiveCountValidation:
    def test_negative_fails(self):
        r = validate(_make(observed_active_count=-1))
        assert not r.valid
        assert any("observed_active_count" in e for e in r.errors)

    def test_exceeds_with_results_fails(self):
        r = validate(_make(
            candidates_with_results=5,
            observed_active_count=6,
            prediction_hit_rate=0.6,
        ))
        assert not r.valid
        assert any("exceed" in e for e in r.errors)

    def test_zero_passes(self):
        r = validate(_make(
            observed_active_count=0,
            prediction_hit_rate=0.0,
            calibration_update_warranted=True,
            calibration_update_rationale="Zero actives; model overestimated.",
        ))
        assert r.valid


# --- prediction_hit_rate validation ---

class TestPredictionHitRateValidation:
    def test_negative_fails(self):
        r = validate(_make(prediction_hit_rate=-0.1))
        assert not r.valid
        assert any("prediction_hit_rate" in e for e in r.errors)

    def test_above_one_fails(self):
        r = validate(_make(prediction_hit_rate=1.1))
        assert not r.valid

    def test_inconsistent_fails(self):
        r = validate(_make(
            candidates_with_results=10,
            observed_active_count=3,
            prediction_hit_rate=0.5,
        ))
        assert not r.valid
        assert any("inconsistent" in e for e in r.errors)

    def test_consistent_passes(self):
        r = validate(_make(
            candidates_with_results=10,
            observed_active_count=4,
            prediction_hit_rate=0.4,
        ))
        assert r.valid

    def test_within_tolerance_passes(self):
        r = validate(_make(
            candidates_with_results=10,
            observed_active_count=3,
            prediction_hit_rate=0.301,
        ))
        assert r.valid


# --- calibration_update_rationale validation ---

class TestRationaleValidation:
    def test_empty_fails(self):
        r = validate(_make(calibration_update_rationale=""))
        assert not r.valid
        assert any("calibration_update_rationale" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(calibration_update_rationale="   "))
        assert not r.valid

    def test_too_long_fails(self):
        r = validate(_make(calibration_update_rationale="x" * (RATIONALE_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("calibration_update_rationale" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(calibration_update_rationale="x" * RATIONALE_MAX_LENGTH))
        assert r.valid

    def test_short_passes(self):
        r = validate(_make(calibration_update_rationale="Hit rate matched predictions."))
        assert r.valid


# --- data_quality_confirmed validation ---

class TestDataQualityValidation:
    def test_false_fails(self):
        r = validate(_make(data_quality_confirmed=False))
        assert not r.valid
        assert any("data_quality_confirmed" in e for e in r.errors)

    def test_true_passes(self):
        r = validate(_make(data_quality_confirmed=True))
        assert r.valid or all("data_quality" not in e for e in r.errors)


# --- notes validation ---

class TestNotesValidation:
    def test_empty_valid(self):
        r = validate(_make(notes=""))
        assert r.valid

    def test_too_long_fails(self):
        r = validate(_make(notes="x" * (NOTES_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("notes" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(notes="x" * NOTES_MAX_LENGTH))
        assert r.valid


# --- Warnings ---

class TestWarnings:
    def test_incomplete_results_warns(self):
        r = validate(_make(
            candidates_tested=10,
            candidates_with_results=8,
            observed_active_count=3,
            prediction_hit_rate=0.375,
        ))
        assert any("no results" in w or "missing" in w or "without results" in w or "have no results" in w for w in r.warnings)

    def test_zero_active_warns(self):
        r = validate(_make(
            observed_active_count=0,
            prediction_hit_rate=0.0,
            calibration_update_warranted=True,
            calibration_update_rationale="Zero actives; model overestimated.",
        ))
        assert any("observed_active_count=0" in w or "no active" in w for w in r.warnings)

    def test_low_hit_rate_no_update_warns(self):
        r = validate(_make(
            observed_active_count=2,
            prediction_hit_rate=0.2,
            calibration_update_warranted=False,
            calibration_update_rationale="Decided against update despite low hit rate.",
        ))
        assert any("low" in w or "calibration_update" in w for w in r.warnings)

    def test_no_warnings_in_clean_entry(self):
        r = validate(_make(notes="clean", calibration_update_warranted=True))
        assert r.warnings == []

    def test_full_results_no_incomplete_warn(self):
        r = validate(_make(candidates_tested=10, candidates_with_results=10))
        assert not any("no results" in w or "missing" in w or "have no results" in w for w in r.warnings)


# --- validate_dict ---

class TestValidateDict:
    def _valid_dict(self, **kwargs):
        d = dict(
            pci_id="PCI-001",
            pipeline_version="v0.10.19",
            batch_id="BATCH-007",
            experiment_date="2026-07-10",
            candidates_tested=10,
            candidates_with_results=10,
            predicted_active_count=4,
            observed_active_count=3,
            prediction_hit_rate=0.3,
            calibration_update_warranted=True,
            calibration_update_rationale="Hit rate 0.30 vs predicted 0.40; update needed.",
            data_quality_confirmed=True,
            notes="",
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_dict(self._valid_dict())
        assert r.valid

    def test_invalid_prefix_fails(self):
        r = validate_dict(self._valid_dict(pci_id="CIR-001"))
        assert not r.valid

    def test_empty_dict_fails(self):
        r = validate_dict({})
        assert not r.valid

    def test_false_data_quality_fails(self):
        r = validate_dict(self._valid_dict(data_quality_confirmed=False))
        assert not r.valid

    def test_inconsistent_hit_rate_fails(self):
        r = validate_dict(self._valid_dict(observed_active_count=3, prediction_hit_rate=0.7))
        assert not r.valid


# --- Constants ---

class TestConstants:
    def test_pci_prefix(self):
        assert PCI_PREFIX == "PCI-"

    def test_hit_rate_tolerance(self):
        assert HIT_RATE_TOLERANCE == 0.01

    def test_rationale_max_length(self):
        assert RATIONALE_MAX_LENGTH == 400

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 300

    def test_low_hit_rate_threshold(self):
        assert LOW_HIT_RATE_THRESHOLD == 0.3
