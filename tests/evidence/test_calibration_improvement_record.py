"""Tests for calibration improvement record schema (Phase O O3)."""
import pytest
from openamp_foundry.evidence.calibration_improvement_record import (
    ACTION_TAKEN_MAX_LENGTH,
    POOR_BRIER_THRESHOLD,
    VALID_ACTION_CATEGORIES,
    VALID_TRIGGER_PREFIXES,
    CalibrationImprovementEntry,
    CalibrationImprovementResult,
    validate_calibration_improvement,
    validate_calibration_improvement_dict,
)


def make_entry(**kwargs) -> CalibrationImprovementEntry:
    defaults = dict(
        improvement_id="CIR-001",
        pipeline_version_before="v1.0.0",
        pipeline_version_after="v1.1.0",
        trigger_ids=["CPS-001"],
        action_taken="Adjusted classification threshold from 0.5 to 0.45.",
        action_category="threshold_adjustment",
        brier_score_before=0.3,
        brier_score_after=0.2,
        improvement_confirmed=True,
        reviewer="alice",
        dry_lab_only=False,
    )
    defaults.update(kwargs)
    return CalibrationImprovementEntry(**defaults)


class TestConstants:
    def test_action_taken_max_length(self):
        assert ACTION_TAKEN_MAX_LENGTH == 500

    def test_poor_brier_threshold(self):
        assert POOR_BRIER_THRESHOLD == 0.25

    def test_valid_action_categories_count(self):
        assert len(VALID_ACTION_CATEGORIES) == 6

    def test_valid_action_categories_contents(self):
        assert "threshold_adjustment" in VALID_ACTION_CATEGORIES
        assert "retraining" in VALID_ACTION_CATEGORIES
        assert "feature_removal" in VALID_ACTION_CATEGORIES
        assert "feature_addition" in VALID_ACTION_CATEGORIES
        assert "data_augmentation" in VALID_ACTION_CATEGORIES
        assert "weighting_change" in VALID_ACTION_CATEGORIES

    def test_valid_trigger_prefixes(self):
        assert "CPS-" in VALID_TRIGGER_PREFIXES
        assert "DRM-" in VALID_TRIGGER_PREFIXES


