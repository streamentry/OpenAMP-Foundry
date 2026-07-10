"""MBL- multi-batch learning record schema.

Per-batch snapshot of prediction quality after wet-lab feedback. Captures
hit rate, AUROC, and n_confirmed for each batch, enabling cross-batch
comparison of whether the pipeline is improving. Feeds into the calibration
improvement tracker (CIT-).
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_MBL_QUALITY_GRADES: frozenset[str] = frozenset({
    "A",
    "B",
    "C",
    "D",
    "N/A",
})

VALID_BATCH_LEARNING_STATUSES: frozenset[str] = frozenset({
    "data_complete",
    "data_partial",
    "no_wet_lab_data",
})

MIN_AUROC: float = 0.0
MAX_AUROC: float = 1.0
MIN_HIT_RATE: float = 0.0
MAX_HIT_RATE: float = 1.0

GRADE_A_HIT_RATE: float = 0.40
GRADE_B_HIT_RATE: float = 0.25
GRADE_C_HIT_RATE: float = 0.10


@dataclass
class MultiBatchLearningRecord:
    mbl_id: str
    batch_id: str
    pipeline_version: str
    n_candidates_tested: int
    n_confirmed_hits: int
    hit_rate: float
    auroc: float
    quality_grade: str
    batch_learning_status: str
    whr_ids: list[str]
    pcu_id: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_multi_batch_learning_record(mbl: MultiBatchLearningRecord) -> None:
    if not mbl.mbl_id.startswith("MBL-"):
        raise ValueError(f"mbl_id must start with 'MBL-': {mbl.mbl_id!r}")
    if not mbl.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not mbl.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if mbl.n_candidates_tested < 0:
        raise ValueError("n_candidates_tested must be non-negative")
    if mbl.n_confirmed_hits < 0:
        raise ValueError("n_confirmed_hits must be non-negative")
    if mbl.n_confirmed_hits > mbl.n_candidates_tested:
        raise ValueError("n_confirmed_hits cannot exceed n_candidates_tested")
    if mbl.batch_learning_status != "no_wet_lab_data":
        if not (MIN_AUROC <= mbl.auroc <= MAX_AUROC):
            raise ValueError(f"auroc must be in [0, 1]: {mbl.auroc}")
        if not (MIN_HIT_RATE <= mbl.hit_rate <= MAX_HIT_RATE):
            raise ValueError(f"hit_rate must be in [0, 1]: {mbl.hit_rate}")
        if mbl.n_candidates_tested > 0:
            expected_hr = round(mbl.n_confirmed_hits / mbl.n_candidates_tested, 6)
            if abs(mbl.hit_rate - expected_hr) > 1e-4:
                raise ValueError(
                    f"hit_rate {mbl.hit_rate} does not match computed "
                    f"{expected_hr}"
                )
    if mbl.quality_grade not in VALID_MBL_QUALITY_GRADES:
        raise ValueError(
            f"quality_grade {mbl.quality_grade!r} not in VALID_MBL_QUALITY_GRADES"
        )
    if mbl.batch_learning_status not in VALID_BATCH_LEARNING_STATUSES:
        raise ValueError(
            f"batch_learning_status {mbl.batch_learning_status!r} not in "
            f"VALID_BATCH_LEARNING_STATUSES"
        )
    if mbl.batch_learning_status == "no_wet_lab_data" and mbl.quality_grade != "N/A":
        raise ValueError(
            "quality_grade must be 'N/A' when batch_learning_status='no_wet_lab_data'"
        )
    if not mbl.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not mbl.limitations:
        raise ValueError("limitations must be non-empty")
    if not mbl.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_quality_grade(
    hit_rate: float,
    n_tested: int,
    status: str,
) -> str:
    if status == "no_wet_lab_data" or n_tested == 0:
        return "N/A"
    if hit_rate >= GRADE_A_HIT_RATE:
        return "A"
    if hit_rate >= GRADE_B_HIT_RATE:
        return "B"
    if hit_rate >= GRADE_C_HIT_RATE:
        return "C"
    return "D"


def build_multi_batch_learning_record(
    *,
    mbl_id: str,
    batch_id: str,
    pipeline_version: str,
    n_candidates_tested: int,
    n_confirmed_hits: int,
    auroc: float,
    batch_learning_status: str,
    whr_ids: list[str],
    pcu_id: str = "",
    limitations: list[str],
    created_at: str,
) -> MultiBatchLearningRecord:
    if n_candidates_tested > 0 and batch_learning_status != "no_wet_lab_data":
        hit_rate = round(n_confirmed_hits / n_candidates_tested, 6)
    else:
        hit_rate = 0.0
    grade = _compute_quality_grade(hit_rate, n_candidates_tested, batch_learning_status)
    mbl = MultiBatchLearningRecord(
        mbl_id=mbl_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        n_candidates_tested=n_candidates_tested,
        n_confirmed_hits=n_confirmed_hits,
        hit_rate=hit_rate,
        auroc=auroc,
        quality_grade=grade,
        batch_learning_status=batch_learning_status,
        whr_ids=list(whr_ids),
        pcu_id=pcu_id,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_multi_batch_learning_record(mbl)
    return mbl


def format_multi_batch_learning_record(mbl: MultiBatchLearningRecord) -> str:
    lines = [
        f"Multi-Batch Learning Record — {mbl.mbl_id}",
        f"Batch: {mbl.batch_id}  |  Pipeline: {mbl.pipeline_version}",
        f"Status: {mbl.batch_learning_status}  |  Grade: {mbl.quality_grade}",
        f"Candidates tested: {mbl.n_candidates_tested}  |  "
        f"Confirmed hits: {mbl.n_confirmed_hits}  |  "
        f"Hit rate: {mbl.hit_rate:.1%}",
        f"AUROC: {mbl.auroc:.4f}",
    ]
    if mbl.whr_ids:
        lines.append(f"WHR IDs: {', '.join(mbl.whr_ids)}")
    if mbl.pcu_id:
        lines.append(f"PCU: {mbl.pcu_id}")
    lines.append(f"Created: {mbl.created_at}")
    lines.append(f"Limitations: {'; '.join(mbl.limitations)}")
    lines.append(f"dry_lab_only: {mbl.dry_lab_only}")
    return "\n".join(lines)
