"""Candidate selection rationale schema — Phase K K1.

Records why specific candidates were selected for a batch.
Documents selection strategy, ranking method, and calibration gate status,
making selection decisions auditable and comparable across batches.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

CSR_PREFIX = "CSR-"
BSP_PREFIX = "BSP-"

VALID_SELECTION_STRATEGIES = frozenset({
    "exploit",
    "explore",
    "diversity",
    "mixed",
})

VALID_RANKING_METHODS = frozenset({
    "composite_score",
    "diversity_filter",
    "novelty_weighted",
    "expert_review",
    "random_balanced",
    "calibration_guided",
})

RATIONALE_MAX_LENGTH = 400
NOTES_MAX_LENGTH = 300
MAX_CANDIDATE_COUNT_WARNING = 20
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class CandidateSelectionRationale:
    csr_id: str
    pipeline_version: str
    batch_id: str
    bsp_id: str
    selection_date: str
    selection_strategy: str
    candidate_count: int
    candidate_ids: List[str]
    ranking_method: str
    calibration_gate_passed: bool
    selection_rationale: str
    notes: str = ""


@dataclass
class CandidateSelectionRationaleResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate(entry: CandidateSelectionRationale) -> CandidateSelectionRationaleResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.csr_id.startswith(CSR_PREFIX):
        errors.append(f"csr_id must start with '{CSR_PREFIX}', got: {entry.csr_id!r}")

    if not entry.pipeline_version.strip():
        errors.append("pipeline_version must be a non-empty string")

    if not entry.batch_id.strip():
        errors.append("batch_id must be a non-empty string")

    if not entry.bsp_id.startswith(BSP_PREFIX):
        errors.append(f"bsp_id must start with '{BSP_PREFIX}', got: {entry.bsp_id!r}")

    if not _ISO_DATE_RE.match(entry.selection_date):
        errors.append(
            f"selection_date must be ISO format YYYY-MM-DD, got: {entry.selection_date!r}"
        )

    if entry.selection_strategy not in VALID_SELECTION_STRATEGIES:
        errors.append(
            f"selection_strategy {entry.selection_strategy!r} not in valid set: "
            f"{sorted(VALID_SELECTION_STRATEGIES)}"
        )

    if entry.candidate_count < 1:
        errors.append(
            f"candidate_count must be at least 1, got: {entry.candidate_count}"
        )

    if len(entry.candidate_ids) != entry.candidate_count:
        errors.append(
            f"candidate_ids length ({len(entry.candidate_ids)}) does not match "
            f"candidate_count ({entry.candidate_count})"
        )

    if entry.ranking_method not in VALID_RANKING_METHODS:
        errors.append(
            f"ranking_method {entry.ranking_method!r} not in valid set: "
            f"{sorted(VALID_RANKING_METHODS)}"
        )

    if not entry.calibration_gate_passed:
        errors.append(
            "calibration_gate_passed must be True; "
            "candidates cannot be selected without passing the calibration gate"
        )

    if not entry.selection_rationale.strip():
        errors.append("selection_rationale must be a non-empty string")
    elif len(entry.selection_rationale) > RATIONALE_MAX_LENGTH:
        errors.append(
            f"selection_rationale exceeds {RATIONALE_MAX_LENGTH} chars "
            f"(got {len(entry.selection_rationale)})"
        )

    if len(entry.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(entry.notes)})"
        )

    # Warnings
    if entry.candidate_count > MAX_CANDIDATE_COUNT_WARNING:
        warnings.append(
            f"candidate_count={entry.candidate_count} is unusually large (>{MAX_CANDIDATE_COUNT_WARNING}); "
            "verify this batch size is intentional"
        )

    if entry.ranking_method == "random_balanced" and not entry.notes.strip():
        warnings.append(
            "ranking_method='random_balanced' without notes; "
            "random selection should be justified in notes"
        )

    if entry.ranking_method == "expert_review" and not entry.notes.strip():
        warnings.append(
            "ranking_method='expert_review' without notes; "
            "expert review decisions should be documented"
        )

    return CandidateSelectionRationaleResult(
        valid=len(errors) == 0, errors=errors, warnings=warnings
    )


def validate_dict(data: dict) -> CandidateSelectionRationaleResult:
    try:
        entry = CandidateSelectionRationale(
            csr_id=data.get("csr_id", ""),
            pipeline_version=data.get("pipeline_version", ""),
            batch_id=data.get("batch_id", ""),
            bsp_id=data.get("bsp_id", ""),
            selection_date=data.get("selection_date", ""),
            selection_strategy=data.get("selection_strategy", ""),
            candidate_count=int(data.get("candidate_count", 0)),
            candidate_ids=list(data.get("candidate_ids", [])),
            ranking_method=data.get("ranking_method", ""),
            calibration_gate_passed=bool(data.get("calibration_gate_passed", False)),
            selection_rationale=data.get("selection_rationale", ""),
            notes=data.get("notes", ""),
        )
    except Exception as exc:
        return CandidateSelectionRationaleResult(
            valid=False, errors=[f"Construction error: {exc}"]
        )
    return validate(entry)
