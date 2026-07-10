"""Batch experiment priority ranker schema — Phase K K2.

Records the priority ordering of candidates for the next synthesis wave.
Documents priority method, resource constraints, and synthesis wave number,
making synthesis ordering auditable and defensible to external reviewers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

BPR_PREFIX = "BPR-"
CSR_PREFIX = "CSR-"

VALID_PRIORITY_METHODS = frozenset({
    "predicted_activity",
    "structural_diversity",
    "cost_efficiency",
    "risk_stratified",
    "novelty_first",
    "expert_ranked",
})

PRIORITY_RATIONALE_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
MAX_SYNTHESIS_WAVE_WARNING = 5
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class BatchExperimentPriorityRanker:
    bpr_id: str
    pipeline_version: str
    batch_id: str
    csr_id: str
    ranking_date: str
    priority_method: str
    top_priority_candidates: List[str]
    priority_rationale: str
    synthesis_wave: int
    resource_constraint_considered: bool
    notes: str = ""


@dataclass
class BatchExperimentPriorityRankerResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate(entry: BatchExperimentPriorityRanker) -> BatchExperimentPriorityRankerResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.bpr_id.startswith(BPR_PREFIX):
        errors.append(f"bpr_id must start with '{BPR_PREFIX}', got: {entry.bpr_id!r}")

    if not entry.pipeline_version.strip():
        errors.append("pipeline_version must be a non-empty string")

    if not entry.batch_id.strip():
        errors.append("batch_id must be a non-empty string")

    if not entry.csr_id.startswith(CSR_PREFIX):
        errors.append(f"csr_id must start with '{CSR_PREFIX}', got: {entry.csr_id!r}")

    if not _ISO_DATE_RE.match(entry.ranking_date):
        errors.append(
            f"ranking_date must be ISO format YYYY-MM-DD, got: {entry.ranking_date!r}"
        )

    if entry.priority_method not in VALID_PRIORITY_METHODS:
        errors.append(
            f"priority_method {entry.priority_method!r} not in valid set: "
            f"{sorted(VALID_PRIORITY_METHODS)}"
        )

    if len(entry.top_priority_candidates) == 0:
        errors.append(
            "top_priority_candidates must contain at least one candidate"
        )

    if not entry.priority_rationale.strip():
        errors.append("priority_rationale must be a non-empty string")
    elif len(entry.priority_rationale) > PRIORITY_RATIONALE_MAX_LENGTH:
        errors.append(
            f"priority_rationale exceeds {PRIORITY_RATIONALE_MAX_LENGTH} chars "
            f"(got {len(entry.priority_rationale)})"
        )

    if entry.synthesis_wave < 1:
        errors.append(
            f"synthesis_wave must be at least 1, got: {entry.synthesis_wave}"
        )

    if len(entry.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(entry.notes)})"
        )

    # Warnings
    if not entry.resource_constraint_considered:
        warnings.append(
            "resource_constraint_considered=False; "
            "synthesis priority without resource constraints may be suboptimal"
        )

    if entry.priority_method == "expert_ranked" and not entry.notes.strip():
        warnings.append(
            "priority_method='expert_ranked' without notes; "
            "expert ranking decisions should be documented"
        )

    if entry.synthesis_wave > MAX_SYNTHESIS_WAVE_WARNING:
        warnings.append(
            f"synthesis_wave={entry.synthesis_wave} is unusually high "
            f"(>{MAX_SYNTHESIS_WAVE_WARNING}); verify this is correct"
        )

    return BatchExperimentPriorityRankerResult(
        valid=len(errors) == 0, errors=errors, warnings=warnings
    )


def validate_dict(data: dict) -> BatchExperimentPriorityRankerResult:
    try:
        entry = BatchExperimentPriorityRanker(
            bpr_id=data.get("bpr_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            batch_id=data.get("batch_id", ""),
            csr_id=data.get("csr_id", ""),
            ranking_date=data.get("ranking_date", ""),
            priority_method=data.get("priority_method", ""),
            top_priority_candidates=list(data.get("top_priority_candidates", [])),
            priority_rationale=data.get("priority_rationale", ""),
            synthesis_wave=int(data.get("synthesis_wave", 0)),
            resource_constraint_considered=bool(
                data.get("resource_constraint_considered", False)
            ),
            notes=data.get("notes", ""),
        )
    except Exception as exc:
        return BatchExperimentPriorityRankerResult(
            valid=False, errors=[f"Construction error: {exc}"]
        )
    return validate(entry)