class TestHappyPath:
    def test_valid_entry_passes(self):
        entry = make_entry()
        result = validate_calibration_improvement(entry)
        assert result.passed
        assert result.errors == []

    def test_result_fields(self):
        entry = make_entry()
        result = validate_calibration_improvement(entry)
        assert result.improvement_id == "CIR-001"
        assert result.pipeline_version_before == "v1.0.0"
        assert result.pipeline_version_after == "v1.1.0"
        assert result.brier_score_before == 0.3
        assert result.brier_score_after == 0.2
        assert result.improvement_confirmed is True
        assert result.dry_lab_only is False

    def test_dry_lab_only_default_false(self):
        entry = CalibrationImprovementEntry(
            improvement_id="CIR-001",
            pipeline_version_before="v1.0",
            pipeline_version_after="v1.1",
            trigger_ids=["CPS-001"],
            action_taken="threshold adjustment",
            action_category="threshold_adjustment",
            brier_score_before=0.3,
            brier_score_after=0.2,
            improvement_confirmed=True,
            reviewer="bob",
        )
        assert entry.dry_lab_only is False

    def test_no_improvement_confirmed_false(self):
        entry = make_entry(
            brier_score_before=0.2,
            brier_score_after=0.3,
            improvement_confirmed=False,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed
        assert result.errors == []

    def test_equal_scores_confirmed_false(self):
        entry = make_entry(
            brier_score_before=0.2,
            brier_score_after=0.2,
            improvement_confirmed=False,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed

    def test_multiple_trigger_ids(self):
        entry = make_entry(trigger_ids=["CPS-001", "DRM-001", "CPS-002"])
        result = validate_calibration_improvement(entry)
        assert result.passed

    def test_drm_trigger_id(self):
        entry = make_entry(trigger_ids=["DRM-001"])
        result = validate_calibration_improvement(entry)
        assert result.passed

    def test_all_action_categories(self):
        for cat in VALID_ACTION_CATEGORIES:
            entry = make_entry(action_category=cat)
            result = validate_calibration_improvement(entry)
            assert result.passed, f"Category {cat} should pass"


class TestImprovementIdValidation:
    def test_wrong_prefix_fails(self):
        entry = make_entry(improvement_id="WRONG-001")
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("CIR-" in e for e in result.errors)

    def test_empty_id_fails(self):
        entry = make_entry(improvement_id="")
        result = validate_calibration_improvement(entry)
        assert not result.passed

    def test_correct_prefix_passes(self):
        entry = make_entry(improvement_id="CIR-XYZ-2026")
        result = validate_calibration_improvement(entry)
        assert result.passed


class TestVersionValidation:
    def test_same_versions_fail(self):
        entry = make_entry(
            pipeline_version_before="v1.0",
            pipeline_version_after="v1.0",
        )
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("differ" in e for e in result.errors)

    def test_different_versions_pass(self):
        entry = make_entry(
            pipeline_version_before="v1.0",
            pipeline_version_after="v1.1",
        )
        result = validate_calibration_improvement(entry)
        assert result.passed


class TestTriggerIdsValidation:
    def test_empty_trigger_ids_fail(self):
        entry = make_entry(trigger_ids=[])
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("trigger_ids" in e for e in result.errors)

    def test_invalid_prefix_trigger_fails(self):
        entry = make_entry(trigger_ids=["WRONG-001"])
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("CPS-" in e or "DRM-" in e for e in result.errors)

    def test_mixed_valid_invalid_trigger_fails(self):
        entry = make_entry(trigger_ids=["CPS-001", "BAD-001"])
        result = validate_calibration_improvement(entry)
        assert not result.passed

    def test_valid_cps_trigger_passes(self):
        entry = make_entry(trigger_ids=["CPS-XYZ"])
        result = validate_calibration_improvement(entry)
        assert result.passed

    def test_valid_drm_trigger_passes(self):
        entry = make_entry(trigger_ids=["DRM-XYZ"])
        result = validate_calibration_improvement(entry)
        assert result.passed


class TestActionTakenValidation:
    def test_too_long_action_fails(self):
        entry = make_entry(action_taken="x" * 501)
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("action_taken" in e for e in result.errors)

    def test_exact_max_length_passes(self):
        entry = make_entry(action_taken="x" * 500)
        result = validate_calibration_improvement(entry)
        assert result.passed

    def test_empty_action_passes(self):
        entry = make_entry(action_taken="")
        result = validate_calibration_improvement(entry)
        assert result.passed


class TestActionCategoryValidation:
    def test_invalid_category_fails(self):
        entry = make_entry(action_category="magic_fix")
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("action_category" in e for e in result.errors)

    def test_empty_category_fails(self):
        entry = make_entry(action_category="")
        result = validate_calibration_improvement(entry)
        assert not result.passed


class TestBrierScoreValidation:
    def test_brier_before_below_zero_fails(self):
        entry = make_entry(brier_score_before=-0.1, improvement_confirmed=False)
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("brier_score_before" in e for e in result.errors)

    def test_brier_before_above_one_fails(self):
        entry = make_entry(brier_score_before=1.1)
        result = validate_calibration_improvement(entry)
        assert not result.passed

    def test_brier_after_below_zero_fails(self):
        entry = make_entry(
            brier_score_after=-0.1,
            improvement_confirmed=False,
        )
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("brier_score_after" in e for e in result.errors)

    def test_brier_after_above_one_fails(self):
        entry = make_entry(brier_score_after=1.1, improvement_confirmed=False)
        result = validate_calibration_improvement(entry)
        assert not result.passed

    def test_brier_zero_values_pass(self):
        entry = make_entry(
            brier_score_before=0.1,
            brier_score_after=0.0,
            improvement_confirmed=True,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed


class TestImprovementConfirmedValidation:
    def test_confirmed_true_but_no_improvement_fails(self):
        entry = make_entry(
            brier_score_before=0.2,
            brier_score_after=0.3,
            improvement_confirmed=True,
        )
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("improvement_confirmed" in e for e in result.errors)

    def test_confirmed_false_but_improved_fails(self):
        entry = make_entry(
            brier_score_before=0.3,
            brier_score_after=0.2,
            improvement_confirmed=False,
        )
        result = validate_calibration_improvement(entry)
        assert not result.passed
        assert any("improvement_confirmed" in e for e in result.errors)

    def test_confirmed_false_equal_scores_passes(self):
        entry = make_entry(
            brier_score_before=0.2,
            brier_score_after=0.2,
            improvement_confirmed=False,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed

    def test_confirmed_true_improved_passes(self):
        entry = make_entry(
            brier_score_before=0.3,
            brier_score_after=0.1,
            improvement_confirmed=True,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed


class TestWarnings:
    def test_poor_brier_after_warns(self):
        entry = make_entry(
            brier_score_before=0.4,
            brier_score_after=0.3,
            improvement_confirmed=True,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed
        assert any("calibration still poor" in w for w in result.warnings)

    def test_good_brier_after_no_warn(self):
        entry = make_entry(
            brier_score_before=0.3,
            brier_score_after=0.1,
            improvement_confirmed=True,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed
        assert not any("calibration still poor" in w for w in result.warnings)

    def test_brier_at_threshold_warns(self):
        entry = make_entry(
            brier_score_before=0.4,
            brier_score_after=0.25,
            improvement_confirmed=True,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed
        assert any("calibration still poor" in w for w in result.warnings)

    def test_brier_just_below_threshold_no_warn(self):
        entry = make_entry(
            brier_score_before=0.3,
            brier_score_after=0.249,
            improvement_confirmed=True,
        )
        result = validate_calibration_improvement(entry)
        assert result.passed
        assert not any("calibration still poor" in w for w in result.warnings)


class TestDictInterface:
    def test_valid_dict_passes(self):
        data = {
            "improvement_id": "CIR-001",
            "pipeline_version_before": "v1.0",
            "pipeline_version_after": "v1.1",
            "trigger_ids": ["CPS-001"],
            "action_taken": "Adjusted threshold.",
            "action_category": "threshold_adjustment",
            "brier_score_before": 0.3,
            "brier_score_after": 0.2,
            "improvement_confirmed": True,
            "reviewer": "alice",
        }
        result = validate_calibration_improvement_dict(data)
        assert result.passed

    def test_missing_field_fails(self):
        data = {"improvement_id": "CIR-001"}
        result = validate_calibration_improvement_dict(data)
        assert not result.passed
        assert any("Missing required field" in e for e in result.errors)

    def test_dict_dry_lab_only_default_false(self):
        data = {
            "improvement_id": "CIR-001",
            "pipeline_version_before": "v1.0",
            "pipeline_version_after": "v1.1",
            "trigger_ids": ["CPS-001"],
            "action_taken": "threshold adjustment",
            "action_category": "threshold_adjustment",
            "brier_score_before": 0.3,
            "brier_score_after": 0.2,
            "improvement_confirmed": True,
            "reviewer": "alice",
        }
        result = validate_calibration_improvement_dict(data)
        assert result.dry_lab_only is False
