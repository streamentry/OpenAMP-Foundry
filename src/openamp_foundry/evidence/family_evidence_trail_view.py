"""FET- family evidence trail view schema.

Per-family aggregation of all evidence schema references into a timeline view.
Shows which schemas are present, missing, and when produced.
"""

from __future__ import annotations

from dataclasses import dataclass, field

REQUIRED_TRAIL_SCHEMA_TYPES: frozenset[str] = frozenset({
    "BTI", "BEG", "SAT", "PCC",
    "BSP", "SEG", "ECC", "RSR", "PQT",
})

VALID_TRAIL_COMPLETENESS_GRADES: frozenset[str] = frozenset({
    "complete", "partial", "empty",
})


@dataclass
class FamilySchemaEvent:
    schema_type: str
    artifact_id: str
    created_at: str


@dataclass
class FamilyEvidenceTrailView:
    fet_id: str
    candidate_family_id: str
    batch_id: str
    pipeline_version: str
    schema_events: list[FamilySchemaEvent]
    present_schema_types: list[str]
    missing_schema_types: list[str]
    n_schemas_present: int
    n_schemas_required: int
    trail_completeness_grade: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _compute_grade(n_present: int, n_required: int) -> str:
    if n_present == 0:
        return "empty"
    if n_present == n_required:
        return "complete"
    return "partial"


def validate_family_evidence_trail_view(view: FamilyEvidenceTrailView) -> None:
    if not view.fet_id.startswith("FET-"):
        raise ValueError(f"fet_id must start with 'FET-': {view.fet_id!r}")
    if view.candidate_family_id.startswith("TOY-"):
        raise ValueError(
            f"candidate_family_id must not start with 'TOY-': {view.candidate_family_id!r}"
        )
    if not view.candidate_family_id:
        raise ValueError("candidate_family_id must be non-empty")
    if not view.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not view.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for event in view.schema_events:
        if event.schema_type not in REQUIRED_TRAIL_SCHEMA_TYPES:
            raise ValueError(
                f"schema_type {event.schema_type!r} not in REQUIRED_TRAIL_SCHEMA_TYPES"
            )
        if not event.artifact_id:
            raise ValueError(
                f"artifact_id must be non-empty for schema_type {event.schema_type!r}"
            )
    if view.trail_completeness_grade not in VALID_TRAIL_COMPLETENESS_GRADES:
        raise ValueError(
            f"trail_completeness_grade {view.trail_completeness_grade!r} not in "
            f"VALID_TRAIL_COMPLETENESS_GRADES"
        )
    if not view.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not view.limitations:
        raise ValueError("limitations must be non-empty")
    if not view.created_at:
        raise ValueError("created_at must be non-empty")
    n_req = len(REQUIRED_TRAIL_SCHEMA_TYPES)
    if view.n_schemas_required != n_req:
        raise ValueError(
            f"n_schemas_required must be {n_req}, got {view.n_schemas_required}"
        )
    if view.n_schemas_present != len(view.present_schema_types):
        raise ValueError("n_schemas_present must equal len(present_schema_types)")
    expected_missing = sorted(
        REQUIRED_TRAIL_SCHEMA_TYPES - set(view.present_schema_types)
    )
    if view.missing_schema_types != expected_missing:
        raise ValueError(
            f"missing_schema_types mismatch: expected {expected_missing}, "
            f"got {view.missing_schema_types}"
        )


def build_family_evidence_trail_view(
    *,
    fet_id: str,
    candidate_family_id: str,
    batch_id: str,
    pipeline_version: str,
    schema_event_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> FamilyEvidenceTrailView:
    events = [
        FamilySchemaEvent(
            schema_type=d["schema_type"],
            artifact_id=d["artifact_id"],
            created_at=d["created_at"],
        )
        for d in schema_event_dicts
    ]
    present_types = sorted({e.schema_type for e in events})
    missing_types = sorted(REQUIRED_TRAIL_SCHEMA_TYPES - set(present_types))
    n_required = len(REQUIRED_TRAIL_SCHEMA_TYPES)
    n_present = len(present_types)
    grade = _compute_grade(n_present, n_required)
    view = FamilyEvidenceTrailView(
        fet_id=fet_id,
        candidate_family_id=candidate_family_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        schema_events=events,
        present_schema_types=present_types,
        missing_schema_types=missing_types,
        n_schemas_present=n_present,
        n_schemas_required=n_required,
        trail_completeness_grade=grade,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_family_evidence_trail_view(view)
    return view


def format_family_evidence_trail_view(view: FamilyEvidenceTrailView) -> str:
    lines = [
        f"Family Evidence Trail View — {view.fet_id}",
        f"Family: {view.candidate_family_id}  |  Batch: {view.batch_id}  |  Pipeline: {view.pipeline_version}",
        f"Grade: {view.trail_completeness_grade}  |  Present: {view.n_schemas_present}/{view.n_schemas_required}",
    ]
    if view.present_schema_types:
        lines.append(f"Present: {', '.join(view.present_schema_types)}")
    if view.missing_schema_types:
        lines.append(f"Missing: {', '.join(view.missing_schema_types)}")
    lines.append(f"Created: {view.created_at}")
    if view.schema_events:
        lines.append("Events:")
        for e in view.schema_events:
            lines.append(f"  {e.schema_type}: {e.artifact_id} @ {e.created_at}")
    lines.append(f"Limitations: {'; '.join(view.limitations)}")
    lines.append(f"dry_lab_only: {view.dry_lab_only}")
    return "\n".join(lines)
