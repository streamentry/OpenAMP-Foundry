"""RCC- recalibration confidence certificate schema.

Asserts with what confidence the current calibration weights are reliable,
based on cohort size, quality consistency, and cross-batch agreement.
Prevents overconfident calibration claims when evidence is thin.
Gives a machine-checkable grade (A-D) that gates downstream claims.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_RCC_GRADES: frozenset[str] = frozenset({
    "A",
    "B",
    "C",
    "D",
})

VALID_RCC_VERDICTS: frozenset[str] = frozenset({
    "high_confidence",
    "moderate_confidence",
    "low_confidence",
    "insufficient_data",
})

VALID_CONSISTENCY_RATINGS: frozenset[str] = frozenset({
    "consistent",
    "moderately_consistent",
    "inconsistent",
    "unknown",
})

MIN_BATCHES_FOR_CONFIDENCE: int = 2
HIGH_CONFIDENCE_MIN_BATCHES: int = 4
MODERATE_CONFIDENCE_MIN_BATCHES: int = 2
MIN_COHORT_SIZE_PER_BATCH: int = 5

GRADE_A_MIN_BATCHES: int = 4
GRADE_B_MIN_BATCHES: int = 2
GRADE_C_MIN_BATCHES: int = 1


@dataclass
class BatchCohortEntry:
    batch_id: str
    mbl_id: str
    cohort_size: int
    quality_grade: str


@dataclass
class RecalibrationConfidenceCertificate:
    rcc_id: str
    pipeline_version: str
    cit_id: str
    lpr_id: str
    batch_cohort_entries: list[BatchCohortEntry]
    n_batches_assessed: int
    total_cohort_size: int
    cross_batch_consistency: str
    rcc_grade: str
    rcc_verdict: str
    confidence_rationale: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_recalibration_confidence_certificate(
    rcc: RecalibrationConfidenceCertificate,
) -> None:
    if not rcc.rcc_id.startswith("RCC-"):
        raise ValueError(f"rcc_id must start with 'RCC-': {rcc.rcc_id!r}")
    if not rcc.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not rcc.cit_id.startswith("CIT-"):
        raise ValueError(f"cit_id must start with 'CIT-': {rcc.cit_id!r}")
    if not rcc.lpr_id.startswith("LPR-"):
        raise ValueError(f"lpr_id must start with 'LPR-': {rcc.lpr_id!r}")
    for entry in rcc.batch_cohort_entries:
        if entry.cohort_size < 0:
            raise ValueError(
                f"cohort_size must be non-negative for batch {entry.batch_id!r}"
            )
    if rcc.n_batches_assessed != len(rcc.batch_cohort_entries):
        raise ValueError("n_batches_assessed must equal len(batch_cohort_entries)")
    expected_total = sum(e.cohort_size for e in rcc.batch_cohort_entries)
    if rcc.total_cohort_size != expected_total:
        raise ValueError(
            f"total_cohort_size mismatch: expected {expected_total}, got {rcc.total_cohort_size}"
        )
    if rcc.cross_batch_consistency not in VALID_CONSISTENCY_RATINGS:
        raise ValueError(
            f"cross_batch_consistency {rcc.cross_batch_consistency!r} not in VALID_CONSISTENCY_RATINGS"
        )
    if rcc.rcc_grade not in VALID_RCC_GRADES:
        raise ValueError(
            f"rcc_grade {rcc.rcc_grade!r} not in VALID_RCC_GRADES"
        )
    if rcc.rcc_verdict not in VALID_RCC_VERDICTS:
        raise ValueError(
            f"rcc_verdict {rcc.rcc_verdict!r} not in VALID_RCC_VERDICTS"
        )
    if not rcc.confidence_rationale:
        raise ValueError("confidence_rationale must be non-empty")
    if not rcc.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not rcc.limitations:
        raise ValueError("limitations must be non-empty")
    if not rcc.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_consistency(
    entries: list[BatchCohortEntry],
) -> str:
    if len(entries) < MIN_BATCHES_FOR_CONFIDENCE:
        return "unknown"
    grades = [e.quality_grade for e in entries if e.quality_grade != "N/A"]
    if not grades:
        return "unknown"
    unique = set(grades)
    if len(unique) == 1:
        return "consistent"
    if len(unique) == 2:
        return "moderately_consistent"
    return "inconsistent"


def _compute_grade_and_verdict(
    n_batches: int,
    consistency: str,
    total_cohort_size: int,
) -> tuple[str, str]:
    if n_batches == 0:
        return "D", "insufficient_data"
    if n_batches < MIN_BATCHES_FOR_CONFIDENCE:
        return "D", "insufficient_data"
    if n_batches >= GRADE_A_MIN_BATCHES and consistency == "consistent":
        return "A", "high_confidence"
    if n_batches >= GRADE_B_MIN_BATCHES and consistency in ("consistent", "moderately_consistent"):
        return "B", "moderate_confidence"
    if n_batches >= GRADE_C_MIN_BATCHES and consistency != "inconsistent":
        return "C", "low_confidence"
    return "D", "low_confidence"


def _build_rationale(
    n_batches: int,
    consistency: str,
    total_cohort_size: int,
    grade: str,
) -> str:
    return (
        f"Grade {grade}: {n_batches} batch(es) assessed, "
        f"total cohort size {total_cohort_size}, "
        f"cross-batch consistency={consistency}."
    )


def build_recalibration_confidence_certificate(
    *,
    rcc_id: str,
    pipeline_version: str,
    cit_id: str,
    lpr_id: str,
    batch_cohort_entry_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> RecalibrationConfidenceCertificate:
    """Build a RecalibrationConfidenceCertificate.

    batch_cohort_entry_dicts: list of dicts with keys:
        batch_id, mbl_id, cohort_size, quality_grade
    """
    entries = [
        BatchCohortEntry(
            batch_id=d["batch_id"],
            mbl_id=d["mbl_id"],
            cohort_size=int(d["cohort_size"]),
            quality_grade=d["quality_grade"],
        )
        for d in batch_cohort_entry_dicts
    ]
    total = sum(e.cohort_size for e in entries)
    consistency = _compute_consistency(entries)
    grade, verdict = _compute_grade_and_verdict(len(entries), consistency, total)
    rationale = _build_rationale(len(entries), consistency, total, grade)
    rcc = RecalibrationConfidenceCertificate(
        rcc_id=rcc_id,
        pipeline_version=pipeline_version,
        cit_id=cit_id,
        lpr_id=lpr_id,
        batch_cohort_entries=entries,
        n_batches_assessed=len(entries),
        total_cohort_size=total,
        cross_batch_consistency=consistency,
        rcc_grade=grade,
        rcc_verdict=verdict,
        confidence_rationale=rationale,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_recalibration_confidence_certificate(rcc)
    return rcc


def format_recalibration_confidence_certificate(
    rcc: RecalibrationConfidenceCertificate,
) -> str:
    lines = [
        f"Recalibration Confidence Certificate — {rcc.rcc_id}",
        f"Pipeline: {rcc.pipeline_version}  |  CIT: {rcc.cit_id}  |  LPR: {rcc.lpr_id}",
        f"Grade: {rcc.rcc_grade}  |  Verdict: {rcc.rcc_verdict}",
        f"Batches assessed: {rcc.n_batches_assessed}  |  "
        f"Total cohort: {rcc.total_cohort_size}  |  "
        f"Consistency: {rcc.cross_batch_consistency}",
        f"Rationale: {rcc.confidence_rationale}",
    ]
    if rcc.batch_cohort_entries:
        lines.append("Batch cohorts:")
        for entry in rcc.batch_cohort_entries:
            lines.append(
                f"  {entry.batch_id} ({entry.mbl_id}): "
                f"cohort={entry.cohort_size}  grade={entry.quality_grade}"
            )
    lines.append(f"Created: {rcc.created_at}")
    lines.append(f"Limitations: {'; '.join(rcc.limitations)}")
    lines.append(f"dry_lab_only: {rcc.dry_lab_only}")
    return "\n".join(lines)
