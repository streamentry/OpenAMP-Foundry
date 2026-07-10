"""Failure mode similarity report schema (Phase F F8).

FMS- records benchmark whether rejected candidates resemble previously
documented failure modes. A pipeline that repeatedly nominates candidates
with the same failure-mode signature (e.g. high hemolysis risk, low
selectivity, known resistance motif) is not learning from its own history.

This report surfaces that pattern so calibration can correct it.
"""

from dataclasses import dataclass, field

FAILURE_MODE_SIMILARITY_REPORT_ID_PREFIX = "FMS-"

VALID_FAILURE_MODE_CATEGORIES: frozenset = frozenset({
    "hemolysis_risk",
    "low_selectivity",
    "toxicity_flag",
    "dual_use_concern",
    "known_resistance_motif",
    "charge_shortcut",
    "length_outside_range",
    "low_novelty",
    "sequence_degeneracy",
    "poor_charge_distribution",
    "other",
})

VALID_SIMILARITY_ASSESSMENT_STATUSES: frozenset = frozenset({
    "low_similarity",
    "moderate_similarity",
    "high_similarity",
    "pattern_repeated",
    "insufficient_data",
})

VALID_BENCHMARK_STATUSES: frozenset = frozenset({
    "draft",
    "complete",
    "under_review",
    "finalized",
})

HIGH_SIMILARITY_THRESHOLD: float = 0.60
PATTERN_REPEATED_THRESHOLD: float = 0.80
MIN_REJECTED_CANDIDATES_FOR_BENCHMARK: int = 3
FRACTION_TOLERANCE: float = 0.01


@dataclass
class FailureModeSimilarityReport:
    report_id: str
    batch_id: str
    n_rejected_candidates: int
    n_with_known_failure_mode: int
    fraction_matching_known_failure_mode: float
    top_failure_mode_category: str
    top_failure_mode_fraction: float
    similarity_assessment_status: str
    pattern_repeated_flag: bool
    benchmark_status: str
    dry_lab_only: bool
    calibration_action_recommended: bool
    notes: str
    created_at: str


def validate_failure_mode_similarity_report(
    report: FailureModeSimilarityReport,
) -> list[str]:
    errors: list[str] = []

    if not report.report_id.startswith(FAILURE_MODE_SIMILARITY_REPORT_ID_PREFIX):
        errors.append(
            f"report_id must start with '{FAILURE_MODE_SIMILARITY_REPORT_ID_PREFIX}', "
            f"got: {report.report_id!r}"
        )

    if report.top_failure_mode_category not in VALID_FAILURE_MODE_CATEGORIES:
        errors.append(
            f"top_failure_mode_category {report.top_failure_mode_category!r} "
            f"not in VALID_FAILURE_MODE_CATEGORIES"
        )

    if report.similarity_assessment_status not in VALID_SIMILARITY_ASSESSMENT_STATUSES:
        errors.append(
            f"similarity_assessment_status {report.similarity_assessment_status!r} "
            f"not in VALID_SIMILARITY_ASSESSMENT_STATUSES"
        )

    if report.benchmark_status not in VALID_BENCHMARK_STATUSES:
        errors.append(
            f"benchmark_status {report.benchmark_status!r} not in VALID_BENCHMARK_STATUSES"
        )

    if not (0.0 <= report.fraction_matching_known_failure_mode <= 1.0):
        errors.append(
            f"fraction_matching_known_failure_mode must be in [0.0, 1.0], "
            f"got: {report.fraction_matching_known_failure_mode}"
        )

    if not (0.0 <= report.top_failure_mode_fraction <= 1.0):
        errors.append(
            f"top_failure_mode_fraction must be in [0.0, 1.0], "
            f"got: {report.top_failure_mode_fraction}"
        )

    if report.n_rejected_candidates > 0:
        computed = report.n_with_known_failure_mode / report.n_rejected_candidates
        if abs(computed - report.fraction_matching_known_failure_mode) > FRACTION_TOLERANCE:
            errors.append(
                f"fraction_matching_known_failure_mode {report.fraction_matching_known_failure_mode} "
                f"does not match n_with_known_failure_mode / n_rejected_candidates "
                f"= {computed:.4f} (tolerance {FRACTION_TOLERANCE})"
            )

    if (
        report.n_rejected_candidates < MIN_REJECTED_CANDIDATES_FOR_BENCHMARK
        and report.similarity_assessment_status != "insufficient_data"
    ):
        errors.append(
            f"n_rejected_candidates={report.n_rejected_candidates} < "
            f"MIN_REJECTED_CANDIDATES_FOR_BENCHMARK={MIN_REJECTED_CANDIDATES_FOR_BENCHMARK}; "
            f"similarity_assessment_status must be 'insufficient_data', "
            f"got: {report.similarity_assessment_status!r}"
        )

    if not report.dry_lab_only:
        errors.append("dry_lab_only must be True for all failure mode similarity reports")

    if (
        report.similarity_assessment_status != "insufficient_data"
        and report.fraction_matching_known_failure_mode >= PATTERN_REPEATED_THRESHOLD
        and not report.pattern_repeated_flag
    ):
        errors.append(
            f"pattern_repeated_flag must be True when fraction_matching_known_failure_mode "
            f"({report.fraction_matching_known_failure_mode}) >= "
            f"PATTERN_REPEATED_THRESHOLD ({PATTERN_REPEATED_THRESHOLD})"
        )

    if not report.batch_id.strip():
        errors.append("batch_id must not be blank")

    if not report.created_at.strip():
        errors.append("created_at must not be blank")

    if report.n_with_known_failure_mode > report.n_rejected_candidates:
        errors.append(
            f"n_with_known_failure_mode ({report.n_with_known_failure_mode}) "
            f"cannot exceed n_rejected_candidates ({report.n_rejected_candidates})"
        )

    return errors


def format_failure_mode_similarity_report(
    report: FailureModeSimilarityReport,
) -> str:
    lines = [
        f"Failure Mode Similarity Report {report.report_id}",
        f"Batch: {report.batch_id}",
        f"Rejected candidates: {report.n_rejected_candidates}",
        f"  With known failure mode: {report.n_with_known_failure_mode} "
        f"({report.fraction_matching_known_failure_mode:.1%})",
        f"Top failure mode: {report.top_failure_mode_category} "
        f"({report.top_failure_mode_fraction:.1%} of rejected)",
        f"Similarity assessment: {report.similarity_assessment_status}",
        f"Benchmark status: {report.benchmark_status}",
    ]
    if report.pattern_repeated_flag:
        lines.append(
            "WARNING: Pattern repeated -- pipeline is re-nominating candidates "
            "with a dominant known failure mode"
        )
    if report.calibration_action_recommended:
        lines.append("ACTION REQUIRED: Calibration update recommended to address failure pattern")
    lines.append(f"Dry-lab only: {report.dry_lab_only}")
    if report.notes:
        lines.append(f"Notes: {report.notes}")
    lines.append(f"Created: {report.created_at}")
    return "\n".join(lines)
