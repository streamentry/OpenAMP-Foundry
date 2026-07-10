"""Tests for CalibrationImprovementRecord (CIR-) schema — Phase O O3."""

import pytest
from openamp_foundry.evidence.calibration_improvement_record import (
    CIR_PREFIX,
    HIGHER_IS_BETTER,
    LOWER_IS_BETTER,
    MINIMUM_MEANINGFUL_IMPROVEMENT,
    NOTES_MAX_LENGTH,
    RATIONALE_MAX_LENGTH,
    VALID_METRIC_NAMES,
    CalibrationImprovementRecord,
    CalibrationImprovementRecordResult,
    validate,
    validate_dict,
)


def _make(**kwargs) -> CalibrationImprovementRecord:
    defaults = dict(
        cir_id="CIR-001",
        pipeline_version="v0.10.18",
        calibration_version_before="cal-v1.0",
        calibration_version_after="cal-v1.1",
        improvement_date="2026-07-10",
        metric_name="auroc",
        metric_value_before=0.72,
        metric_value_after=0.79,
        improvement_confirmed=True,
        improvement_rationale="Added 5 real outcomes from Batch-3; AUROC improved from 0.72 to 0.79.",
        data_source_id="BATCH-003",
        notes="",
    )
    defaults.update(kwargs)
    return CalibrationImprovementRecord(**defaults)


# --- Baseline valid ---

class TestValidBaseline:
    def test_valid_record_passes(self):
        r = validate(_make())
        assert r.valid
        assert r.errors == []

    def test_valid_returns_result_type(self):
        r = validate(_make())
        assert isinstance(r, CalibrationImprovementRecordResult)

    def test_valid_with_notes(self):
        r = validate(_make(notes="Reviewed by calibration team."))
        assert r.valid

    def test_valid_lower_is_better_metric(self):
        r = validate(_make(
            metric_name="brier_score",
            metric_value_before=0.35,
            metric_value_after=0.28,
        ))
        assert r.valid

    def test_valid_all_higher_is_better_metrics(self):
        for metric in HIGHER_IS_BETTER:
            r = validate(_make(metric_name=metric, metric_value_before=0.6, metric_value_after=0.7))
            assert r.valid or all("metric_name" not in e for e in r.errors)

    def test_valid_all_lower_is_better_metrics(self):
        for metric in LOWER_IS_BETTER:
            r = validate(_make(metric_name=metric, metric_value_before=0.4, metric_value_after=0.3))
            assert r.valid or all("metric_name" not in e for e in r.errors)


# --- cir_id validation ---

class TestCirIdValidation:
    def test_wrong_prefix(self):
        r = validate(_make(cir_id="BSP-001"))
        assert not r.valid
        assert any("cir_id" in e for e in r.errors)

    def test_empty_id(self):
        r = validate(_make(cir_id=""))
        assert not r.valid

    def test_lowercase_prefix(self):
        r = validate(_make(cir_id="cir-001"))
        assert not r.valid

    def test_valid_prefix(self):
        r = validate(_make(cir_id="CIR-999"))
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


# --- calibration_version validation ---

class TestCalibrationVersionValidation:
    def test_empty_before_fails(self):
        r = validate(_make(calibration_version_before=""))
        assert not r.valid
        assert any("calibration_version_before" in e for e in r.errors)

    def test_empty_after_fails(self):
        r = validate(_make(calibration_version_after=""))
        assert not r.valid
        assert any("calibration_version_after" in e for e in r.errors)

    def test_same_versions_fail(self):
        r = validate(_make(
            calibration_version_before="cal-v1.0",
            calibration_version_after="cal-v1.0",
        ))
        assert not r.valid
        assert any("must differ" in e for e in r.errors)

    def test_whitespace_before_fails(self):
        r = validate(_make(calibration_version_before="   "))
        assert not r.valid

    def test_whitespace_after_fails(self):
        r = validate(_make(calibration_version_after="  "))
        assert not r.valid

    def test_different_versions_pass(self):
        r = validate(_make(calibration_version_before="v1.0", calibration_version_after="v1.1"))
        assert r.valid


# --- improvement_date validation ---

class TestImprovementDateValidation:
    def test_valid_date(self):
        r = validate(_make(improvement_date="2026-01-15"))
        assert r.valid

    def test_invalid_format(self):
        r = validate(_make(improvement_date="15/01/2026"))
        assert not r.valid
        assert any("improvement_date" in e for e in r.errors)

    def test_empty_fails(self):
        r = validate(_make(improvement_date=""))
        assert not r.valid

    def test_partial_date_fails(self):
        r = validate(_make(improvement_date="2026-07"))
        assert not r.valid

    def test_text_date_fails(self):
        r = validate(_make(improvement_date="July 2026"))
        assert not r.valid


# --- metric_name validation ---

class TestMetricNameValidation:
    def test_invalid_metric(self):
        r = validate(_make(metric_name="unknown_metric"))
        assert not r.valid
        assert any("metric_name" in e for e in r.errors)

    def test_empty_metric(self):
        r = validate(_make(metric_name=""))
        assert not r.valid

    def test_all_valid_metrics(self):
        for m in VALID_METRIC_NAMES:
            r = validate(_make(metric_name=m, metric_value_before=0.5, metric_value_after=0.6))
            assert not any("metric_name" in e for e in r.errors)


# --- improvement_confirmed validation ---

