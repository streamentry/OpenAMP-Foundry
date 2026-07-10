"""Certificate claim boundary schema — Phase B B2.

Documents what a certificate's scores do NOT prove. Prevents score-to-proof
drift by requiring explicit enumeration of unsupported claim classes before
a certificate can be shared externally.

This schema is the negative complement of ProofLadderLevelCertificate (PLC-):
while PLC- asserts what level IS supported, CCB- explicitly asserts what is NOT.

Claim classes (the things a dry-lab certificate cannot support):
  biological_activity    — actual in-vitro antimicrobial activity
  human_safety           — safety for human use or administration
  clinical_utility       — usefulness in clinical settings
  animal_efficacy        — efficacy in animal models
  therapeutic_indication — indication for therapeutic use
  regulatory_approval    — any regulatory or market approval
  mechanism_proof        — proven mechanism of action
  resistance_profile     — actual resistance/susceptibility profile
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

CCB_PREFIX = "CCB-"

ALL_CLAIM_CLASSES = frozenset({
    "biological_activity",
    "human_safety",
    "clinical_utility",
    "animal_efficacy",
    "therapeutic_indication",
    "regulatory_approval",
    "mechanism_proof",
    "resistance_profile",
})

MINIMUM_UNSUPPORTED_CLASSES = 3
BOUNDARY_STATEMENT_MAX_LENGTH = 600
NOTES_MAX_LENGTH = 300
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class CertificateClaimBoundary:
    ccb_id: str
    pipeline_version: str
    certificate_id: str
    candidate_id: str
    boundary_date: str
    unsupported_claim_classes: List[str]
    boundary_statement: str
    dry_lab_only: bool
    all_listed_classes_unsupported: bool
    notes: str = ""


def validate(boundary: CertificateClaimBoundary) -> List[str]:
    """Return list of error strings; empty list means valid."""
    errors: List[str] = []

    # Rule 1: ID prefix
    if not boundary.ccb_id.startswith(CCB_PREFIX):
        errors.append(
            f"ccb_id must start with '{CCB_PREFIX}', got: {boundary.ccb_id!r}"
        )

    # Rule 2: pipeline_version non-empty
    if not boundary.pipeline_version.strip():
        errors.append("pipeline_version must not be empty")

    # Rule 3: certificate_id non-empty
    if not boundary.certificate_id.strip():
        errors.append("certificate_id must not be empty")

    # Rule 4: candidate_id non-empty
    if not boundary.candidate_id.strip():
        errors.append("candidate_id must not be empty")

    # Rule 5: boundary_date ISO format
    if not _ISO_DATE_RE.match(boundary.boundary_date):
        errors.append(
            f"boundary_date must be YYYY-MM-DD, got: {boundary.boundary_date!r}"
        )

    # Rule 6: unsupported_claim_classes must be non-empty list
    if not boundary.unsupported_claim_classes:
        errors.append(
            "unsupported_claim_classes must not be empty — "
            "at least one claim class must be listed as unsupported"
        )

    # Rule 7: each claim class must be in ALL_CLAIM_CLASSES
    invalid_classes = [
        c for c in boundary.unsupported_claim_classes
        if c not in ALL_CLAIM_CLASSES
    ]
    if invalid_classes:
        errors.append(
            f"unsupported_claim_classes contains invalid values: {invalid_classes}; "
            f"valid classes are {sorted(ALL_CLAIM_CLASSES)}"
        )

    # Rule 8: minimum unsupported classes
    valid_listed = [c for c in boundary.unsupported_claim_classes if c in ALL_CLAIM_CLASSES]
    if len(valid_listed) < MINIMUM_UNSUPPORTED_CLASSES:
        errors.append(
            f"unsupported_claim_classes must list at least "
            f"{MINIMUM_UNSUPPORTED_CLASSES} valid claim classes; "
            f"got {len(valid_listed)}"
        )

    # Rule 9: boundary_statement non-empty and length
    if not boundary.boundary_statement.strip():
        errors.append("boundary_statement must not be empty")
    elif len(boundary.boundary_statement) > BOUNDARY_STATEMENT_MAX_LENGTH:
        errors.append(
            f"boundary_statement exceeds {BOUNDARY_STATEMENT_MAX_LENGTH} chars "
            f"(got {len(boundary.boundary_statement)})"
        )

    # Rule 10: dry_lab_only must be True for pipeline-generated boundaries
    if not boundary.dry_lab_only:
        errors.append(
            "dry_lab_only must be True — certificate claim boundaries are "
            "issued for dry-lab certificates only"
        )

    # Rule 11: all_listed_classes_unsupported must be True
    if not boundary.all_listed_classes_unsupported:
        errors.append(
            "all_listed_classes_unsupported must be True — all listed claim "
            "classes are verified as unsupported by this certificate"
        )

    # Rule 12: no duplicate claim classes
    seen = set()
    duplicates = []
    for c in boundary.unsupported_claim_classes:
        if c in seen:
            duplicates.append(c)
        seen.add(c)
    if duplicates:
        errors.append(
            f"unsupported_claim_classes contains duplicates: {duplicates}"
        )

    # Rule 13: notes length
    if len(boundary.notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"notes exceeds {NOTES_MAX_LENGTH} chars (got {len(boundary.notes)})"
        )

    # Warnings
    if len(valid_listed) < len(ALL_CLAIM_CLASSES):
        missing = sorted(ALL_CLAIM_CLASSES - set(boundary.unsupported_claim_classes))
        errors.append(
            f"WARNING: {len(missing)} claim class(es) not listed as unsupported: "
            f"{missing} — consider whether these are truly supported by this certificate"
        )
    if not boundary.notes.strip():
        errors.append(
            "WARNING: notes is empty — consider documenting why specific "
            "claim classes are not listed"
        )

    return errors


def validate_dict(data: dict) -> List[str]:
    """Validate a plain dict by constructing CertificateClaimBoundary first."""
    try:
        boundary = CertificateClaimBoundary(**data)
    except TypeError as exc:
        return [f"Schema construction error: {exc}"]
    return validate(boundary)
