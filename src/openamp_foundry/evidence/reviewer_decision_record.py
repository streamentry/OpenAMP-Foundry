"""RDR- Reviewer Decision Record schema.

Machine-parseable record of an expert reviewer's decision about a candidate
family. Makes reviewer feedback auditable and comparable across reviewers.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_RDR_DIMENSIONS: frozenset[str] = frozenset({
    "novelty",
    "controls",
    "safety",
    "synthesis",
    "claim_scope",
})

VALID_RDR_RATINGS: frozenset[str] = frozenset({
    "acceptable",
    "concerns_noted",
    "requires_revision",
    "not_assessed",
})

VALID_RDR_OVERALL_DECISIONS: frozenset[str] = frozenset({
    "approved",
    "approved_with_conditions",
    "rejected",
    "deferred",
})

BLOCKING_RATINGS: frozenset[str] = frozenset({"requires_revision"})

REQUIRED_DIMENSIONS: tuple[str, ...] = ("novelty", "safety", "claim_scope")


@dataclass
class DimensionRating:
    dimension: str
    rating: str
    notes: str


@dataclass
class ReviewerDecisionRecord:
    rdr_id: str
    pipeline_version: str
    artifact_id: str
    reviewer_role: str
    dimension_ratings: list[DimensionRating]
    n_dimensions_assessed: int
    n_blocking: int
    has_unassessed_required: bool
    overall_decision: str
    decision_notes: str
    dry_lab_only: bool = True
    created_at: str = ""


def build_reviewer_decision_record(
    *,
    rdr_id: str,
    pipeline_version: str,
    artifact_id: str,
    reviewer_role: str,
    dimension_ratings: list[DimensionRating],
    overall_decision: str,
    decision_notes: str,
    created_at: str,
) -> ReviewerDecisionRecord:
    n_dimensions_assessed = sum(
        1 for dr in dimension_ratings if dr.rating != "not_assessed"
    )
    n_blocking = sum(
        1 for dr in dimension_ratings if dr.rating in BLOCKING_RATINGS
    )
    assessed_dims = {
        dr.dimension for dr in dimension_ratings if dr.rating != "not_assessed"
    }
    has_unassessed_required = any(
        req not in assessed_dims for req in REQUIRED_DIMENSIONS
    )

    rdr = ReviewerDecisionRecord(
        rdr_id=rdr_id,
        pipeline_version=pipeline_version,
        artifact_id=artifact_id,
        reviewer_role=reviewer_role,
        dimension_ratings=dimension_ratings,
        n_dimensions_assessed=n_dimensions_assessed,
        n_blocking=n_blocking,
        has_unassessed_required=has_unassessed_required,
        overall_decision=overall_decision,
        decision_notes=decision_notes,
        dry_lab_only=True,
        created_at=created_at,
    )
    validate_reviewer_decision_record(rdr)
    return rdr


def validate_reviewer_decision_record(
    rdr: ReviewerDecisionRecord,
) -> None:
    if not rdr.rdr_id.startswith("RDR-"):
        raise ValueError(
            f"rdr_id must start with 'RDR-': {rdr.rdr_id!r}"
        )
    if not rdr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not rdr.artifact_id:
        raise ValueError("artifact_id must be non-empty")
    if not rdr.reviewer_role:
        raise ValueError("reviewer_role must be non-empty")

    seen = set()
    for dr in rdr.dimension_ratings:
        if dr.dimension not in VALID_RDR_DIMENSIONS:
            raise ValueError(
                f"dimension {dr.dimension!r} not in VALID_RDR_DIMENSIONS"
            )
        if dr.rating not in VALID_RDR_RATINGS:
            raise ValueError(
                f"rating {dr.rating!r} not in VALID_RDR_RATINGS"
            )
        if len(dr.notes) > 300:
            raise ValueError(
                f"notes exceeds 300 chars: {len(dr.notes)}"
            )
        if dr.dimension in seen:
            raise ValueError(f"duplicate dimension: {dr.dimension}")
        seen.add(dr.dimension)

    expected_n_assessed = sum(
        1 for dr in rdr.dimension_ratings if dr.rating != "not_assessed"
    )
    if rdr.n_dimensions_assessed != expected_n_assessed:
        raise ValueError(
            f"n_dimensions_assessed {rdr.n_dimensions_assessed} != "
            f"{expected_n_assessed} (expected)"
        )

    expected_n_blocking = sum(
        1 for dr in rdr.dimension_ratings if dr.rating in BLOCKING_RATINGS
    )
    if rdr.n_blocking != expected_n_blocking:
        raise ValueError(
            f"n_blocking {rdr.n_blocking} != {expected_n_blocking} (expected)"
        )

    assessed_dims = {
        dr.dimension for dr in rdr.dimension_ratings if dr.rating != "not_assessed"
    }
    expected_has_unassessed = any(
        req not in assessed_dims for req in REQUIRED_DIMENSIONS
    )
    if rdr.has_unassessed_required != expected_has_unassessed:
        raise ValueError(
            f"has_unassessed_required {rdr.has_unassessed_required} != "
            f"{expected_has_unassessed} (expected)"
        )

    if rdr.overall_decision not in VALID_RDR_OVERALL_DECISIONS:
        raise ValueError(
            f"overall_decision {rdr.overall_decision!r} "
            f"not in VALID_RDR_OVERALL_DECISIONS"
        )

    if rdr.overall_decision == "approved":
        if rdr.n_blocking > 0:
            raise ValueError(
                f"overall_decision 'approved' but n_blocking={rdr.n_blocking} > 0"
            )
        if rdr.has_unassessed_required:
            raise ValueError(
                "overall_decision 'approved' but has_unassessed_required is True"
            )
    if rdr.overall_decision == "approved_with_conditions":
        if rdr.n_blocking < 1:
            raise ValueError(
                f"overall_decision 'approved_with_conditions' but "
                f"n_blocking={rdr.n_blocking} < 1"
            )
        if rdr.n_blocking >= len(rdr.dimension_ratings):
            raise ValueError(
                "overall_decision 'approved_with_conditions' but "
                "all dimensions are blocking"
            )
    if rdr.overall_decision == "rejected":
        if rdr.n_blocking < 1:
            raise ValueError(
                f"overall_decision 'rejected' but n_blocking={rdr.n_blocking} < 1"
            )

    if rdr.dry_lab_only is not True:
        raise ValueError("dry_lab_only must be True")
    if not rdr.created_at:
        raise ValueError("created_at must be non-empty")


def format_reviewer_decision_record(
    rdr: ReviewerDecisionRecord,
) -> str:
    lines = [
        f"Reviewer Decision Record — {rdr.rdr_id}",
        f"Pipeline: {rdr.pipeline_version}",
        f"Artifact: {rdr.artifact_id}",
        f"Reviewer role: {rdr.reviewer_role}",
        f"Dimensions assessed: {rdr.n_dimensions_assessed}"
        f"/{len(rdr.dimension_ratings)}",
        f"Blocking issues: {rdr.n_blocking}",
        f"Unassessed required: {rdr.has_unassessed_required}",
    ]
    for dr in rdr.dimension_ratings:
        lines.append(f"  {dr.dimension}: {dr.rating} — {dr.notes}")
    lines.append(f"Overall decision: {rdr.overall_decision}")
    if rdr.decision_notes:
        lines.append(f"Decision notes: {rdr.decision_notes}")
    lines.append(f"Dry lab only: {rdr.dry_lab_only}")
    lines.append(f"Created: {rdr.created_at}")
    return "\n".join(lines)
