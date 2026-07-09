from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

VALID_CLAIM_TYPES: set[str] = {
    "activity_prediction",
    "calibration_statement",
    "novelty_claim",
    "performance_comparison",
    "reproducibility_claim",
    "safety_assessment",
    "selection_rationale",
}

VALID_EVIDENCE_LEVELS: set[int] = {1, 2, 3, 4, 5, 6}
MAX_CLAIM_TEXT_LENGTH: int = 500
LONG_CLAIM_TEXT_THRESHOLD: int = 300
WEAK_EVIDENCE_THRESHOLD: int = 2


@dataclass
class ClaimToEvidenceEntry:
    mapping_id: str
    batch_id: str
    pipeline_version: str
    claim_text: str
    claim_type: str
    supporting_artifact_ids: List[str]
    evidence_level: int
    pre_specified: bool
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class ClaimToEvidenceResult:
    mapping_id: str
    batch_id: str
    claim_type: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_claim_to_evidence(entry: ClaimToEvidenceEntry) -> ClaimToEvidenceResult:
    errors: List[str] = []
    warnings: List[str] = []

    if not entry.mapping_id.startswith("CEM-"):
        errors.append(f"mapping_id must start with 'CEM-', got '{entry.mapping_id}'")

    if not entry.claim_text:
        errors.append("claim_text must not be empty")
    elif len(entry.claim_text) > MAX_CLAIM_TEXT_LENGTH:
        errors.append(
            f"claim_text exceeds {MAX_CLAIM_TEXT_LENGTH} characters "
            f"(got {len(entry.claim_text)})"
        )

    if entry.claim_type not in VALID_CLAIM_TYPES:
        errors.append(
            f"claim_type '{entry.claim_type}' is not valid; "
            f"must be one of {sorted(VALID_CLAIM_TYPES)}"
        )

    if not entry.supporting_artifact_ids:
        errors.append("supporting_artifact_ids must contain at least one artifact ID")

    if entry.evidence_level not in VALID_EVIDENCE_LEVELS:
        errors.append(
            f"evidence_level {entry.evidence_level} is not valid; "
            f"must be one of {sorted(VALID_EVIDENCE_LEVELS)}"
        )

    if not entry.reviewer:
        errors.append("reviewer must not be empty")

    if not entry.dry_lab_only:
        errors.append(
            "dry_lab_only must be True for claim-to-evidence mappings "
            "(computational claims only)"
        )

    if not errors:
        if not entry.pre_specified:
            warnings.append(
                "pre_specified=False: this claim was not pre-specified before analysis; "
                "treat as exploratory and interpret with caution"
            )

        if entry.evidence_level <= WEAK_EVIDENCE_THRESHOLD:
            warnings.append(
                f"evidence_level={entry.evidence_level} is weak (<=2); "
                "consider seeking stronger supporting evidence"
            )

        if len(entry.supporting_artifact_ids) == 1:
            warnings.append(
                "only one supporting artifact; consider seeking corroborating evidence "
                "from a second independent artifact"
            )

        if entry.claim_text and len(entry.claim_text) > LONG_CLAIM_TEXT_THRESHOLD:
            warnings.append(
                f"claim_text is long ({len(entry.claim_text)} chars > "
                f"{LONG_CLAIM_TEXT_THRESHOLD}); consider condensing for clarity"
            )

    passed = len(errors) == 0
    return ClaimToEvidenceResult(
        mapping_id=entry.mapping_id,
        batch_id=entry.batch_id,
        claim_type=entry.claim_type,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=True,
    )


def validate_claim_to_evidence_dict(d: dict) -> ClaimToEvidenceResult:
    required_fields = [
        "mapping_id",
        "batch_id",
        "pipeline_version",
        "claim_text",
        "claim_type",
        "supporting_artifact_ids",
        "evidence_level",
        "pre_specified",
        "reviewer",
    ]
    missing = [f for f in required_fields if f not in d]
    if missing:
        return ClaimToEvidenceResult(
            mapping_id=d.get("mapping_id", "UNKNOWN"),
            batch_id=d.get("batch_id", "UNKNOWN"),
            claim_type=d.get("claim_type", "UNKNOWN"),
            passed=False,
            errors=[f"Missing required fields: {missing}"],
            dry_lab_only=True,
        )

    entry = ClaimToEvidenceEntry(
        mapping_id=d["mapping_id"],
        batch_id=d["batch_id"],
        pipeline_version=d["pipeline_version"],
        claim_text=d["claim_text"],
        claim_type=d["claim_type"],
        supporting_artifact_ids=d["supporting_artifact_ids"],
        evidence_level=d["evidence_level"],
        pre_specified=d["pre_specified"],
        reviewer=d["reviewer"],
        dry_lab_only=d.get("dry_lab_only", True),
    )
    return validate_claim_to_evidence(entry)
