"""Tests for uncertainty quantification report schema (Phase K K5)."""

import pytest
from openamp_foundry.evidence.uncertainty_report import (
    VALID_METRIC_NAMES,
    WIDE_INTERVAL_THRESHOLD,
    UncertaintyReportEntry,
    UncertaintyReportResult,
    validate_uncertainty_report,
    validate_uncertainty_report_dict,
)


def _valid_entry(**kwargs) -> UncertaintyReportEntry:
    defaults = dict(
        report_id="UQ-001",
        batch_id="BATCH-001",
        candidate_id="AMP-001",
        pipeline_version="0.8.3",
        metric_name="mic",
        point_estimate=4.0,
        lower_bound=2.0,
        upper_bound=8.0,
        confidence_level=0.90,
        calibration_source="historical_holdout_v2",
        reviewer="alice",
        dry_lab_only=True,
    )
    defaults.update(kwargs)
    return UncertaintyReportEntry(**defaults)


# ── Constants ────────────────────────────────────────────────────────────────


def test_valid_metric_names_contains_mic():
    assert "mic" in VALID_METRIC_NAMES


def test_valid_metric_names_contains_hemolysis():
    assert "hemolysis_fraction" in VALID_METRIC_NAMES


def test_wide_interval_threshold_is_10():
    assert WIDE_INTERVAL_THRESHOLD == 10.0


# ── Valid entry ───────────────────────────────────────────────────────────────


def test_valid_entry_passes():
    result = validate_uncertainty_report(_valid_entry())
    assert result.passed
    assert result.errors == []


def test_result_dry_lab_only_true():
    result = validate_uncertainty_report(_valid_entry())
    assert result.dry_lab_only is True


def test_result_interval_width_computed():
    result = validate_uncertainty_report(_valid_entry(lower_bound=2.0, upper_bound=8.0))
    assert result.interval_width == pytest.approx(6.0)


def test_result_fields_match():
    result = validate_uncertainty_report(_valid_entry())
    assert result.report_id == "UQ-001"
    assert result.candidate_id == "AMP-001"


def test_valid_all_metric_names():
    for metric in VALID_METRIC_NAMES:
        result = validate_uncertainty_report(_valid_entry(metric_name=metric))
        assert result.passed, f"metric_name '{metric}' should be valid"


def test_valid_point_estimate_equals_bounds():
    result = validate_uncertainty_report(
        _valid_entry(point_estimate=5.0, lower_bound=5.0, upper_bound=5.0)
    )
    assert result.passed


def test_valid_negative_point_estimate():
    result = validate_uncertainty_report(
        _valid_entry(point_estimate=-2.0, lower_bound=-4.0, upper_bound=-1.0)
    )
    assert result.passed


# ── report_id validation ──────────────────────────────────────────────────────


def test_report_id_missing_prefix_fails():
    result = validate_uncertainty_report(_valid_entry(report_id="001"))
    assert not result.passed
    assert any("UQ-" in e for e in result.errors)


def test_report_id_wrong_prefix_fails():
    result = validate_uncertainty_report(_valid_entry(report_id="CAL-001"))
    assert not result.passed


def test_report_id_correct_prefix_passes():
    result = validate_uncertainty_report(_valid_entry(report_id="UQ-XYZ-99"))
    assert result.passed


# ── metric_name validation ────────────────────────────────────────────────────


def test_invalid_metric_name_fails():
    result = validate_uncertainty_report(_valid_entry(metric_name="unknown_metric"))
    assert not result.passed
    assert any("metric_name" in e for e in result.errors)


# ── bounds validation ─────────────────────────────────────────────────────────


def test_lower_bound_above_point_estimate_fails():
    result = validate_uncertainty_report(
        _valid_entry(point_estimate=4.0, lower_bound=5.0, upper_bound=8.0)
    )
    assert not result.passed
    assert any("lower_bound" in e for e in result.errors)


