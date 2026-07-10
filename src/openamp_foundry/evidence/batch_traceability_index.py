from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


REQUIRED_BATCH_ARTIFACT_TYPES = frozenset({"BSP", "SEG", "ECC", "STL"})

VALID_FAMILY_COMPLETENESS_GRADES = frozenset({"complete", "partial", "empty"})

VALID_BATCH_COMPLETENESS_GRADES = frozenset({"full", "majority", "minority", "none"})


@dataclass
class FamilyArtifactEntry:
    candidate_family_id: str
    artifact_ids: dict[str, str]
    present_artifact_types: list[str]
    missing_artifact_types: list[str]
    family_completeness_grade: str


@dataclass
class BatchTraceabilityIndex:
    bti_id: str
    batch_id: str
    pipeline_version: str
    n_families_total: int
    n_families_complete: int
    n_families_partial: int
    n_families_empty: int
    family_entries: list[FamilyArtifactEntry]
    batch_completeness_grade: str
    required_artifact_types: list[str]
    dry_lab_only: bool
    limitations: list[str]
    created_at: str
    audit_notes: str


@dataclass
class BTIValidationResult:
    valid: bool
    violations: list[str] = field(default_factory=list)


def _compute_family_completeness_grade(
    artifact_ids: dict[str, str],
) -> str:
    if not artifact_ids:
        return "empty"
    present_keys = set(artifact_ids.keys())
    if REQUIRED_BATCH_ARTIFACT_TYPES.issubset(present_keys):
        return "complete"
    return "partial"


def _compute_batch_completeness_grade(
    n_families_complete: int,
    n_families_total: int,
) -> str:
    if n_families_total == 0:
        return "none"
    if n_families_complete == n_families_total:
        return "full"
    if n_families_complete >= n_families_total / 2:
        return "majority"
    if n_families_complete > 0:
        return "minority"
    return "none"


def validate_batch_traceability_index(
    index: BatchTraceabilityIndex,
) -> BTIValidationResult:
    violations = []

    if not index.bti_id.startswith("BTI-"):
        violations.append("bti_id must start with 'BTI-'")

    if not index.batch_id:
        violations.append("batch_id must not be empty")

    if not index.dry_lab_only:
        violations.append("dry_lab_only must be True")

    if index.n_families_total != len(index.family_entries):
        violations.append(
            f"n_families_total ({index.n_families_total}) must equal len(family_entries) ({len(index.family_entries)})"
        )

    expected_complete = sum(
        1 for e in index.family_entries if e.family_completeness_grade == "complete"
    )
    if index.n_families_complete != expected_complete:
        violations.append(
            f"n_families_complete ({index.n_families_complete}) must equal count of complete entries ({expected_complete})"
        )

    expected_partial = sum(
        1 for e in index.family_entries if e.family_completeness_grade == "partial"
    )
    if index.n_families_partial != expected_partial:
        violations.append(
            f"n_families_partial ({index.n_families_partial}) must equal count of partial entries ({expected_partial})"
        )

    expected_empty = sum(
        1 for e in index.family_entries if e.family_completeness_grade == "empty"
    )
    if index.n_families_empty != expected_empty:
        violations.append(
            f"n_families_empty ({index.n_families_empty}) must equal count of empty entries ({expected_empty})"
        )

    if index.required_artifact_types != sorted(REQUIRED_BATCH_ARTIFACT_TYPES):
        violations.append(
            f"required_artifact_types ({index.required_artifact_types}) must equal {sorted(REQUIRED_BATCH_ARTIFACT_TYPES)}"
        )

    n_total = index.n_families_total
    n_complete = index.n_families_complete
    if index.batch_completeness_grade == "full":
        if not (n_complete == n_total and n_total > 0):
            violations.append(
                f"batch_completeness_grade='full' requires n_families_complete ({n_complete}) == n_families_total ({n_total}) > 0"
            )
    elif index.batch_completeness_grade == "majority":
        if not (n_complete >= n_total / 2 and n_complete < n_total):
            violations.append(
                f"batch_completeness_grade='majority' requires n_families_complete ({n_complete}) >= n_families_total/2 ({n_total / 2}) and < n_families_total ({n_total})"
            )
    elif index.batch_completeness_grade == "minority":
        if not (n_complete > 0 and n_complete < n_total / 2):
            violations.append(
                f"batch_completeness_grade='minority' requires n_families_complete ({n_complete}) > 0 and < n_families_total/2 ({n_total / 2})"
            )
    elif index.batch_completeness_grade == "none":
        if n_complete != 0:
            violations.append(
                f"batch_completeness_grade='none' requires n_families_complete ({n_complete}) == 0"
            )
    else:
        violations.append(
            f"batch_completeness_grade '{index.batch_completeness_grade}' must be one of {sorted(VALID_BATCH_COMPLETENESS_GRADES)}"
        )

    for entry in index.family_entries:
        if entry.candidate_family_id.startswith("TOY-"):
            violations.append(
                f"TOY- candidate_family_id ('{entry.candidate_family_id}') is not allowed"
            )

        if entry.present_artifact_types != sorted(entry.artifact_ids.keys()):
            violations.append(
                f"present_artifact_types ({entry.present_artifact_types}) must equal sorted(artifact_ids.keys()) ({sorted(entry.artifact_ids.keys())}) for {entry.candidate_family_id}"
            )

        expected_missing = sorted(
            REQUIRED_BATCH_ARTIFACT_TYPES - set(entry.artifact_ids.keys())
        )
        if entry.missing_artifact_types != expected_missing:
            violations.append(
                f"missing_artifact_types ({entry.missing_artifact_types}) must equal {expected_missing} for {entry.candidate_family_id}"
            )

        expected_grade = _compute_family_completeness_grade(entry.artifact_ids)
        if entry.family_completeness_grade != expected_grade:
            violations.append(
                f"family_completeness_grade '{entry.family_completeness_grade}' must be '{expected_grade}' for {entry.candidate_family_id}"
            )

    if not index.limitations:
        violations.append("limitations must be non-empty")

    return BTIValidationResult(valid=len(violations) == 0, violations=violations)


