"""Tests for prediction drift monitor schema (Phase O O2)."""
import pytest
from openamp_foundry.evidence.prediction_drift_monitor import (
    DRIFT_NOTES_MAX_LENGTH,
    MEAN_SHIFT_TOLERANCE,
    MIN_POPULATION_FOR_RELIABLE_DRIFT,
    SIGNIFICANT_DRIFT_THRESHOLD,
    VARIANCE_EXPLOSION_RATIO,
    PredictionDriftEntry,
    PredictionDriftResult,
    validate_prediction_drift,
    validate_prediction_drift_dict,
)


def make_entry(**kwargs) -> PredictionDriftEntry:
    defaults = dict(
        monitor_id="DRM-001",
        pipeline_version="v1.0.0",
        reference_batch_id="BATCH-REF",
        evaluation_batch_id="BATCH-EVAL",
        reference_mean_score=0.6,
        reference_std_score=0.1,
        evaluation_mean_score=0.65,
        evaluation_std_score=0.12,
        mean_shift_magnitude=0.05,
        population_size_reference=50,
        population_size_evaluation=50,
        drift_flag=False,
        drift_notes="",
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return PredictionDriftEntry(**defaults)


class TestConstants:
    def test_drift_notes_max_length(self):
        assert DRIFT_NOTES_MAX_LENGTH == 400

    def test_mean_shift_tolerance(self):
        assert MEAN_SHIFT_TOLERANCE == 0.001

    def test_significant_drift_threshold(self):
        assert SIGNIFICANT_DRIFT_THRESHOLD == 0.1

    def test_min_population_for_reliable_drift(self):
        assert MIN_POPULATION_FOR_RELIABLE_DRIFT == 10

    def test_variance_explosion_ratio(self):
        assert VARIANCE_EXPLOSION_RATIO == 2.0


class TestHappyPath:
    def test_valid_entry_passes(self):
        entry = make_entry()
        result = validate_prediction_drift(entry)
        assert result.passed
        assert result.errors == []

    def test_result_fields(self):
        entry = make_entry()
        result = validate_prediction_drift(entry)
        assert result.monitor_id == "DRM-001"
        assert result.pipeline_version == "v1.0.0"
        assert result.mean_shift_magnitude == 0.05
        assert result.drift_flag is False
        assert result.dry_lab_only is True

    def test_drift_flag_true_with_notes(self):
        entry = make_entry(
            evaluation_mean_score=0.75,
            mean_shift_magnitude=0.15,
            drift_flag=True,
            drift_notes="Significant drift detected; investigate input distribution.",
        )
        result = validate_prediction_drift(entry)
        assert result.passed
        assert result.errors == []

    def test_zero_mean_scores(self):
        entry = make_entry(
            reference_mean_score=0.0,
            evaluation_mean_score=0.0,
            mean_shift_magnitude=0.0,
        )
        result = validate_prediction_drift(entry)
        assert result.passed

    def test_max_mean_scores(self):
        entry = make_entry(
            reference_mean_score=1.0,
            evaluation_mean_score=1.0,
            mean_shift_magnitude=0.0,
        )
        result = validate_prediction_drift(entry)
        assert result.passed

    def test_dry_lab_only_default_true(self):
        entry = PredictionDriftEntry(
            monitor_id="DRM-002",
            pipeline_version="v1.0",
            reference_batch_id="A",
            evaluation_batch_id="B",
            reference_mean_score=0.5,
            reference_std_score=0.1,
            evaluation_mean_score=0.5,
            evaluation_std_score=0.1,
            mean_shift_magnitude=0.0,
            population_size_reference=20,
            population_size_evaluation=20,
            drift_flag=False,
            drift_notes="",
            reviewer="bob",
        )
        assert entry.dry_lab_only is True


class TestMonitorIdValidation:
    def test_wrong_prefix_fails(self):
        entry = make_entry(monitor_id="WRONG-001")
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("DRM-" in e for e in result.errors)

    def test_empty_prefix_fails(self):
        entry = make_entry(monitor_id="001")
        result = validate_prediction_drift(entry)
        assert not result.passed

    def test_correct_prefix_passes(self):
        entry = make_entry(monitor_id="DRM-XYZ-999")
        result = validate_prediction_drift(entry)
        assert result.passed


class TestBatchIdValidation:
    def test_same_batch_ids_fail(self):
        entry = make_entry(
            reference_batch_id="SAME",
            evaluation_batch_id="SAME",
        )
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("differ" in e for e in result.errors)

    def test_different_batch_ids_pass(self):
        entry = make_entry(
            reference_batch_id="BATCH-A",
            evaluation_batch_id="BATCH-B",
        )
        result = validate_prediction_drift(entry)
        assert result.passed


class TestScoreRangeValidation:
    def test_reference_mean_below_zero_fails(self):
        entry = make_entry(reference_mean_score=-0.1)
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("reference_mean_score" in e for e in result.errors)

    def test_reference_mean_above_one_fails(self):
        entry = make_entry(reference_mean_score=1.1)
        result = validate_prediction_drift(entry)
        assert not result.passed

    def test_evaluation_mean_below_zero_fails(self):
        entry = make_entry(
            evaluation_mean_score=-0.05,
            mean_shift_magnitude=0.65,
        )
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("evaluation_mean_score" in e for e in result.errors)

    def test_evaluation_mean_above_one_fails(self):
        entry = make_entry(evaluation_mean_score=1.05)
        result = validate_prediction_drift(entry)
        assert not result.passed


class TestStdDevValidation:
    def test_negative_reference_std_fails(self):
        entry = make_entry(reference_std_score=-0.1)
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("reference_std_score" in e for e in result.errors)

    def test_negative_evaluation_std_fails(self):
        entry = make_entry(evaluation_std_score=-0.05)
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("evaluation_std_score" in e for e in result.errors)

    def test_zero_std_passes(self):
        entry = make_entry(reference_std_score=0.0, evaluation_std_score=0.0)
        result = validate_prediction_drift(entry)
        assert result.passed


class TestMeanShiftValidation:
    def test_shift_magnitude_mismatch_fails(self):
        entry = make_entry(
            reference_mean_score=0.5,
            evaluation_mean_score=0.7,
            mean_shift_magnitude=0.1,
        )
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("mean_shift_magnitude" in e for e in result.errors)

    def test_shift_within_tolerance_passes(self):
        entry = make_entry(
            reference_mean_score=0.5,
            evaluation_mean_score=0.7,
            mean_shift_magnitude=0.2005,
        )
        result = validate_prediction_drift(entry)
        assert result.passed

    def test_shift_outside_tolerance_fails(self):
        entry = make_entry(
            reference_mean_score=0.5,
            evaluation_mean_score=0.7,
            mean_shift_magnitude=0.202,
        )
        result = validate_prediction_drift(entry)
        assert not result.passed

    def test_zero_shift_passes(self):
        entry = make_entry(
            reference_mean_score=0.5,
            evaluation_mean_score=0.5,
            mean_shift_magnitude=0.0,
        )
        result = validate_prediction_drift(entry)
        assert result.passed


class TestPopulationSizeValidation:
    def test_zero_reference_population_fails(self):
        entry = make_entry(population_size_reference=0)
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("population_size_reference" in e for e in result.errors)

    def test_zero_evaluation_population_fails(self):
        entry = make_entry(population_size_evaluation=0)
        result = validate_prediction_drift(entry)
        assert not result.passed

    def test_one_reference_passes(self):
        entry = make_entry(population_size_reference=1)
        result = validate_prediction_drift(entry)
        assert result.passed

    def test_negative_population_fails(self):
        entry = make_entry(population_size_reference=-1)
        result = validate_prediction_drift(entry)
        assert not result.passed


class TestDriftNotesValidation:
    def test_notes_too_long_fails(self):
        entry = make_entry(drift_notes="x" * 401)
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("drift_notes" in e for e in result.errors)

    def test_notes_exact_max_passes(self):
        entry = make_entry(drift_notes="x" * 400)
        result = validate_prediction_drift(entry)
        assert result.passed

    def test_drift_flag_true_empty_notes_fails(self):
        entry = make_entry(
            evaluation_mean_score=0.75,
            mean_shift_magnitude=0.15,
            drift_flag=True,
            drift_notes="",
        )
        result = validate_prediction_drift(entry)
        assert not result.passed
        assert any("drift_notes" in e for e in result.errors)

    def test_drift_flag_true_whitespace_notes_fails(self):
        entry = make_entry(
            evaluation_mean_score=0.75,
            mean_shift_magnitude=0.15,
            drift_flag=True,
            drift_notes="   ",
        )
        result = validate_prediction_drift(entry)
        assert not result.passed

    def test_drift_flag_false_empty_notes_passes(self):
        entry = make_entry(drift_flag=False, drift_notes="")
        result = validate_prediction_drift(entry)
        assert result.passed


class TestWarnings:
    def test_large_shift_without_flag_warns(self):
        entry = make_entry(
            reference_mean_score=0.5,
            evaluation_mean_score=0.65,
            mean_shift_magnitude=0.15,
            drift_flag=False,
        )
        result = validate_prediction_drift(entry)
        assert result.passed
        assert any("unreported drift" in w for w in result.warnings)

    def test_large_shift_with_flag_no_warn(self):
        entry = make_entry(
            reference_mean_score=0.5,
            evaluation_mean_score=0.65,
            mean_shift_magnitude=0.15,
            drift_flag=True,
            drift_notes="Known distribution shift.",
        )
        result = validate_prediction_drift(entry)
        assert result.passed
        assert not any("unreported drift" in w for w in result.warnings)

    def test_small_reference_population_warns(self):
        entry = make_entry(population_size_reference=5)
        result = validate_prediction_drift(entry)
        assert result.passed
        assert any("population_size_reference" in w for w in result.warnings)

    def test_small_evaluation_population_warns(self):
        entry = make_entry(population_size_evaluation=9)
        result = validate_prediction_drift(entry)
        assert result.passed
        assert any("population_size_evaluation" in w for w in result.warnings)

    def test_variance_explosion_warns(self):
        entry = make_entry(
            reference_std_score=0.1,
            evaluation_std_score=0.25,
        )
        result = validate_prediction_drift(entry)
        assert result.passed
        assert any("variance explosion" in w for w in result.warnings)

    def test_no_variance_explosion_at_exact_ratio(self):
        entry = make_entry(
            reference_std_score=0.1,
            evaluation_std_score=0.2,
        )
        result = validate_prediction_drift(entry)
        assert result.passed
        assert not any("variance explosion" in w for w in result.warnings)

    def test_zero_reference_std_no_variance_explosion(self):
        entry = make_entry(reference_std_score=0.0, evaluation_std_score=0.5)
        result = validate_prediction_drift(entry)
        assert result.passed
        assert not any("variance explosion" in w for w in result.warnings)


class TestDictInterface:
    def test_valid_dict_passes(self):
        data = {
            "monitor_id": "DRM-001",
            "pipeline_version": "v1.0",
            "reference_batch_id": "A",
            "evaluation_batch_id": "B",
            "reference_mean_score": 0.6,
            "reference_std_score": 0.1,
            "evaluation_mean_score": 0.65,
            "evaluation_std_score": 0.12,
            "mean_shift_magnitude": 0.05,
            "population_size_reference": 50,
            "population_size_evaluation": 50,
            "drift_flag": False,
            "drift_notes": "",
            "reviewer": "alice",
        }
        result = validate_prediction_drift_dict(data)
        assert result.passed

    def test_missing_required_field_fails(self):
        data = {
            "monitor_id": "DRM-001",
            "pipeline_version": "v1.0",
        }
        result = validate_prediction_drift_dict(data)
        assert not result.passed
        assert any("Missing required field" in e for e in result.errors)

    def test_dict_dry_lab_only_default(self):
        data = {
            "monitor_id": "DRM-001",
            "pipeline_version": "v1.0",
            "reference_batch_id": "A",
            "evaluation_batch_id": "B",
            "reference_mean_score": 0.6,
            "reference_std_score": 0.1,
            "evaluation_mean_score": 0.65,
            "evaluation_std_score": 0.12,
            "mean_shift_magnitude": 0.05,
            "population_size_reference": 50,
            "population_size_evaluation": 50,
            "drift_flag": False,
            "drift_notes": "",
            "reviewer": "alice",
        }
        result = validate_prediction_drift_dict(data)
        assert result.dry_lab_only is True
