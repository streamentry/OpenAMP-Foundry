"""Batch experiment priority ranker for OpenAMP Foundry candidate synthesis planning."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

VALID_SYNTHESIS_COMPLEXITIES: set[str] = {
    "high",
    "low",
    "medium",
}
VALID_NOVELTY_TIERS: set[str] = {
    "high",
    "low",
    "medium",
}
VALID_EVIDENCE_LEVELS: set[int] = {1, 2, 3, 4, 5, 6}


@dataclass
class BatchPriorityEntry:
    """A priority ranking entry for one candidate in a synthesis batch."""

    priority_id: str
    batch_id: str
    candidate_id: str
    pipeline_version: str
    priority_rank: int
    priority_score: float
    evidence_level: int
    synthesis_complexity: str
    novelty_tier: str
    primary_rationale: str
    disqualifying_concerns: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


@dataclass
class BatchPriorityResult:
    """Result of validating a BatchPriorityEntry."""

    priority_id: str
    candidate_id: str
    priority_rank: int
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_batch_priority(entry: BatchPriorityEntry) -> BatchPriorityResult:
    """Validate a BatchPriorityEntry against policy rules."""
    errors: list[str] = []
    warnings: list[str] = []

    if not entry.priority_id or not str(entry.priority_id).strip():
        errors.append("priority_id must be non-empty")
    elif not entry.priority_id.startswith("PRI-"):
        errors.append(
            f"priority_id must start with 'PRI-', got: {entry.priority_id!r}"
        )

    if not entry.batch_id or not str(entry.batch_id).strip():
        errors.append("batch_id must be non-empty")

    if not entry.candidate_id or not str(entry.candidate_id).strip():
        errors.append("candidate_id must be non-empty")

    if not entry.pipeline_version or not str(entry.pipeline_version).strip():
        errors.append("pipeline_version must be non-empty")

    if not isinstance(entry.priority_rank, int) or entry.priority_rank < 1:
        errors.append(
            f"priority_rank must be an integer >= 1, got: {entry.priority_rank!r}"
        )

    if not isinstance(entry.priority_score, (int, float)) or not (0.0 <= float(entry.priority_score) <= 1.0):
        errors.append(
            f"priority_score must be a float between 0.0 and 1.0, got: {entry.priority_score!r}"
        )

    if not isinstance(entry.evidence_level, int) or entry.evidence_level not in VALID_EVIDENCE_LEVELS:
        errors.append(
            f"evidence_level must be one of {sorted(VALID_EVIDENCE_LEVELS)}, "
            f"got: {entry.evidence_level!r}"
        )

    if entry.synthesis_complexity not in VALID_SYNTHESIS_COMPLEXITIES:
        errors.append(
            f"synthesis_complexity must be one of {sorted(VALID_SYNTHESIS_COMPLEXITIES)}, "
            f"got: {entry.synthesis_complexity!r}"
        )

    if entry.novelty_tier not in VALID_NOVELTY_TIERS:
        errors.append(
            f"novelty_tier must be one of {sorted(VALID_NOVELTY_TIERS)}, "
            f"got: {entry.novelty_tier!r}"
        )

    if not entry.primary_rationale or not str(entry.primary_rationale).strip():
        errors.append("primary_rationale must be non-empty")

    if not entry.dry_lab_only:
        errors.append("dry_lab_only must be True for batch priority entries")

    # Warnings
    if isinstance(entry.evidence_level, int) and entry.evidence_level <= 2:
        warnings.append(
            f"evidence_level is {entry.evidence_level} (low): "
            "consider additional evidence before committing to synthesis"
        )

    if (
        isinstance(entry.priority_rank, int)
        and entry.priority_rank == 1
        and entry.synthesis_complexity == "high"
    ):
        warnings.append(
            "top-ranked candidate has high synthesis complexity: "
            "confirm synthesis feasibility before ordering"
        )

    if isinstance(entry.priority_score, (int, float)) and float(entry.priority_score) < 0.3:
        warnings.append(
            f"priority_score is {entry.priority_score:.2f} (below 0.30): "
            "consider whether this candidate meets the synthesis threshold"
        )

    return BatchPriorityResult(
        priority_id=entry.priority_id,
        candidate_id=entry.candidate_id,
        priority_rank=entry.priority_rank,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_batch_priority_dict(d: dict) -> BatchPriorityResult:
    """Validate a dict representation of a BatchPriorityEntry."""
    required = [
        "batch_id",
        "candidate_id",
        "evidence_level",
        "novelty_tier",
        "pipeline_version",
        "primary_rationale",
        "priority_id",
        "priority_rank",
        "priority_score",
        "synthesis_complexity",
    ]
    missing = [f for f in required if f not in d]
    if missing:
        return BatchPriorityResult(
            priority_id=d.get("priority_id", ""),
            candidate_id=d.get("candidate_id", ""),
            priority_rank=d.get("priority_rank", 0),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )
    entry = BatchPriorityEntry(
        priority_id=d["priority_id"],
        batch_id=d["batch_id"],
        candidate_id=d["candidate_id"],
        pipeline_version=d["pipeline_version"],
        priority_rank=d["priority_rank"],
        priority_score=d["priority_score"],
        evidence_level=d["evidence_level"],
        synthesis_complexity=d["synthesis_complexity"],
        novelty_tier=d["novelty_tier"],
        primary_rationale=d["primary_rationale"],
        disqualifying_concerns=d.get("disqualifying_concerns", []),
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_batch_priority(entry)
