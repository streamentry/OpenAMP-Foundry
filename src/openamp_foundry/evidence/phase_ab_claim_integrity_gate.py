"""ABAG- Phase AB Claim Integrity Gate schema.

Top-level gate asserting that all Phase AB claim integrity components
are present: CSD (claim strength downgrade), RDR (reviewer decision),
EGN (evidence gap notification), EHP (external handoff packet).
"""

from __future__ import annotations
from dataclasses import dataclass

REQUIRED_AB_COMPONENTS: tuple[str, ...] = ("CSD", "RDR", "EGN", "EHP")

VALID_ABAG_VERDICTS: frozenset[str] = frozenset({
    "claim_integrity_verified",
    "claim_integrity_partial",
    "claim_integrity_not_established",
})


@dataclass
class PhaseAbClaimIntegrityGate:
    abag_id: str
    pipeline_version: str
    components_present: list[str]
    n_components_present: int
    n_components_required: int
    missing_components: list[str]
    verdict: str
    limitations: list[str]
    dry_lab_only: bool = True
    created_at: str = ""


def _compute_abag_verdict(n_present: int) -> str:
    if n_present == 4:
        return "claim_integrity_verified"
    if n_present >= 2:
        return "claim_integrity_partial"
    return "claim_integrity_not_established"


def build_phase_ab_claim_integrity_gate(
    *,
    abag_id: str,
    pipeline_version: str,
    components_present: list[str],
    limitations: list[str],
    created_at: str,
) -> PhaseAbClaimIntegrityGate:
    seen: set[str] = set()
    for comp in components_present:
        if comp not in REQUIRED_AB_COMPONENTS:
            raise ValueError(f"component {comp!r} not in REQUIRED_AB_COMPONENTS")
        if comp in seen:
            raise ValueError(f"duplicate component {comp!r}")
        seen.add(comp)
    n_components_required = len(REQUIRED_AB_COMPONENTS)
    unique_present = sorted(seen)
    n_components_present = len(unique_present)
    missing_components = sorted(set(REQUIRED_AB_COMPONENTS) - set(unique_present))
    verdict = _compute_abag_verdict(n_components_present)
    gate = PhaseAbClaimIntegrityGate(
        abag_id=abag_id,
        pipeline_version=pipeline_version,
        components_present=components_present,
        n_components_present=n_components_present,
        n_components_required=n_components_required,
        missing_components=missing_components,
        verdict=verdict,
        limitations=limitations,
        dry_lab_only=True,
        created_at=created_at,
    )
    validate_phase_ab_claim_integrity_gate(gate)
    return gate


def validate_phase_ab_claim_integrity_gate(gate: PhaseAbClaimIntegrityGate) -> None:
    if not gate.abag_id.startswith("ABAG-"):
        raise ValueError(f"abag_id must start with 'ABAG-': {gate.abag_id!r}")
    if not gate.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    for comp in gate.components_present:
        if comp not in REQUIRED_AB_COMPONENTS:
            raise ValueError(
                f"component {comp!r} not in REQUIRED_AB_COMPONENTS"
            )
    seen = set()
    for comp in gate.components_present:
        if comp in seen:
            raise ValueError(f"duplicate component {comp!r}")
        seen.add(comp)
    if not gate.limitations:
        raise ValueError("limitations must be non-empty")
    if not gate.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not gate.created_at:
        raise ValueError("created_at must be non-empty")
    if gate.verdict not in VALID_ABAG_VERDICTS:
        raise ValueError(f"verdict {gate.verdict!r} not in VALID_ABAG_VERDICTS")
    expected_verdict = _compute_abag_verdict(gate.n_components_present)
    if gate.verdict != expected_verdict:
        raise ValueError(
            f"verdict {gate.verdict!r} inconsistent with n_components_present={gate.n_components_present}"
        )


def format_phase_ab_claim_integrity_gate(gate: PhaseAbClaimIntegrityGate) -> str:
    lines = [
        f"Phase AB Claim Integrity Gate — {gate.abag_id}",
        f"Pipeline: {gate.pipeline_version}",
        f"Components present: {gate.n_components_present}/{gate.n_components_required}",
        f"Missing components: {', '.join(gate.missing_components) if gate.missing_components else 'none'}",
        f"Verdict: {gate.verdict}",
        f"dry_lab_only: {gate.dry_lab_only}",
    ]
    if gate.limitations:
        lines.append("Limitations:")
        for lim in gate.limitations:
            lines.append(f"  - {lim}")
    if gate.created_at:
        lines.append(f"Created: {gate.created_at}")
    return "\n".join(lines)
