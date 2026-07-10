"""EGN- Evidence Gap Notification schema.

Machine-readable record of what evidence is missing and how to close
the gap. Makes "needs more work" outcomes actionable.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_EGN_GAP_TYPES: frozenset[str] = frozenset({
    "missing_wet_lab_validation",
    "missing_baseline_comparison",
    "missing_novelty_evidence",
    "missing_safety_clearance",
    "missing_reproducibility_data",
    "missing_reviewer_assessment",
    "claim_strength_mismatch",
    "missing_family_benchmark",
    "missing_adapter_baseline",
})

VALID_EGN_CLOSURE_ARTIFACT_TYPES: frozenset[str] = frozenset({
    "WHR", "CBR", "SEG", "CFC", "FNR", "PSC", "DCR", "RMC",
    "RDR", "CSD", "FBH", "CBF", "BXR", "ARG",
})

VALID_EGN_EFFORT_ESTIMATES: frozenset[str] = frozenset({
    "hours",
    "days",
    "weeks",
    "months",
    "unknown",
})

VALID_EGN_PRIORITIES: frozenset[str] = frozenset({
    "critical", "high", "medium", "low",
})

VALID_EGN_VERDICTS: frozenset[str] = frozenset({
    "actionable",
    "blocked_on_resources",
    "under_investigation",
    "accepted_limitation",
})


@dataclass
class EvidenceGapNotification:
    egn_id: str
    pipeline_version: str
    artifact_id: str
    gap_type: str
    gap_description: str
    closure_artifact_type: str
    closure_description: str
    effort_estimate: str
    priority: str
    verdict: str
    is_blocking: bool
    limitations: list[str]
    created_at: str
    dry_lab_only: bool = True


def build_evidence_gap_notification(
    *,
    egn_id: str,
    pipeline_version: str,
    artifact_id: str,
    gap_type: str,
    gap_description: str,
    closure_artifact_type: str,
    closure_description: str,
    effort_estimate: str,
    priority: str,
    verdict: str,
    is_blocking: bool,
    limitations: list[str],
    created_at: str,
) -> EvidenceGapNotification:
    egn = EvidenceGapNotification(
        egn_id=egn_id,
        pipeline_version=pipeline_version,
        artifact_id=artifact_id,
        gap_type=gap_type,
        gap_description=gap_description,
        closure_artifact_type=closure_artifact_type,
        closure_description=closure_description,
        effort_estimate=effort_estimate,
        priority=priority,
        verdict=verdict,
        is_blocking=is_blocking,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_evidence_gap_notification(egn)
    return egn


def validate_evidence_gap_notification(
    egn: EvidenceGapNotification,
) -> None:
    if not egn.egn_id.startswith("EGN-"):
        raise ValueError(
            f"egn_id must start with 'EGN-': {egn.egn_id!r}"
        )
    if not egn.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not egn.artifact_id:
        raise ValueError("artifact_id must be non-empty")
    if not egn.gap_description:
        raise ValueError("gap_description must be non-empty")
    if len(egn.gap_description) > 400:
        raise ValueError(
            f"gap_description exceeds 400 chars: {len(egn.gap_description)}"
        )
    if egn.gap_type not in VALID_EGN_GAP_TYPES:
        raise ValueError(
            f"gap_type {egn.gap_type!r} not in VALID_EGN_GAP_TYPES"
        )
    if not egn.closure_description:
        raise ValueError("closure_description must be non-empty")
    if egn.closure_artifact_type not in VALID_EGN_CLOSURE_ARTIFACT_TYPES:
        raise ValueError(
            f"closure_artifact_type {egn.closure_artifact_type!r} "
            f"not in VALID_EGN_CLOSURE_ARTIFACT_TYPES"
        )
    if egn.effort_estimate not in VALID_EGN_EFFORT_ESTIMATES:
        raise ValueError(
            f"effort_estimate {egn.effort_estimate!r} "
            f"not in VALID_EGN_EFFORT_ESTIMATES"
        )
    if egn.priority not in VALID_EGN_PRIORITIES:
        raise ValueError(
            f"priority {egn.priority!r} not in VALID_EGN_PRIORITIES"
        )
    if egn.verdict not in VALID_EGN_VERDICTS:
        raise ValueError(
            f"verdict {egn.verdict!r} not in VALID_EGN_VERDICTS"
        )
    if egn.dry_lab_only is not True:
        raise ValueError("dry_lab_only must be True")
    if not egn.limitations:
        raise ValueError("limitations must be non-empty")
    if not egn.created_at:
        raise ValueError("created_at must be non-empty")


def format_evidence_gap_notification(
    egn: EvidenceGapNotification,
) -> str:
    lines = [
        f"Evidence Gap Notification — {egn.egn_id}",
        f"Pipeline: {egn.pipeline_version}",
        f"Artifact: {egn.artifact_id}",
        f"Gap type: {egn.gap_type}",
        f"Gap description: {egn.gap_description}",
        f"Closure artifact type: {egn.closure_artifact_type}",
        f"Closure description: {egn.closure_description}",
        f"Effort estimate: {egn.effort_estimate}",
        f"Priority: {egn.priority}",
        f"Verdict: {egn.verdict}",
        f"Is blocking: {egn.is_blocking}",
    ]
    for lim in egn.limitations:
        lines.append(f"  Limitation: {lim}")
    lines.append(f"Dry lab only: {egn.dry_lab_only}")
    lines.append(f"Created: {egn.created_at}")
    return "\n".join(lines)
