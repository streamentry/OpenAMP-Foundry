"""EHP- External Handoff Packet schema.

Machine-readable record of what was bundled into an external handoff
(to a wet lab, external reviewer, collaborator, etc.) and whether safety
was cleared before transfer.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_EHP_HANDOFF_PURPOSES: frozenset[str] = frozenset({
    "wet_lab_synthesis",
    "external_review",
    "regulatory_filing",
    "publication_support",
    "collaboration_transfer",
})

VALID_EHP_ARTIFACT_TYPES: frozenset[str] = frozenset({
    "WHR", "CBR", "SEG", "CFC", "FNR", "PSC", "DCR", "RMC",
    "RDR", "CSD", "FBH", "CBF", "BXR", "ARG", "EGN",
})

VALID_EHP_VERDICTS: frozenset[str] = frozenset({
    "complete",
    "partial",
    "incomplete",
})

SAFETY_CLEARANCE_ARTIFACT_TYPES: frozenset[str] = frozenset({"PSC", "FNR"})
MINIMUM_ARTIFACTS_FOR_COMPLETE: int = 4


@dataclass
class ExternalHandoffPacket:
    ehp_id: str
    pipeline_version: str
    candidate_family_id: str
    handoff_purpose: str
    included_artifact_types: list[str]
    n_artifacts_included: int
    has_safety_clearance: bool
    verdict: str
    limitations: list[str]
    dry_lab_only: bool = True
    created_at: str = ""


def build_external_handoff_packet(
    *,
    ehp_id: str,
    pipeline_version: str,
    candidate_family_id: str,
    handoff_purpose: str,
    included_artifact_types: list[str],
    limitations: list[str],
    created_at: str,
) -> ExternalHandoffPacket:
    n_artifacts_included = len(included_artifact_types)
    has_safety_clearance = bool(
        SAFETY_CLEARANCE_ARTIFACT_TYPES & set(included_artifact_types)
    )
    if n_artifacts_included < 2:
        verdict = "incomplete"
    elif n_artifacts_included < MINIMUM_ARTIFACTS_FOR_COMPLETE:
        verdict = "partial"
    else:
        verdict = "complete"

    ehp = ExternalHandoffPacket(
        ehp_id=ehp_id,
        pipeline_version=pipeline_version,
        candidate_family_id=candidate_family_id,
        handoff_purpose=handoff_purpose,
        included_artifact_types=included_artifact_types,
        n_artifacts_included=n_artifacts_included,
        has_safety_clearance=has_safety_clearance,
        verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_external_handoff_packet(ehp)
    return ehp


def validate_external_handoff_packet(
    ehp: ExternalHandoffPacket,
) -> None:
    if not ehp.ehp_id.startswith("EHP-"):
        raise ValueError(
            f"ehp_id must start with 'EHP-': {ehp.ehp_id!r}"
        )
    if not ehp.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not ehp.candidate_family_id:
        raise ValueError("candidate_family_id must be non-empty")
    if ehp.handoff_purpose not in VALID_EHP_HANDOFF_PURPOSES:
        raise ValueError(
            f"handoff_purpose {ehp.handoff_purpose!r} not in VALID_EHP_HANDOFF_PURPOSES"
        )
    seen: set[str] = set()
    for atype in ehp.included_artifact_types:
        if atype not in VALID_EHP_ARTIFACT_TYPES:
            raise ValueError(
                f"artifact type {atype!r} not in VALID_EHP_ARTIFACT_TYPES"
            )
        if atype in seen:
            raise ValueError(
                f"duplicate artifact type {atype!r} in included_artifact_types"
            )
        seen.add(atype)
    if not ehp.limitations:
        raise ValueError("limitations must be non-empty")
    if ehp.dry_lab_only is not True:
        raise ValueError("dry_lab_only must be True")
    if not ehp.created_at:
        raise ValueError("created_at must be non-empty")
    if (
        ehp.handoff_purpose == "wet_lab_synthesis"
        and not ehp.has_safety_clearance
    ):
        raise ValueError(
            "wet_lab_synthesis handoff requires safety clearance "
            "artifact (PSC or FNR)"
        )


def format_external_handoff_packet(
    ehp: ExternalHandoffPacket,
) -> str:
    lines = [
        f"External Handoff Packet — {ehp.ehp_id}",
        f"Pipeline: {ehp.pipeline_version}",
        f"Candidate family: {ehp.candidate_family_id}",
        f"Handoff purpose: {ehp.handoff_purpose}",
        f"Artifacts included ({ehp.n_artifacts_included}): {', '.join(ehp.included_artifact_types)}",
        f"Has safety clearance: {ehp.has_safety_clearance}",
        f"Verdict: {ehp.verdict}",
    ]
    for lim in ehp.limitations:
        lines.append(f"  Limitation: {lim}")
    lines.append(f"Dry lab only: {ehp.dry_lab_only}")
    lines.append(f"Created: {ehp.created_at}")
    return "\n".join(lines)