class TestImprovementConfirmedValidation:
    def test_false_fails(self):
        r = validate(_make(improvement_confirmed=False))
        assert not r.valid
        assert any("improvement_confirmed" in e for e in r.errors)

    def test_true_passes(self):
        r = validate(_make(improvement_confirmed=True))
        assert r.valid or all("improvement_confirmed" not in e for e in r.errors)


# --- improvement_rationale validation ---

class TestImprovementRationaleValidation:
    def test_empty_fails(self):
        r = validate(_make(improvement_rationale=""))
        assert not r.valid
        assert any("improvement_rationale" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(improvement_rationale="   "))
        assert not r.valid

    def test_too_long_fails(self):
        r = validate(_make(improvement_rationale="x" * (RATIONALE_MAX_LENGTH + 1)))
        assert not r.valid
        assert any("improvement_rationale" in e for e in r.errors)

    def test_at_max_passes(self):
        r = validate(_make(improvement_rationale="x" * RATIONALE_MAX_LENGTH))
        assert r.valid

    def test_short_passes(self):
        r = validate(_make(improvement_rationale="AUROC improved after adding 5 real outcomes."))
        assert r.valid


# --- data_source_id validation ---

class TestDataSourceIdValidation:
    def test_empty_fails(self):
        r = validate(_make(data_source_id=""))
        assert not r.valid
        assert any("data_source_id" in e for e in r.errors)

    def test_whitespace_fails(self):
        r = validate(_make(data_source_id="   "))
        assert not r.valid

    def test_valid(self):
        r = validate(_make(data_source_id="BATCH-007"))
        assert r.valid


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
    def test_higher_is_better_wrong_direction_warns(self):
        r = validate(_make(
            metric_name="auroc",
            metric_value_before=0.80,
            metric_value_after=0.75,
        ))
        assert any("higher-is-better" in w or "genuine improvement" in w for w in r.warnings)

    def test_lower_is_better_wrong_direction_warns(self):
        r = validate(_make(
            metric_name="brier_score",
            metric_value_before=0.25,
            metric_value_after=0.30,
        ))
        assert any("lower-is-better" in w or "genuine improvement" in w for w in r.warnings)

    def test_very_small_improvement_warns(self):
        r = validate(_make(
            metric_name="auroc",
            metric_value_before=0.700,
            metric_value_after=0.702,
        ))
        assert any("very small" in w or "meaningful" in w for w in r.warnings)

    def test_empty_notes_warns(self):
        r = validate(_make(notes=""))
        assert any("notes" in w or "context" in w for w in r.warnings)

    def test_no_warnings_in_clean_entry(self):
        r = validate(_make(notes="Reviewed by calibration team.", metric_value_before=0.70, metric_value_after=0.79))
        assert r.warnings == []

    def test_good_lower_is_better_no_direction_warn(self):
        r = validate(_make(
            metric_name="brier_score",
            metric_value_before=0.40,
            metric_value_after=0.30,
            notes="Brier score improved."
        ))
        assert not any("genuine improvement" in w for w in r.warnings)


# --- validate_dict ---

class TestValidateDict:
    def _valid_dict(self, **kwargs):
        d = dict(
            cir_id="CIR-001",
            pipeline_version="v0.10.18",
            calibration_version_before="cal-v1.0",
            calibration_version_after="cal-v1.1",
            improvement_date="2026-07-10",
            metric_name="auroc",
            metric_value_before=0.72,
            metric_value_after=0.79,
            improvement_confirmed=True,
            improvement_rationale="AUROC improved from 0.72 to 0.79 after adding batch data.",
            data_source_id="BATCH-003",
            notes="",
        )
        d.update(kwargs)
        return d

    def test_valid_dict_passes(self):
        r = validate_dict(self._valid_dict())
        assert r.valid

    def test_invalid_prefix_fails(self):
        r = validate_dict(self._valid_dict(cir_id="BSP-001"))
        assert not r.valid

    def test_empty_dict_fails(self):
        r = validate_dict({})
        assert not r.valid

    def test_false_confirmed_fails(self):
        r = validate_dict(self._valid_dict(improvement_confirmed=False))
        assert not r.valid

    def test_same_versions_fails(self):
        r = validate_dict(self._valid_dict(
            calibration_version_before="v1.0",
            calibration_version_after="v1.0",
        ))
        assert not r.valid


# --- Constants ---

class TestConstants:
    def test_cir_prefix(self):
        assert CIR_PREFIX == "CIR-"

    def test_valid_metrics_count(self):
        assert len(VALID_METRIC_NAMES) == 8

    def test_higher_is_better_count(self):
        assert len(HIGHER_IS_BETTER) == 5

    def test_lower_is_better_count(self):
        assert len(LOWER_IS_BETTER) == 3

    def test_higher_lower_disjoint(self):
        assert HIGHER_IS_BETTER.isdisjoint(LOWER_IS_BETTER)

    def test_all_metrics_classified(self):
        assert VALID_METRIC_NAMES == HIGHER_IS_BETTER | LOWER_IS_BETTER

    def test_rationale_max_length(self):
        assert RATIONALE_MAX_LENGTH == 400

    def test_notes_max_length(self):
        assert NOTES_MAX_LENGTH == 300

    def test_minimum_meaningful_improvement(self):
        assert MINIMUM_MEANINGFUL_IMPROVEMENT == 0.005
