"""ECI- evidence completeness index schema.

Top-level index of which schemas exist for each batch and family across all
phases. Aggregates PCC + CBA2 + BEG + SAT into a single completeness
snapshot. Closes Phase U.
"""

from __future__ import annotations

from dataclasses import dataclass

AGGREGATED_SCHEMA_TYPES: frozenset[str] = frozenset({"PCC", "CBA2", "BEG", "SAT"})

VALID_ECI_GRADES: frozenset[str] = frozenset({"A", "B", "C", "D"})

# Grade thresholds: A=100%, B>=75%, C>=50%, D<50%
_GRADE_THRESHOLDS = [
    ("A", 1.0),
    ("B", 0.75),
    ("C", 0.5),
]


def _compute_grade(fraction: float) -> str:
    for grade, threshold in _GRADE_THRESHOLDS:
        if fraction >= threshold:
            return grade
    return "D"


@dataclass
class BatchSchemaPresence:
    batch_id: str
    pcc_id: str
    pcc_present: bool
    cba2_id: str
    cba2_present: bool
    beg_id: str
    beg_present: bool
    sat_id: str
    sat_present: bool
    n_schemas_present: int
    n_schemas_required: int
    completeness_fraction: float
    batch_grade: str


@dataclass
class EvidenceCompletenessIndex:
    eci_id: str
    pipeline_version: str
    batch_entries: list[BatchSchemaPresence]
    n_batches: int
    n_schemas_required_per_batch: int
    total_schema_slots: int
    total_schemas_present: int
    overall_completeness_fraction: float
    completeness_grade: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_evidence_completeness_index(eci: EvidenceCompletenessIndex) -> None:
    if not eci.eci_id.startswith("ECI-"):
        raise ValueError(f"eci_id must start with 'ECI-': {eci.eci_id!r}")
    if not eci.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if eci.completeness_grade not in VALID_ECI_GRADES:
        raise ValueError(
            f"completeness_grade {eci.completeness_grade!r} not in VALID_ECI_GRADES"
        )
    if not eci.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not eci.limitations:
        raise ValueError("limitations must be non-empty")
    if not eci.created_at:
        raise ValueError("created_at must be non-empty")
    n_req = len(AGGREGATED_SCHEMA_TYPES)
    if eci.n_schemas_required_per_batch != n_req:
        raise ValueError(
            f"n_schemas_required_per_batch must be {n_req}, got {eci.n_schemas_required_per_batch}"
        )
    if eci.n_batches != len(eci.batch_entries):
        raise ValueError("n_batches must equal len(batch_entries)")
    expected_slots = eci.n_batches * n_req
    if eci.total_schema_slots != expected_slots:
        raise ValueError(
            f"total_schema_slots must be {expected_slots}, got {eci.total_schema_slots}"
        )
    total_present = sum(e.n_schemas_present for e in eci.batch_entries)
    if eci.total_schemas_present != total_present:
        raise ValueError("total_schemas_present mismatch")


def build_evidence_completeness_index(
    *,
    eci_id: str,
    pipeline_version: str,
    batch_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> EvidenceCompletenessIndex:
    """Build an evidence completeness index.

    batch_dicts: list of dicts with keys:
        batch_id, pcc_id, cba2_id, beg_id, sat_id
        Each id is non-empty string if present, "" if absent.
    """
    n_req = len(AGGREGATED_SCHEMA_TYPES)
    entries: list[BatchSchemaPresence] = []
    for d in batch_dicts:
        pcc_present = bool(d.get("pcc_id", ""))
        cba2_present = bool(d.get("cba2_id", ""))
        beg_present = bool(d.get("beg_id", ""))
        sat_present = bool(d.get("sat_id", ""))
        n_present = sum([pcc_present, cba2_present, beg_present, sat_present])
        fraction = n_present / n_req
        entries.append(BatchSchemaPresence(
            batch_id=d["batch_id"],
            pcc_id=d.get("pcc_id", ""),
            pcc_present=pcc_present,
            cba2_id=d.get("cba2_id", ""),
            cba2_present=cba2_present,
            beg_id=d.get("beg_id", ""),
            beg_present=beg_present,
            sat_id=d.get("sat_id", ""),
            sat_present=sat_present,
            n_schemas_present=n_present,
            n_schemas_required=n_req,
            completeness_fraction=fraction,
            batch_grade=_compute_grade(fraction),
        ))

    n_batches = len(entries)
    total_slots = n_batches * n_req
    total_present = sum(e.n_schemas_present for e in entries)
    overall_fraction = total_present / total_slots if total_slots > 0 else 0.0
    grade = _compute_grade(overall_fraction)

    eci = EvidenceCompletenessIndex(
        eci_id=eci_id,
        pipeline_version=pipeline_version,
        batch_entries=entries,
        n_batches=n_batches,
        n_schemas_required_per_batch=n_req,
        total_schema_slots=total_slots,
        total_schemas_present=total_present,
        overall_completeness_fraction=overall_fraction,
        completeness_grade=grade,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_evidence_completeness_index(eci)
    return eci


def format_evidence_completeness_index(eci: EvidenceCompletenessIndex) -> str:
    lines = [
        f"Evidence Completeness Index — {eci.eci_id}",
        f"Pipeline: {eci.pipeline_version}",
        f"Grade: {eci.completeness_grade}  |  Fraction: {eci.overall_completeness_fraction:.2%}",
        f"Batches: {eci.n_batches}  |  Schemas/batch: {eci.n_schemas_required_per_batch}",
        f"Total slots: {eci.total_schema_slots}  |  Present: {eci.total_schemas_present}",
    ]
    if eci.batch_entries:
        lines.append("Batch summary:")
        for entry in eci.batch_entries:
            lines.append(
                f"  {entry.batch_id}: grade={entry.batch_grade} "
                f"({entry.n_schemas_present}/{entry.n_schemas_required}) "
                f"PCC={entry.pcc_present} CBA2={entry.cba2_present} "
                f"BEG={entry.beg_present} SAT={entry.sat_present}"
            )
    lines.append(f"Created: {eci.created_at}")
    lines.append(f"Limitations: {'; '.join(eci.limitations)}")
    lines.append(f"dry_lab_only: {eci.dry_lab_only}")
    return "\n".join(lines)
