"""Proof-ladder level certificate schema — Phase B B1.

Makes the proof-ladder level claim machine-checkable. Instead of a bare string
field in a certificate, a PLC- record asserts:
  - which candidate is being assessed
  - what level is claimed
  - what the maximum permissible level is (capped by evidence type)
  - which artifacts support the claim
  - what is explicitly NOT supported at this level

Proof-ladder levels (ordered by evidence strength):
  valid_input                    — passes format validation only
  reproducible_dry_lab_features  — features are reproducibly computed
  baseline_triaged               — beats or ties a cheap heuristic baseline
  leakage_aware_benchmark        — benchmark is split-clean
  multi_signal_candidate_evidence — multiple independent scorers agree
  expert_reviewed_assay_proposal — domain expert reviewed and proposed assay
  initial_qualified_assay_result — first wet-lab result obtained (qualified lab)
  safety_adjusted_follow_up_signal — follow-up with safety adjustment
  independent_replication        — independently replicated wet-lab result
  reusable_discovery_loop        — pipeline produces reusable discovery loop

Levels >= expert_reviewed_assay_proposal require human review before issuance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

PLC_PREFIX = "PLC-"

VALID_PROOF_LADDER_LEVELS = (
    "valid_input",
    "reproducible_dry_lab_features",
    "baseline_triaged",
    "leakage_aware_benchmark",
    "multi_signal_candidate_evidence",
    "expert_reviewed_assay_proposal",
    "initial_qualified_assay_result",
    "safety_adjusted_follow_up_signal",
    "independent_replication",
    "reusable_discovery_loop",
)

# Max level a dry-lab-only pipeline can issue without human review
DRY_LAB_MAX_LEVEL = "multi_signal_candidate_evidence"
DRY_LAB_MAX_INDEX = VALID_PROOF_LADDER_LEVELS.index(DRY_LAB_MAX_LEVEL)

VALID_EVIDENCE_TYPES = frozenset({
    "dry_lab_only",
    "dry_lab_plus_expert_review",
    "wet_lab_preliminary",
    "wet_lab_replicated",
})

VALID_VERIFIER_TYPES = frozenset({
    "automated_pipeline",
    "pipeline_owner",
    "external_domain_expert",
    "safety_officer",
    "independent_lab",
})

UNSUPPORTED_CLAIMS_MAX_LENGTH = 500
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class ProofLadderLevelCertificate:
    plc_id: str
    pipeline_version: str
    candidate_id: str
    certificate_id: str
    claimed_level: str
    evidence_type: str
    verifier_type: str
    verification_date: str
    supporting_artifact_ids: List[str]
    unsupported_claims: str
    human_review_required: bool
    human_review_completed: bool
    dry_lab_only: bool
    notes: str = ""


def validate(plc: ProofLadderLevelCertificate) -> List[str]:
    """Return list of error strings; empty list means valid."""
    errors: List[str] = []

    # Rule 1: ID prefix
    if not plc.plc_id.startswith(PLC_PREFIX):
        errors.append(
            f"plc_id must start with '{PLC_PREFIX}', got: {plc.plc_id!r}"
        )

    # Rule 2: pipeline_version non-empty
    if not plc.pipeline_version.strip():
        errors.append("pipeline_version must not be empty")

    # Rule 3: candidate_id non-empty
    if not plc.candidate_id.strip():
        errors.append("candidate_id must not be empty")

    # Rule 4: certificate_id non-empty
    if not plc.certificate_id.strip():
        errors.append("certificate_id must not be empty")

    # Rule 5: claimed_level is a valid proof-ladder level
    if plc.claimed_level not in VALID_PROOF_LADDER_LEVELS:
        errors.append(
            f"claimed_level must be one of {list(VALID_PROOF_LADDER_LEVELS)}, "
            f"got: {plc.claimed_level!r}"
        )

    # Rule 6: evidence_type vocabulary
    if plc.evidence_type not in VALID_EVIDENCE_TYPES:
        errors.append(
            f"evidence_type must be one of {sorted(VALID_EVIDENCE_TYPES)}, "
            f"got: {plc.evidence_type!r}"
        )

    # Rule 7: verifier_type vocabulary
    if plc.verifier_type not in VALID_VERIFIER_TYPES:
        errors.append(
            f"verifier_type must be one of {sorted(VALID_VERIFIER_TYPES)}, "
            f"got: {plc.verifier_type!r}"
        )

    # Rule 8: verification_date ISO format
    if not _ISO_DATE_RE.match(plc.verification_date):
        errors.append(
            f"verification_date must be YYYY-MM-DD, got: {plc.verification_date!r}"
        )

    # Rule 9: supporting_artifact_ids must be non-empty list
    if not plc.supporting_artifact_ids:
        errors.append(
            "supporting_artifact_ids must be non-empty — "
            "at least one artifact must support the claimed level"
        )

    # Rule 10: unsupported_claims non-empty (explicitly documenting what is NOT supported)
    if not plc.unsupported_claims.strip():
        errors.append(
            "unsupported_claims must not be empty — explicitly document what "
            "this level does NOT support (anti-overclaim guard)"
        )
    elif len(plc.unsupported_claims) > UNSUPPORTED_CLAIMS_MAX_LENGTH:
        errors.append(
            f"unsupported_claims exceeds {UNSUPPORTED_CLAIMS_MAX_LENGTH} chars "
            f"(got {len(plc.unsupported_claims)})"
        )

    # Rule 11: dry_lab_only=True caps level at DRY_LAB_MAX_LEVEL
    if plc.dry_lab_only and plc.claimed_level in VALID_PROOF_LADDER_LEVELS:
        claimed_index = VALID_PROOF_LADDER_LEVELS.index(plc.claimed_level)
        if claimed_index > DRY_LAB_MAX_INDEX:
            errors.append(
                f"dry_lab_only=True caps claimed_level at '{DRY_LAB_MAX_LEVEL}'; "
                f"got '{plc.claimed_level}' which requires wet-lab evidence"
            )

    # Rule 12: wet_lab levels require human_review_required=True
    if plc.claimed_level in VALID_PROOF_LADDER_LEVELS:
        claimed_index = VALID_PROOF_LADDER_LEVELS.index(plc.claimed_level)
        if claimed_index >= VALID_PROOF_LADDER_LEVELS.index("expert_reviewed_assay_proposal"):
            if not plc.human_review_required:
                errors.append(
                    f"claimed_level '{plc.claimed_level}' requires "
                    "human_review_required=True"
                )

    # Rule 13: if human_review_required then human_review_completed must track status
    if plc.human_review_required and not plc.human_review_completed:
        errors.append(
            "WARNING: human_review_required=True but human_review_completed=False "
            "— this certificate is pending human review"
        )

    # Rule 14: notes length
    if len(plc.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(plc.notes)})"
        )

    # Warnings
    if len(plc.supporting_artifact_ids) == 1:
        errors.append(
            "WARNING: only 1 supporting artifact — consider adding additional "
            "corroborating artifacts for stronger evidence"
        )
    if not plc.notes.strip():
        errors.append(
            "WARNING: notes is empty — consider documenting verification context"
        )

    return errors


def validate_dict(data: dict) -> List[str]:
    """Validate a plain dict by constructing ProofLadderLevelCertificate first."""
    try:
        plc = ProofLadderLevelCertificate(**data)
    except TypeError as exc:
        return [f"Schema construction error: {exc}"]
    return validate(plc)
