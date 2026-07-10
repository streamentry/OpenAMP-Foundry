"""Tests for simulation uncertainty calibration report schema (Phase H H6).

5 test classes, 63 tests total.
"""

import pytest

from openamp_foundry.simulation.uncertainty_calibration_report import (
    CALIBRATION_ERROR_TOLERANCE,
    MIN_SAMPLES_FOR_CALIBRATION,
    OVERCONFIDENCE_THRESHOLD,
    SIMULATION_UNCERTAINTY_CALIBRATION_REPORT_ID_PREFIX,
    UNDERCONFIDENCE_THRESHOLD,
    VALID_CALIBRATION_METHODS,
    VALID_SIMULATION_MODULES,
    VALID_UNCERTAINTY_ASSESSMENT_STATUSES,
    SimulationUncertaintyCalibrationReport,
    format_uncertainty_calibration_report,
    validate_uncertainty_calibration_report,
)


def _valid_report(**kwargs) -> SimulationUncertaintyCalibrationReport:
    defaults = dict(
        report_id="SUC-001",
        module_id="MEM-001",
        simulation_module="membrane_proxy",
        calibration_method="empirical_coverage_only",
        n_samples=50,
        expected_coverage=0.80,
        empirical_coverage=0.82,
        calibration_error=0.02,
        uncertainty_assessment_status="well_calibrated",
        overconfidence_flag=False,
        dry_lab_only=True,
        cheap_baseline_beats_module=None,
        notes="Routine calibration check",
        created_at="2026-01-01",
    )
    defaults.update(kwargs)
    return SimulationUncertaintyCalibrationReport(**defaults)


# ---------------------------------------------------------------------------
# Class 1: Constants (10 tests)
# ---------------------------------------------------------------------------

class TestSimulationUncertaintyCalibrationReportConstants:
    def test_prefix_value(self):
        assert SIMULATION_UNCERTAINTY_CALIBRATION_REPORT_ID_PREFIX == "SUC-"

    def test_overconfidence_threshold_positive(self):
        assert OVERCONFIDENCE_THRESHOLD > 0.0

    def test_underconfidence_threshold_positive(self):
        assert UNDERCONFIDENCE_THRESHOLD > 0.0

    def test_min_samples_positive(self):
        assert MIN_SAMPLES_FOR_CALIBRATION > 0

    def test_calibration_error_tolerance_small(self):
        assert CALIBRATION_ERROR_TOLERANCE < 0.1

    def test_valid_simulation_modules_nonempty(self):
        assert len(VALID_SIMULATION_MODULES) >= 5

    def test_valid_calibration_methods_nonempty(self):
        assert len(VALID_CALIBRATION_METHODS) >= 4

    def test_valid_assessment_statuses_nonempty(self):
        assert len(VALID_UNCERTAINTY_ASSESSMENT_STATUSES) >= 4

    def test_membrane_proxy_in_modules(self):
        assert "membrane_proxy" in VALID_SIMULATION_MODULES

    def test_none_applied_in_calibration_methods(self):
        assert "none_applied" in VALID_CALIBRATION_METHODS


# ---------------------------------------------------------------------------
# Class 2: Validation happy and sad paths (20 tests)
# ---------------------------------------------------------------------------

