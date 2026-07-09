"""Candidate summary card schema (Phase L L3).

Validates publication-ready per-candidate structured summaries
for preprints and external reviewer packets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

VALID_ACTIVITY_LABELS: set[str] = {
    "high_activity",
    "inactive",
    "low_activity",
    "moderate_activity",
    "uncertain",
}

VALID_AMINO_ACIDS: set[str] = set("ACDEFGHIKLMNPQRSTVWY")
LONG_PEPTIDE_THRESHOLD: int = 50
VALID_EVIDENCE_LEVELS: set[int] = {1, 2, 3, 4, 5, 6}


@dataclass
class CandidateSummaryCardEntry:
    """One candidate summary card record."""

    card_id: str
    candidate_id: str
    batch_id: str
    pipeline_version: str
    sequence: str
    sequence_length: int
    evidence_level: int
    predicted_activity: str
    safety_flags: List[str]
    selection_rationale_id: str
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class CandidateSummaryCardResult:
    """Validation result for a CandidateSummaryCardEntry."""

    card_id: str
    candidate_id: str
    sequence_length: int
    passed: bool
    errors: List[str]
    warnings: List[str]
    dry_lab_only: bool = True


def validate_candidate_summary_card(
    entry: CandidateSummaryCardEntry,
) -> CandidateSummaryCardResult:
    """Validate a CandidateSummaryCardEntry.  Returns a CandidateSummaryCardResult."""
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.card_id.startswith("CRD-"):
        errors.append("card_id must start with 'CRD-'")

    if not entry.candidate_id:
        errors.append("candidate_id must not be empty")

    if not entry.batch_id:
        errors.append("batch_id must not be empty")

    if not entry.pipeline_version:
        errors.append("pipeline_version must not be empty")

    if not entry.sequence:
        errors.append("sequence must not be empty")
    else:
        invalid_chars = set(entry.sequence.upper()) - VALID_AMINO_ACIDS
        if invalid_chars:
            errors.append(
                f"sequence contains invalid amino acid characters: {sorted(invalid_chars)}"
            )
        if len(entry.sequence) != entry.sequence_length:
            errors.append(
                f"sequence_length ({entry.sequence_length}) does not match "
                f"actual length of sequence ({len(entry.sequence)})"
            )

    if entry.evidence_level not in VALID_EVIDENCE_LEVELS:
        errors.append(
            f"evidence_level {entry.evidence_level} is not valid; "
            f"must be one of {sorted(VALID_EVIDENCE_LEVELS)}"
        )

    if entry.predicted_activity not in VALID_ACTIVITY_LABELS:
        errors.append(
            f"predicted_activity '{entry.predicted_activity}' is not valid; "
            f"must be one of {sorted(VALID_ACTIVITY_LABELS)}"
        )

    if not entry.selection_rationale_id.startswith("SEL-"):
        errors.append("selection_rationale_id must start with 'SEL-'")

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if entry.dry_lab_only is not True:
        errors.append("dry_lab_only must be True")

    if not errors:
        if entry.evidence_level <= 2:
            warnings.append(
                f"evidence_level {entry.evidence_level} is low (≤2); "
                "apply extra scrutiny to computational predictions."
            )

        if entry.safety_flags:
            warnings.append(
                f"Safety concerns flagged: {entry.safety_flags}. "
                "Review before considering synthesis."
            )

        if entry.predicted_activity == "uncertain":
            warnings.append(
                "predicted_activity is 'uncertain'; prioritize candidates "
                "with clearer predictions for the synthesis wave."
            )

        if entry.sequence_length > LONG_PEPTIDE_THRESHOLD:
            warnings.append(
                f"Sequence length {entry.sequence_length} exceeds "
                f"{LONG_PEPTIDE_THRESHOLD}; synthesis cost may be high."
            )

    return CandidateSummaryCardResult(
        card_id=entry.card_id,
        candidate_id=entry.candidate_id,
        sequence_length=entry.sequence_length,
        passed=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def validate_candidate_summary_card_dict(d: dict) -> CandidateSummaryCardResult:
    """Validate a dict representation of a CandidateSummaryCardEntry."""
    required = [
        "card_id",
        "candidate_id",
        "batch_id",
        "pipeline_version",
        "sequence",
        "sequence_length",
        "evidence_level",
        "predicted_activity",
        "safety_flags",
        "selection_rationale_id",
        "reviewer",
    ]
    for key in required:
        if key not in d:
            return CandidateSummaryCardResult(
                card_id=d.get("card_id", ""),
                candidate_id=d.get("candidate_id", ""),
                sequence_length=0,
                passed=False,
                errors=[f"missing required field: {key}"],
                warnings=[],
            )

    entry = CandidateSummaryCardEntry(
        card_id=d["card_id"],
        candidate_id=d["candidate_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        sequence=d["sequence"],
        sequence_length=d["sequence_length"],
        evidence_level=d["evidence_level"],
        predicted_activity=d["predicted_activity"],
        safety_flags=d["safety_flags"],
        selection_rationale_id=d["selection_rationale_id"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_candidate_summary_card(entry)
