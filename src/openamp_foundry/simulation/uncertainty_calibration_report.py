"""Simulation uncertainty calibration report schema (Phase H H6).

SUC- records track whether a simulation module's uncertainty estimates
are well-calibrated — i.e. whether a stated 80% confidence interval
actually contains the true value 80% of the time.

An over-confident module (claims narrow intervals but has low coverage)
is dangerous: it inflates trust in rankings without evidence.
An under-confident module wastes selection budget.
"""

from dataclasses import dataclass, field

SIMULATION_UNCERTAINTY_CALIBRATION_REPORT_ID_PREFIX = "SUC-"

VALID_SIMULATION_MODULES: frozenset = frozenset({
    "membrane_proxy",
    "structure_proxy",
    "ensemble_checker",
    "external_adapter",
    "dummy_module",
    "baseline_registry",
    "other",
})

VALID_CALIBRATION_METHODS: frozenset = frozenset({
    "isotonic_regression",
    "platt_scaling",
    "temperature_scaling",
    "histogram_binning",
    "empirical_coverage_only",
    "none_applied",
})

VALID_UNCERTAINTY_ASSESSMENT_STATUSES: frozenset = frozenset({
    "well_calibrated",
    "overconfident",
    "underconfident",
    "insufficient_data",
    "not_assessed",
})

OVERCONFIDENCE_THRESHOLD: float = 0.15
UNDERCONFIDENCE_THRESHOLD: float = 0.15
MIN_SAMPLES_FOR_CALIBRATION: int = 10
CALIBRATION_ERROR_TOLERANCE: float = 0.01


@dataclass
class SimulationUncertaintyCalibrationReport:
    report_id: str
    module_id: str
    simulation_module: str
    calibration_method: str
    n_samples: int
    expected_coverage: float
    empirical_coverage: float
    calibration_error: float
    uncertainty_assessment_status: str
    overconfidence_flag: bool
    dry_lab_only: bool
    cheap_baseline_beats_module: bool | None
    notes: str
    created_at: str


def validate_uncertainty_calibration_report(
    report: SimulationUncertaintyCalibrationReport,
) -> list[str]:
    errors: list[str] = []

    if not report.report_id.startswith(SIMULATION_UNCERTAINTY_CALIBRATION_REPORT_ID_PREFIX):
        errors.append(
            f"report_id must start with '{SIMULATION_UNCERTAINTY_CALIBRATION_REPORT_ID_PREFIX}', "
            f"got: {report.report_id!r}"
        )

    if report.simulation_module not in VALID_SIMULATION_MODULES:
        errors.append(
            f"simulation_module {report.simulation_module!r} not in VALID_SIMULATION_MODULES"
        )

    if report.calibration_method not in VALID_CALIBRATION_METHODS:
        errors.append(
            f"calibration_method {report.calibration_method!r} not in VALID_CALIBRATION_METHODS"
        )

    if report.uncertainty_assessment_status not in VALID_UNCERTAINTY_ASSESSMENT_STATUSES:
        errors.append(
            f"uncertainty_assessment_status {report.uncertainty_assessment_status!r} "
            f"not in VALID_UNCERTAINTY_ASSESSMENT_STATUSES"
        )

    if not (0.0 <= report.expected_coverage <= 1.0):
        errors.append(
            f"expected_coverage must be in [0.0, 1.0], got: {report.expected_coverage}"
        )

    if not (0.0 <= report.empirical_coverage <= 1.0):
        errors.append(
            f"empirical_coverage must be in [0.0, 1.0], got: {report.empirical_coverage}"
        )

    computed_error = abs(report.expected_coverage - report.empirical_coverage)
    if abs(computed_error - report.calibration_error) > CALIBRATION_ERROR_TOLERANCE:
        errors.append(
            f"calibration_error {report.calibration_error} does not match "
            f"abs(expected_coverage - empirical_coverage) = {computed_error:.4f} "
            f"(tolerance {CALIBRATION_ERROR_TOLERANCE})"
        )

    if (
        report.n_samples < MIN_SAMPLES_FOR_CALIBRATION
        and report.uncertainty_assessment_status != "insufficient_data"
    ):
        errors.append(
            f"n_samples={report.n_samples} < MIN_SAMPLES_FOR_CALIBRATION={MIN_SAMPLES_FOR_CALIBRATION}; "
            f"uncertainty_assessment_status must be 'insufficient_data', "
            f"got: {report.uncertainty_assessment_status!r}"
        )

    if not report.dry_lab_only:
        errors.append("dry_lab_only must be True for all simulation calibration reports")

    if (
        report.uncertainty_assessment_status != "insufficient_data"
        and report.empirical_coverage < report.expected_coverage - OVERCONFIDENCE_THRESHOLD
        and not report.overconfidence_flag
    ):
        errors.append(
            f"overconfidence_flag must be True when empirical_coverage "
            f"({report.empirical_coverage}) < expected_coverage ({report.expected_coverage}) "
            f"- OVERCONFIDENCE_THRESHOLD ({OVERCONFIDENCE_THRESHOLD})"
        )

    if not report.module_id.strip():
        errors.append("module_id must not be blank")

    if not report.created_at.strip():
        errors.append("created_at must not be blank")

    return errors


def format_uncertainty_calibration_report(
    report: SimulationUncertaintyCalibrationReport,
) -> str:
    lines = [
        f"Simulation Uncertainty Calibration Report {report.report_id}",
        f"Module: {report.module_id} ({report.simulation_module})",
        f"Calibration Method: {report.calibration_method}",
        f"Samples: {report.n_samples}",
        f"Expected Coverage: {report.expected_coverage:.1%}",
        f"Empirical Coverage: {report.empirical_coverage:.1%}",
        f"Calibration Error: {report.calibration_error:.4f}",
        f"Assessment: {report.uncertainty_assessment_status}",
    ]
    if report.overconfidence_flag:
        lines.append("WARNING: Module is over-confident (narrow intervals, low coverage)")
    if report.cheap_baseline_beats_module is True:
        lines.append("NOTE: Cheap baseline beats this module — consider deprecation")
    elif report.cheap_baseline_beats_module is False:
        lines.append("Cheap baseline does NOT beat this module")
    else:
        lines.append("Cheap baseline comparison: not yet assessed")
    lines.append(f"Dry-lab only: {report.dry_lab_only}")
    if report.notes:
        lines.append(f"Notes: {report.notes}")
    lines.append(f"Created: {report.created_at}")
    return "\n".join(lines)