class TestValidateSimulationUncertaintyCalibrationReport:
    def test_valid_report_has_no_errors(self):
        r = _valid_report()
        assert validate_uncertainty_calibration_report(r) == []

    def test_bad_prefix_rejected(self):
        r = _valid_report(report_id="BAD-001")
        errs = validate_uncertainty_calibration_report(r)
        assert any("report_id" in e for e in errs)

    def test_invalid_simulation_module_rejected(self):
        r = _valid_report(simulation_module="unknown_module")
        errs = validate_uncertainty_calibration_report(r)
        assert any("simulation_module" in e for e in errs)

    def test_invalid_calibration_method_rejected(self):
        r = _valid_report(calibration_method="magic_method")
        errs = validate_uncertainty_calibration_report(r)
        assert any("calibration_method" in e for e in errs)

    def test_invalid_assessment_status_rejected(self):
        r = _valid_report(uncertainty_assessment_status="great")
        errs = validate_uncertainty_calibration_report(r)
        assert any("uncertainty_assessment_status" in e for e in errs)

    def test_expected_coverage_above_one_rejected(self):
        r = _valid_report(expected_coverage=1.5, empirical_coverage=0.8,
                          calibration_error=0.7)
        errs = validate_uncertainty_calibration_report(r)
        assert any("expected_coverage" in e for e in errs)

    def test_expected_coverage_below_zero_rejected(self):
        r = _valid_report(expected_coverage=-0.1, empirical_coverage=0.8,
                          calibration_error=0.9)
        errs = validate_uncertainty_calibration_report(r)
        assert any("expected_coverage" in e for e in errs)

    def test_empirical_coverage_above_one_rejected(self):
        r = _valid_report(empirical_coverage=1.1, calibration_error=0.3)
        errs = validate_uncertainty_calibration_report(r)
        assert any("empirical_coverage" in e for e in errs)

    def test_calibration_error_mismatch_rejected(self):
        r = _valid_report(expected_coverage=0.80, empirical_coverage=0.82,
                          calibration_error=0.99)
        errs = validate_uncertainty_calibration_report(r)
        assert any("calibration_error" in e for e in errs)

    def test_insufficient_samples_requires_status(self):
        r = _valid_report(
            n_samples=5,
            uncertainty_assessment_status="well_calibrated",
        )
        errs = validate_uncertainty_calibration_report(r)
        assert any("insufficient_data" in e for e in errs)

    def test_insufficient_samples_with_correct_status_ok(self):
        r = _valid_report(
            n_samples=5,
            uncertainty_assessment_status="insufficient_data",
        )
        errs = validate_uncertainty_calibration_report(r)
        assert not any("insufficient_data" in e for e in errs)

    def test_dry_lab_only_false_rejected(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_uncertainty_calibration_report(r)
        assert any("dry_lab_only" in e for e in errs)

    def test_overconfidence_flag_must_be_true_when_coverage_low(self):
        low_coverage = 0.80 - OVERCONFIDENCE_THRESHOLD - 0.05
        err = abs(0.80 - low_coverage)
        r = _valid_report(
            expected_coverage=0.80,
            empirical_coverage=low_coverage,
            calibration_error=round(err, 4),
            uncertainty_assessment_status="overconfident",
            overconfidence_flag=False,
        )
        errs = validate_uncertainty_calibration_report(r)
        assert any("overconfidence_flag" in e for e in errs)

    def test_overconfidence_flag_true_when_coverage_low_passes(self):
        low_coverage = 0.80 - OVERCONFIDENCE_THRESHOLD - 0.05
        err = abs(0.80 - low_coverage)
        r = _valid_report(
            expected_coverage=0.80,
            empirical_coverage=low_coverage,
            calibration_error=round(err, 4),
            uncertainty_assessment_status="overconfident",
            overconfidence_flag=True,
        )
        errs = validate_uncertainty_calibration_report(r)
        assert not any("overconfidence_flag" in e for e in errs)

    def test_blank_module_id_rejected(self):
        r = _valid_report(module_id="   ")
        errs = validate_uncertainty_calibration_report(r)
        assert any("module_id" in e for e in errs)

    def test_blank_created_at_rejected(self):
        r = _valid_report(created_at="")
        errs = validate_uncertainty_calibration_report(r)
        assert any("created_at" in e for e in errs)

    def test_all_simulation_modules_valid(self):
        for mod in VALID_SIMULATION_MODULES:
            r = _valid_report(simulation_module=mod)
            errs = validate_uncertainty_calibration_report(r)
            assert not any("simulation_module" in e for e in errs), mod

    def test_all_calibration_methods_valid(self):
        for method in VALID_CALIBRATION_METHODS:
            r = _valid_report(calibration_method=method)
            errs = validate_uncertainty_calibration_report(r)
            assert not any("calibration_method" in e for e in errs), method

    def test_all_assessment_statuses_valid_with_sufficient_samples(self):
        for status in VALID_UNCERTAINTY_ASSESSMENT_STATUSES:
            if status == "insufficient_data":
                continue
            r = _valid_report(uncertainty_assessment_status=status)
            errs = validate_uncertainty_calibration_report(r)
            assert not any("uncertainty_assessment_status" in e for e in errs), status

    def test_calibration_error_within_tolerance_passes(self):
        r = _valid_report(
            expected_coverage=0.80,
            empirical_coverage=0.805,
            calibration_error=0.005,
        )
        errs = validate_uncertainty_calibration_report(r)
        assert not any("calibration_error" in e for e in errs)


# ---------------------------------------------------------------------------
# Class 3: Edge cases (13 tests)
# ---------------------------------------------------------------------------

class TestSimulationUncertaintyCalibrationReportEdgeCases:
    def test_zero_calibration_error_perfect_calibration(self):
        r = _valid_report(
            expected_coverage=0.80,
            empirical_coverage=0.80,
            calibration_error=0.0,
        )
        assert validate_uncertainty_calibration_report(r) == []

    def test_exactly_min_samples_ok(self):
        r = _valid_report(n_samples=MIN_SAMPLES_FOR_CALIBRATION)
        assert validate_uncertainty_calibration_report(r) == []

    def test_one_below_min_samples_requires_insufficient(self):
        r = _valid_report(
            n_samples=MIN_SAMPLES_FOR_CALIBRATION - 1,
            uncertainty_assessment_status="well_calibrated",
        )
        errs = validate_uncertainty_calibration_report(r)
        assert any("insufficient_data" in e for e in errs)

    def test_cheap_baseline_beats_module_none_ok(self):
        r = _valid_report(cheap_baseline_beats_module=None)
        assert validate_uncertainty_calibration_report(r) == []

    def test_cheap_baseline_beats_module_true_ok(self):
        r = _valid_report(cheap_baseline_beats_module=True)
        assert validate_uncertainty_calibration_report(r) == []

    def test_cheap_baseline_beats_module_false_ok(self):
        r = _valid_report(cheap_baseline_beats_module=False)
        assert validate_uncertainty_calibration_report(r) == []

    def test_expected_coverage_zero_valid(self):
        r = _valid_report(
            expected_coverage=0.0,
            empirical_coverage=0.0,
            calibration_error=0.0,
        )
        assert validate_uncertainty_calibration_report(r) == []

    def test_expected_coverage_one_valid(self):
        r = _valid_report(
            expected_coverage=1.0,
            empirical_coverage=1.0,
            calibration_error=0.0,
        )
        assert validate_uncertainty_calibration_report(r) == []

    def test_not_assessed_status_ok_with_sufficient_samples(self):
        r = _valid_report(uncertainty_assessment_status="not_assessed")
        assert validate_uncertainty_calibration_report(r) == []

    def test_underconfident_status_ok_when_coverage_high(self):
        r = _valid_report(
            expected_coverage=0.70,
            empirical_coverage=0.95,
            calibration_error=0.25,
            uncertainty_assessment_status="underconfident",
            overconfidence_flag=False,
        )
        assert validate_uncertainty_calibration_report(r) == []

    def test_empty_notes_ok(self):
        r = _valid_report(notes="")
        assert validate_uncertainty_calibration_report(r) == []

    def test_overconfidence_exactly_at_threshold_no_flag_required(self):
        threshold_coverage = 0.80 - OVERCONFIDENCE_THRESHOLD
        err = abs(0.80 - threshold_coverage)
        r = _valid_report(
            expected_coverage=0.80,
            empirical_coverage=threshold_coverage,
            calibration_error=round(err, 4),
            uncertainty_assessment_status="overconfident",
            overconfidence_flag=False,
        )
        errs = validate_uncertainty_calibration_report(r)
        assert not any("overconfidence_flag" in e for e in errs)

    def test_prefix_case_sensitive(self):
        r = _valid_report(report_id="suc-001")
        errs = validate_uncertainty_calibration_report(r)
        assert any("report_id" in e for e in errs)


# ---------------------------------------------------------------------------
# Class 4: Format output (10 tests)
# ---------------------------------------------------------------------------

class TestFormatSimulationUncertaintyCalibrationReport:
    def test_format_contains_report_id(self):
        r = _valid_report()
        out = format_uncertainty_calibration_report(r)
        assert "SUC-001" in out

    def test_format_contains_module_id(self):
        r = _valid_report()
        out = format_uncertainty_calibration_report(r)
        assert "MEM-001" in out

    def test_format_contains_expected_coverage(self):
        r = _valid_report()
        out = format_uncertainty_calibration_report(r)
        assert "80.0%" in out or "80%" in out

    def test_format_contains_empirical_coverage(self):
        r = _valid_report()
        out = format_uncertainty_calibration_report(r)
        assert "82.0%" in out or "82%" in out

    def test_format_contains_assessment_status(self):
        r = _valid_report()
        out = format_uncertainty_calibration_report(r)
        assert "well_calibrated" in out

    def test_format_overconfidence_warning_when_flag_true(self):
        r = _valid_report(overconfidence_flag=True)
        out = format_uncertainty_calibration_report(r)
        assert "over-confident" in out.lower() or "overconfident" in out.lower() or "WARNING" in out

    def test_format_baseline_beats_note_when_true(self):
        r = _valid_report(cheap_baseline_beats_module=True)
        out = format_uncertainty_calibration_report(r)
        assert "baseline" in out.lower()

    def test_format_baseline_none_note(self):
        r = _valid_report(cheap_baseline_beats_module=None)
        out = format_uncertainty_calibration_report(r)
        assert "not yet assessed" in out.lower() or "none" in out.lower() or "baseline" in out.lower()

    def test_format_contains_dry_lab_only(self):
        r = _valid_report()
        out = format_uncertainty_calibration_report(r)
        assert "True" in out

    def test_format_is_string(self):
        r = _valid_report()
        out = format_uncertainty_calibration_report(r)
        assert isinstance(out, str)
        assert len(out) > 50


# ---------------------------------------------------------------------------
# Class 5: Dry-lab enforcement (10 tests)
# ---------------------------------------------------------------------------

class TestSimulationUncertaintyCalibrationReportDryLabEnforcement:
    def test_dry_lab_only_true_required(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_uncertainty_calibration_report(r)
        assert len(errs) >= 1

    def test_dry_lab_only_true_passes(self):
        r = _valid_report(dry_lab_only=True)
        assert validate_uncertainty_calibration_report(r) == []

    def test_error_message_mentions_dry_lab(self):
        r = _valid_report(dry_lab_only=False)
        errs = validate_uncertainty_calibration_report(r)
        assert any("dry_lab" in e for e in errs)

    def test_all_modules_enforce_dry_lab(self):
        for mod in list(VALID_SIMULATION_MODULES)[:3]:
            r = _valid_report(simulation_module=mod, dry_lab_only=False)
            errs = validate_uncertainty_calibration_report(r)
            assert any("dry_lab" in e for e in errs), mod

    def test_format_shows_dry_lab_true(self):
        r = _valid_report(dry_lab_only=True)
        out = format_uncertainty_calibration_report(r)
        assert "True" in out

    def test_suc_prefix_is_mandatory(self):
        r = _valid_report(report_id="UCR-001")
        errs = validate_uncertainty_calibration_report(r)
        assert any("SUC-" in e for e in errs)

    def test_well_calibrated_near_zero_error(self):
        r = _valid_report(
            expected_coverage=0.90,
            empirical_coverage=0.91,
            calibration_error=0.01,
            uncertainty_assessment_status="well_calibrated",
        )
        assert validate_uncertainty_calibration_report(r) == []

    def test_n_samples_large_ok(self):
        r = _valid_report(n_samples=1000)
        assert validate_uncertainty_calibration_report(r) == []

    def test_notes_with_special_chars_ok(self):
        r = _valid_report(notes="Module tested on TOY-001 to TOY-005; all dry-lab only.")
        assert validate_uncertainty_calibration_report(r) == []

    def test_isotonic_regression_calibration_method_ok(self):
        r = _valid_report(calibration_method="isotonic_regression")
        assert validate_uncertainty_calibration_report(r) == []
