"""CSD- Claim Strength Downgrade Record schema.

Auditable trail for every claim downgrade triggered by benchmark results,
reviewer challenges, cheap enemy refutations, data quality issues, scope
creep detection, or calibration failures. Prevents silent claim drift upward
after challenges.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_CSD_CLAIM_CLASSES: frozenset[str] = frozenset({
    "novelty",
    "activity",
    "selectivity",
    "safety",
    "reproducibility",
    "calibration_improvement",
    "cheap_baseline_outperformed",
})

VALID_CSD_TRIGGER_TYPES: frozenset[str] = frozenset({
    "benchmark_result",
    "reviewer_challenge",
    "cheap_enemy_refutation",
    "data_quality_issue",
    "scope_creep_detected",
    "calibration_failure",
})

VALID_CSD_DOWNGRADE_LEVELS: frozenset[str] = frozenset({
    "minor",
    "major",
    "retracted",
})

PROOF_LADDER_LEVELS: tuple[str, ...] = (
    "speculative",
    "plausible_candidate",
    "multi_signal_candidate_evidence",
    "expert_reviewed_assay_proposal",
    "confirmed_in_vitro_hit",
    "replicated_independent_hit",
    "in_vivo_validated",
)


@dataclass
class ClaimStrengthDowngrade:
    csd_id: str
    pipeline_version: str
    artifact_id: str
    claim_class: str
    trigger_type: str
    original_claim_text: str
    downgraded_claim_text: str
    original_proof_ladder_level: str
    downgraded_proof_ladder_level: str
    downgrade_level: str
    proof_ladder_steps_dropped: int
    trigger_evidence_ref: str
    is_retracted: bool
    dry_lab_only: bool = True
    limitations: list[str] | None = None
    created_at: str = ""


def build_claim_strength_downgrade(
    *,
    csd_id: str,
    pipeline_version: str,
    artifact_id: str,
    claim_class: str,
    trigger_type: str,
    original_claim_text: str,
    downgraded_claim_text: str,
    original_proof_ladder_level: str,
    downgraded_proof_ladder_level: str,
    downgrade_level: str,
    trigger_evidence_ref: str,
    limitations: list[str],
    created_at: str,
) -> ClaimStrengthDowngrade:
    is_retracted = downgrade_level == "retracted"
    if is_retracted:
        proof_ladder_steps_dropped = 0
    else:
        orig_idx = PROOF_LADDER_LEVELS.index(original_proof_ladder_level)
        down_idx = PROOF_LADDER_LEVELS.index(downgraded_proof_ladder_level)
        proof_ladder_steps_dropped = orig_idx - down_idx

    csd = ClaimStrengthDowngrade(
        csd_id=csd_id,
        pipeline_version=pipeline_version,
        artifact_id=artifact_id,
        claim_class=claim_class,
        trigger_type=trigger_type,
        original_claim_text=original_claim_text,
        downgraded_claim_text=downgraded_claim_text,
        original_proof_ladder_level=original_proof_ladder_level,
        downgraded_proof_ladder_level=downgraded_proof_ladder_level,
        downgrade_level=downgrade_level,
        proof_ladder_steps_dropped=proof_ladder_steps_dropped,
        trigger_evidence_ref=trigger_evidence_ref,
        is_retracted=is_retracted,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_claim_strength_downgrade(csd)
    return csd


def validate_claim_strength_downgrade(
    csd: ClaimStrengthDowngrade,
) -> None:
    if not csd.csd_id.startswith("CSD-"):
        raise ValueError(
            f"csd_id must start with 'CSD-': {csd.csd_id!r}"
        )
    if not csd.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if not csd.artifact_id:
        raise ValueError("artifact_id must be non-empty")
    if not csd.original_claim_text:
        raise ValueError("original_claim_text must be non-empty")
    if not csd.downgraded_claim_text:
        raise ValueError("downgraded_claim_text must be non-empty")
    if csd.claim_class not in VALID_CSD_CLAIM_CLASSES:
        raise ValueError(
            f"claim_class {csd.claim_class!r} not in VALID_CSD_CLAIM_CLASSES"
        )
    if csd.trigger_type not in VALID_CSD_TRIGGER_TYPES:
        raise ValueError(
            f"trigger_type {csd.trigger_type!r} not in VALID_CSD_TRIGGER_TYPES"
        )
    if csd.downgrade_level not in VALID_CSD_DOWNGRADE_LEVELS:
        raise ValueError(
            f"downgrade_level {csd.downgrade_level!r} not in VALID_CSD_DOWNGRADE_LEVELS"
        )
    if csd.original_proof_ladder_level not in PROOF_LADDER_LEVELS:
        raise ValueError(
            f"original_proof_ladder_level {csd.original_proof_ladder_level!r} "
            f"not in PROOF_LADDER_LEVELS"
        )
    if csd.downgraded_proof_ladder_level not in PROOF_LADDER_LEVELS:
        raise ValueError(
            f"downgraded_proof_ladder_level {csd.downgraded_proof_ladder_level!r} "
            f"not in PROOF_LADDER_LEVELS"
        )

    if csd.downgrade_level != "retracted":
        orig_idx = PROOF_LADDER_LEVELS.index(csd.original_proof_ladder_level)
        down_idx = PROOF_LADDER_LEVELS.index(csd.downgraded_proof_ladder_level)
        if down_idx > orig_idx:
            raise ValueError(
                f"downgraded_proof_ladder_level {csd.downgraded_proof_ladder_level!r} "
                f"(index {down_idx}) > original_proof_ladder_level "
                f"{csd.original_proof_ladder_level!r} (index {orig_idx}) — "
                f"upgrade not allowed"
            )
    else:
        if csd.downgraded_claim_text != "RETRACTED":
            raise ValueError(
                f"downgraded_claim_text must be 'RETRACTED' for retracted: "
                f"{csd.downgraded_claim_text!r}"
            )

    if csd.downgrade_level != "retracted":
        expected_steps = (
            PROOF_LADDER_LEVELS.index(csd.original_proof_ladder_level)
            - PROOF_LADDER_LEVELS.index(csd.downgraded_proof_ladder_level)
        )
    else:
        expected_steps = 0
    if csd.proof_ladder_steps_dropped != expected_steps:
        raise ValueError(
            f"proof_ladder_steps_dropped {csd.proof_ladder_steps_dropped} != "
            f"{expected_steps} (expected)"
        )

    expected_retracted = csd.downgrade_level == "retracted"
    if csd.is_retracted != expected_retracted:
        raise ValueError(
            f"is_retracted {csd.is_retracted} != {expected_retracted} "
            f"expected for downgrade_level={csd.downgrade_level!r}"
        )

    if csd.dry_lab_only is not True:
        raise ValueError("dry_lab_only must be True")
    if not csd.trigger_evidence_ref:
        raise ValueError("trigger_evidence_ref must be non-empty")
    if not csd.limitations:
        raise ValueError("limitations must be non-empty")
    if not csd.created_at:
        raise ValueError("created_at must be non-empty")


def format_claim_strength_downgrade(
    csd: ClaimStrengthDowngrade,
) -> str:
    lines = [
        f"Claim Strength Downgrade — {csd.csd_id}",
        f"Pipeline: {csd.pipeline_version}",
        f"Artifact: {csd.artifact_id}",
        f"Claim class: {csd.claim_class}",
        f"Trigger: {csd.trigger_type}",
        f"Downgrade level: {csd.downgrade_level}",
        f"Original proof ladder level: {csd.original_proof_ladder_level}",
        f"Downgraded proof ladder level: {csd.downgraded_proof_ladder_level}",
        f"Proof ladder steps dropped: {csd.proof_ladder_steps_dropped}",
        f"Original claim: {csd.original_claim_text}",
        f"Downgraded claim: {csd.downgraded_claim_text}",
        f"Trigger evidence ref: {csd.trigger_evidence_ref}",
        f"Retracted: {csd.is_retracted}",
        f"Dry lab only: {csd.dry_lab_only}",
    ]
    if csd.limitations:
        lines.append(f"Limitations: {'; '.join(csd.limitations)}")
    lines.append(f"Created: {csd.created_at}")
    return "\n".join(lines)
