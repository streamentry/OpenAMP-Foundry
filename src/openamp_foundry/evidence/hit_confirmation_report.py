from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


VALID_CONFIRMATION_VERDICTS = frozenset({
    "confirmed_hit",
    "partial_hit",
    "not_confirmed",
    "inconclusive",
})

VALID_DIVERGENCE_TYPES = frozenset({
    "mic_above_predicted_range",
    "mic_below_predicted_range",
    "activity_spectrum_mismatch",
    "selectivity_mismatch",
    "hemolysis_above_predicted",
    "no_divergence",
    "multiple_divergences",
})

VALID_PREDICTION_QUALITY_GRADES = frozenset({
    "A",  # prediction matched outcome within expected range
    "B",  # minor deviation, within 2x
    "C",  # significant deviation, 2-10x
    "D",  # major divergence, >10x or qualitative mismatch
    "N/A",  # insufficient data to grade
})


@dataclass
class HitConfirmationReport:
    hcr_id: str
    candidate_id: str
    sequence: str
    whr_ids: List[str]
    pre_registration_id: Optional[str]
    dry_lab_score: float
    confirmation_verdict: str
    divergence_types: List[str]
    prediction_quality_grade: str
    n_experiments: int
    n_confirmed: int
    n_inactive: int
    n_inconclusive: int
    dry_lab_only: bool
    limitations: str
    notes: str = ""


@dataclass
class HCRValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_hit_confirmation_report(report: HitConfirmationReport) -> HCRValidationResult:
    violations = []

    if not report.hcr_id.startswith("HCR-"):
        violations.append("hcr_id must start with 'HCR-'")

    if not report.candidate_id:
        violations.append("candidate_id is required")

    if report.candidate_id.startswith("TOY-"):
        violations.append("TOY- candidate IDs are not allowed in real HCR- records")

    if not report.sequence or len(report.sequence) < 5:
        violations.append("sequence must be at least 5 amino acids")

    if not report.whr_ids:
        violations.append("at least one whr_id is required")

    for wid in report.whr_ids:
        if not wid.startswith("WHR-"):
            violations.append(f"whr_id '{wid}' must start with 'WHR-'")

    if report.dry_lab_score < 0.0 or report.dry_lab_score > 1.0:
        violations.append("dry_lab_score must be in [0.0, 1.0]")

    if report.confirmation_verdict not in VALID_CONFIRMATION_VERDICTS:
        violations.append(
            f"confirmation_verdict '{report.confirmation_verdict}' must be one of {sorted(VALID_CONFIRMATION_VERDICTS)}"
        )

    for dt in report.divergence_types:
        if dt not in VALID_DIVERGENCE_TYPES:
            violations.append(
                f"divergence_type '{dt}' must be one of {sorted(VALID_DIVERGENCE_TYPES)}"
            )

    if report.prediction_quality_grade not in VALID_PREDICTION_QUALITY_GRADES:
        violations.append(
            f"prediction_quality_grade '{report.prediction_quality_grade}' must be one of {sorted(VALID_PREDICTION_QUALITY_GRADES)}"
        )

    if report.n_experiments < 1:
        violations.append("n_experiments must be >= 1")

    if report.n_confirmed < 0:
        violations.append("n_confirmed must be >= 0")

    if report.n_inactive < 0:
        violations.append("n_inactive must be >= 0")

    if report.n_inconclusive < 0:
        violations.append("n_inconclusive must be >= 0")

    total = report.n_confirmed + report.n_inactive + report.n_inconclusive
    if total > report.n_experiments:
        violations.append(
            f"n_confirmed ({report.n_confirmed}) + n_inactive ({report.n_inactive}) + n_inconclusive ({report.n_inconclusive}) = {total} exceeds n_experiments ({report.n_experiments})"
        )

    if report.dry_lab_only:
        violations.append("dry_lab_only must be False for HCR- records (real experimental outcomes required)")

    if not report.limitations or len(report.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    # Consistency: confirmed_hit requires at least one confirmed experiment
    if report.confirmation_verdict == "confirmed_hit" and report.n_confirmed < 1:
        violations.append("confirmation_verdict='confirmed_hit' requires n_confirmed >= 1")

    # Consistency: not_confirmed requires n_inactive >= 1
    if report.confirmation_verdict == "not_confirmed" and report.n_inactive < 1:
        violations.append("confirmation_verdict='not_confirmed' requires n_inactive >= 1")

    # Consistency: no_divergence cannot coexist with other divergence types
    if "no_divergence" in report.divergence_types and len(report.divergence_types) > 1:
        violations.append("divergence_type 'no_divergence' cannot coexist with other divergence types")

    return HCRValidationResult(valid=len(violations) == 0, violations=violations)


def build_hit_confirmation_report(
    hcr_id: str,
    candidate_id: str,
    sequence: str,
    whr_ids: List[str],
    dry_lab_score: float,
    confirmation_verdict: str,
    divergence_types: List[str],
    prediction_quality_grade: str,
    n_experiments: int,
    n_confirmed: int,
    n_inactive: int,
    n_inconclusive: int,
    limitations: str,
    pre_registration_id: Optional[str] = None,
    notes: str = "",
) -> HitConfirmationReport:
    report = HitConfirmationReport(
        hcr_id=hcr_id,
        candidate_id=candidate_id,
        sequence=sequence,
        whr_ids=whr_ids,
        pre_registration_id=pre_registration_id,
        dry_lab_score=dry_lab_score,
        confirmation_verdict=confirmation_verdict,
        divergence_types=divergence_types,
        prediction_quality_grade=prediction_quality_grade,
        n_experiments=n_experiments,
        n_confirmed=n_confirmed,
        n_inactive=n_inactive,
        n_inconclusive=n_inconclusive,
        dry_lab_only=False,
        limitations=limitations,
        notes=notes,
    )
    result = validate_hit_confirmation_report(report)
    if not result.valid:
        raise ValueError(f"Invalid HCR: {result.violations}")
    return report


def format_hit_confirmation_report(report: HitConfirmationReport) -> str:
    lines = [
        f"Hit Confirmation Report — {report.hcr_id}",
        f"Candidate: {report.candidate_id}  |  Sequence: {report.sequence}",
        f"Dry-Lab Score: {report.dry_lab_score:.3f}",
        f"Verdict: {report.confirmation_verdict}",
        f"Prediction Quality: {report.prediction_quality_grade}",
        f"Experiments: {report.n_experiments} total ({report.n_confirmed} confirmed, {report.n_inactive} inactive, {report.n_inconclusive} inconclusive)",
        f"WHR Records: {', '.join(report.whr_ids)}",
    ]
    if report.pre_registration_id:
        lines.append(f"Pre-Registration: {report.pre_registration_id}")
    if report.divergence_types:
        lines.append(f"Divergences: {', '.join(report.divergence_types)}")
    lines.append(f"Limitations: {report.limitations}")
    if report.notes:
        lines.append(f"Notes: {report.notes}")
    lines.append("dry_lab_only: False (real experimental outcomes)")
    return "\n".join(lines)