def build_batch_traceability_index(
    bti_id: str,
    batch_id: str,
    pipeline_version: str,
    family_artifact_dicts: list[dict],
    limitations: list[str],
    created_at: str,
    audit_notes: str = "",
) -> BatchTraceabilityIndex:
    family_entries: list[FamilyArtifactEntry] = []
    for d in family_artifact_dicts:
        artifact_ids = d["artifact_ids"]
        present = sorted(artifact_ids.keys())
        missing = sorted(REQUIRED_BATCH_ARTIFACT_TYPES - set(artifact_ids.keys()))
        grade = _compute_family_completeness_grade(artifact_ids)
        family_entries.append(
            FamilyArtifactEntry(
                candidate_family_id=d["candidate_family_id"],
                artifact_ids=artifact_ids,
                present_artifact_types=present,
                missing_artifact_types=missing,
                family_completeness_grade=grade,
            )
        )

    n_families_total = len(family_entries)
    n_families_complete = sum(
        1 for e in family_entries if e.family_completeness_grade == "complete"
    )
    n_families_partial = sum(
        1 for e in family_entries if e.family_completeness_grade == "partial"
    )
    n_families_empty = sum(
        1 for e in family_entries if e.family_completeness_grade == "empty"
    )
    batch_completeness_grade = _compute_batch_completeness_grade(
        n_families_complete, n_families_total
    )
    required_artifact_types = sorted(REQUIRED_BATCH_ARTIFACT_TYPES)

    index = BatchTraceabilityIndex(
        bti_id=bti_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        n_families_total=n_families_total,
        n_families_complete=n_families_complete,
        n_families_partial=n_families_partial,
        n_families_empty=n_families_empty,
        family_entries=family_entries,
        batch_completeness_grade=batch_completeness_grade,
        required_artifact_types=required_artifact_types,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
        audit_notes=audit_notes,
    )

    result = validate_batch_traceability_index(index)
    if not result.valid:
        raise ValueError(f"Invalid BTI: {result.violations}")
    return index


def format_batch_traceability_index(index: BatchTraceabilityIndex) -> str:
    lines = [
        f"Batch Traceability Index — {index.bti_id}",
        f"Batch: {index.batch_id}  |  Pipeline: {index.pipeline_version}",
        f"Batch Grade: {index.batch_completeness_grade}  |  "
        f"Complete: {index.n_families_complete}  |  "
        f"Partial: {index.n_families_partial}  |  "
        f"Empty: {index.n_families_empty}  |  "
        f"Total: {index.n_families_total}",
        f"Required Artifact Types: {', '.join(index.required_artifact_types)}",
        f"Created: {index.created_at}",
        f"Limitations: {'; '.join(index.limitations)}",
        "dry_lab_only: True",
    ]
    if index.audit_notes:
        lines.append(f"Audit Notes: {index.audit_notes}")
    lines.append("")
    lines.append("Family Entries:")
    for entry in index.family_entries:
        present_str = ", ".join(entry.present_artifact_types) if entry.present_artifact_types else "(none)"
        missing_str = ", ".join(entry.missing_artifact_types) if entry.missing_artifact_types else "(none)"
        lines.append(
            f"  {entry.candidate_family_id}: "
            f"grade={entry.family_completeness_grade}, "
            f"present=[{present_str}], "
            f"missing=[{missing_str}]"
        )
    return "\n".join(lines)
