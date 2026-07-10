"""External sharing clearance schema — Phase Q Q3.

Records the formal clearance event when a PilotEvidencePackage (PEP) is
shared with an external lab partner. Makes external sharing auditable:
the dry-lab-only caveat must be confirmed, the external partner must be
identified by anonymous token, and the sharing event is timestamped.

This is the final release gate in Phase Q — no PEP should leave the
foundry without an ESC record.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

ESC_PREFIX = "ESC-"
PEP_PREFIX = "PEP-"
PRE_PREFIX = "PRE-"

VALID_SHARING_PURPOSES = frozenset({
    "pilot_experiment",
    "peer_review",
    "collaboration",
})

NOTES_MAX_LENGTH = 400


@dataclass
class ExternalSharingClearance:
    """Clearance record for sharing a PEP with an external lab partner."""

    esc_id: str
    pipeline_version: str
    pep_id: str  # must start with "PEP-"
    pre_id: str  # must start with "PRE-"
    external_lab_token: str  # anonymized lab identifier, no PII
    sharing_date: str  # ISO YYYY-MM-DD
    caveat_confirmed: bool  # must be True — dry-lab-only caveat was communicated
    dry_lab_only_acknowledged: bool  # must be True — partner acknowledged dry-lab status
    sharing_purpose: str  # {pilot_experiment, peer_review, collaboration}
    sharing_notes: str  # max 400 chars
    reviewer: str
    dry_lab_only: bool = True


@dataclass
class ExternalSharingClearanceResult:
    esc_id: str
    pep_id: str
    pre_id: str
    sharing_purpose: str
    passed: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    dry_lab_only: bool = True


def validate_external_sharing_clearance(
    entry: ExternalSharingClearance,
) -> ExternalSharingClearanceResult:
    errors: List[str] = []
    warnings: List[str] = []

    # Rule 1: ESC- prefix
    if not entry.esc_id.startswith(ESC_PREFIX):
        errors.append(
            f"esc_id must start with '{ESC_PREFIX}', got '{entry.esc_id}'"
        )

    # Rule 2: PEP- prefix
    if not entry.pep_id.startswith(PEP_PREFIX):
        errors.append(
            f"pep_id must start with '{PEP_PREFIX}', got '{entry.pep_id}'"
        )

    # Rule 3: PRE- prefix
    if not entry.pre_id.startswith(PRE_PREFIX):
        errors.append(
            f"pre_id must start with '{PRE_PREFIX}', got '{entry.pre_id}'"
        )

    # Rule 4: non-empty required strings
    for fname, val in [
        ("pipeline_version", entry.pipeline_version),
        ("external_lab_token", entry.external_lab_token),
        ("reviewer", entry.reviewer),
    ]:
        if not val or not val.strip():
            errors.append(f"{fname} must not be empty")

    # Rule 5: sharing_date must be ISO YYYY-MM-DD
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", entry.sharing_date):
        errors.append(
            f"sharing_date must be ISO format YYYY-MM-DD, got '{entry.sharing_date}'"
        )

    # Rule 6: caveat_confirmed must be True
    if not entry.caveat_confirmed:
        errors.append(
            "caveat_confirmed must be True — dry-lab-only caveat must be communicated"
            " before external sharing"
        )

    # Rule 7: dry_lab_only_acknowledged must be True
    if not entry.dry_lab_only_acknowledged:
        errors.append(
            "dry_lab_only_acknowledged must be True — external partner must acknowledge"
            " dry-lab-only status before receiving the package"
        )

    # Rule 8: valid sharing purpose
    if entry.sharing_purpose not in VALID_SHARING_PURPOSES:
        errors.append(
            f"sharing_purpose must be one of {sorted(VALID_SHARING_PURPOSES)}, "
            f"got '{entry.sharing_purpose}'"
        )

    # Rule 9: notes length
    if len(entry.sharing_notes) > NOTES_MAX_LENGTH:
        errors.append(
            f"sharing_notes must be at most {NOTES_MAX_LENGTH} characters, "
            f"got {len(entry.sharing_notes)}"
        )

    # Warning 1: no sharing_notes provided
    if not entry.sharing_notes.strip():
        warnings.append(
            "sharing_notes is empty — consider documenting the context of this sharing event"
        )

    # Warning 2: pilot_experiment is highest stakes
    if entry.sharing_purpose == "pilot_experiment":
        warnings.append(
            "sharing_purpose is 'pilot_experiment' — confirm wet-lab partner has reviewed"
            " all safety clearance artifacts before proceeding"
        )

    # Warning 3: collaboration without notes is unusual
    if entry.sharing_purpose == "collaboration" and not entry.sharing_notes.strip():
        warnings.append(
            "sharing_purpose is 'collaboration' with no sharing_notes — document the"
            " scope of the collaboration"
        )

    passed = len(errors) == 0
    return ExternalSharingClearanceResult(
        esc_id=entry.esc_id,
        pep_id=entry.pep_id,
        pre_id=entry.pre_id,
        sharing_purpose=entry.sharing_purpose,
        passed=passed,
        errors=errors,
        warnings=warnings,
        dry_lab_only=entry.dry_lab_only,
    )


def validate_external_sharing_clearance_dict(
    data: dict,
) -> ExternalSharingClearanceResult:
    entry = ExternalSharingClearance(
        esc_id=data.get("esc_id", ""),
        pipeline_version=data.get("pipeline_version", ""),
        pep_id=data.get("pep_id", ""),
        pre_id=data.get("pre_id", ""),
        external_lab_token=data.get("external_lab_token", ""),
        sharing_date=data.get("sharing_date", ""),
        caveat_confirmed=bool(data.get("caveat_confirmed", False)),
        dry_lab_only_acknowledged=bool(data.get("dry_lab_only_acknowledged", False)),
        sharing_purpose=data.get("sharing_purpose", ""),
        sharing_notes=data.get("sharing_notes", ""),
        reviewer=data.get("reviewer", ""),
        dry_lab_only=bool(data.get("dry_lab_only", True)),
    )
    return validate_external_sharing_clearance(entry)