def test_upper_bound_below_point_estimate_fails():
    result = validate_uncertainty_report(
        _valid_entry(point_estimate=4.0, lower_bound=2.0, upper_bound=3.0)
    )
    assert not result.passed
    assert any("upper_bound" in e for e in result.errors)


# ── confidence_level validation ───────────────────────────────────────────────


def test_confidence_above_1_fails():
    result = validate_uncertainty_report(_valid_entry(confidence_level=1.1))
    assert not result.passed


def test_confidence_negative_fails():
    result = validate_uncertainty_report(_valid_entry(confidence_level=-0.1))
    assert not result.passed


def test_confidence_0_passes():
    result = validate_uncertainty_report(_valid_entry(confidence_level=0.0))
    assert result.passed


def test_confidence_1_passes():
    result = validate_uncertainty_report(_valid_entry(confidence_level=1.0))
    assert result.passed


# ── dry_lab_only constraint ───────────────────────────────────────────────────


def test_dry_lab_only_false_fails():
    result = validate_uncertainty_report(_valid_entry(dry_lab_only=False))
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)


# ── warnings ─────────────────────────────────────────────────────────────────


def test_wide_interval_warns():
    result = validate_uncertainty_report(
        _valid_entry(lower_bound=0.0, upper_bound=15.0, point_estimate=7.0)
    )
    assert result.passed
    assert any("width" in w or "threshold" in w for w in result.warnings)


def test_narrow_interval_no_warning():
    result = validate_uncertainty_report(
        _valid_entry(lower_bound=3.5, upper_bound=4.5, point_estimate=4.0)
    )
    assert result.passed
    assert not any("width" in w for w in result.warnings)


def test_low_confidence_warns():
    result = validate_uncertainty_report(_valid_entry(confidence_level=0.70))
    assert result.passed
    assert any("0.80" in w or "unreliable" in w for w in result.warnings)


def test_very_high_confidence_warns():
    result = validate_uncertainty_report(_valid_entry(confidence_level=1.0))
    assert result.passed
    assert any("0.99" in w or "overfitting" in w for w in result.warnings)


def test_normal_confidence_no_warning():
    result = validate_uncertainty_report(_valid_entry(confidence_level=0.90))
    assert result.passed
    assert result.warnings == []


# ── dict interface ────────────────────────────────────────────────────────────


def test_dict_valid_passes():
    d = dict(
        report_id="UQ-D01",
        batch_id="BATCH-D01",
        candidate_id="AMP-D01",
        pipeline_version="0.8.3",
        metric_name="mic",
        point_estimate=4.0,
        lower_bound=2.0,
        upper_bound=8.0,
        confidence_level=0.90,
        calibration_source="historical_holdout_v2",
        reviewer="alice",
        dry_lab_only=True,
    )
    result = validate_uncertainty_report_dict(d)
    assert result.passed


def test_dict_missing_field_fails():
    d = dict(
        report_id="UQ-D02",
        batch_id="BATCH-D02",
        candidate_id="AMP-D02",
        pipeline_version="0.8.3",
        metric_name="mic",
        point_estimate=4.0,
        lower_bound=2.0,
        upper_bound=8.0,
        confidence_level=0.90,
        # missing calibration_source
        reviewer="alice",
    )
    result = validate_uncertainty_report_dict(d)
    assert not result.passed
    assert any("calibration_source" in e for e in result.errors)


def test_dict_dry_lab_only_defaults_true():
    d = dict(
        report_id="UQ-D03",
        batch_id="BATCH-D03",
        candidate_id="AMP-D03",
        pipeline_version="0.8.3",
        metric_name="mic",
        point_estimate=4.0,
        lower_bound=2.0,
        upper_bound=8.0,
        confidence_level=0.90,
        calibration_source="holdout_v1",
        reviewer="alice",
    )
    result = validate_uncertainty_report_dict(d)
    assert result.passed
    assert result.dry_lab_only is True
