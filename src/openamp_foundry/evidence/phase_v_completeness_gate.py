"""V5G- Phase V completeness gate schema.

Top-level gate asserting that all four Phase V artifacts (PRG, EBM, SRS, ERP)
are present for a batch. A 'ready' verdict signals the batch is cleared for
external scientific review.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_V5_COMPONENTS: tuple[str, ...] = ("PRG", "EBM", "SRS", "ERP")

VALID_V5G_VERDICTS: frozenset[str] = frozenset({"ready", "blocked"})

_COMPONENT_ID_PREFIXES: dict[str, str] = {
    "PRG": "PRG-",
    "EBM": "EBM-",
    "SRS": "SRS-",
    "ERP": "ERP-",
}


@dataclass
class V5ComponentCheck:
    component_type: str
    artifact_id: str
    present: bool


@dataclass
class PhaseVCompletenessGate:
    v5g_id: str
    batch_id: str
    pipeline_version: str
    component_checks: list[V5ComponentCheck]
    n_components_required: int
    n_components_present: int
    missing_component_types: list[str]
    gate_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_phase_v_completeness_gate(gate: PhaseVCompletenessGate) -> None:
    if not gate.v5g_id.startswith("V5G-"):
        raise ValueError(f"v5g_id must start with 'V5G-': {gate.v5g_id!r}")
    if not gate.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not gate.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    seen_types = set()
    for check in gate.component_checks:
        if check.component_type not in REQUIRED_V5_COMPONENTS:
            raise ValueError(
                f"component_type {check.component_type!r} not in REQUIRED_V5_COMPONENTS"
            )
        if check.component_type in seen_types:
            raise ValueError(
                f"duplicate component_type: {check.component_type!r}"
            )
        seen_types.add(check.component_type)
        expected_prefix = _COMPONENT_ID_PREFIXES[check.component_type]
        if check.present and not check.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id for {check.component_type} must start with "
                f"'{expected_prefix}': {check.artifact_id!r}"
            )
    if gate.n_components_required != len(REQUIRED_V5_COMPONENTS):
        raise ValueError(
            f"n_components_required must be {len(REQUIRED_V5_COMPONENTS)}"
        )
    present_count = sum(1 for c in gate.component_checks if c.present)
    if gate.n_components_present != present_count:
        raise ValueError("n_components_present mismatch")
    expected_missing = sorted(
        c.component_type for c in gate.component_checks if not c.present
    )
    if gate.missing_component_types != expected_missing:
        raise ValueError("missing_component_types mismatch")
    if gate.gate_verdict not in VALID_V5G_VERDICTS:
        raise ValueError(
            f"gate_verdict {gate.gate_verdict!r} not in VALID_V5G_VERDICTS"
        )
    if not gate.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not gate.limitations:
        raise ValueError("limitations must be non-empty")
    if not gate.created_at:
        raise ValueError("created_at must be non-empty")


def build_phase_v_completeness_gate(
    *,
    v5g_id: str,
    batch_id: str,
    pipeline_version: str,
    prg_artifact_id: str = "",
    ebm_artifact_id: str = "",
    srs_artifact_id: str = "",
    erp_artifact_id: str = "",
    limitations: list[str],
    created_at: str,
) -> PhaseVCompletenessGate:
    artifact_map = {
        "PRG": prg_artifact_id,
        "EBM": ebm_artifact_id,
        "SRS": srs_artifact_id,
        "ERP": erp_artifact_id,
    }
    checks = [
        V5ComponentCheck(
            component_type=ctype,
            artifact_id=artifact_map[ctype],
            present=bool(artifact_map[ctype]),
        )
        for ctype in REQUIRED_V5_COMPONENTS
    ]
    n_present = sum(1 for c in checks if c.present)
    missing = sorted(c.component_type for c in checks if not c.present)
    verdict = "ready" if n_present == len(REQUIRED_V5_COMPONENTS) else "blocked"
    gate = PhaseVCompletenessGate(
        v5g_id=v5g_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        component_checks=checks,
        n_components_required=len(REQUIRED_V5_COMPONENTS),
        n_components_present=n_present,
        missing_component_types=missing,
        gate_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_phase_v_completeness_gate(gate)
    return gate


def format_phase_v_completeness_gate(gate: PhaseVCompletenessGate) -> str:
    lines = [
        f"Phase V Completeness Gate — {gate.v5g_id}",
        f"Batch: {gate.batch_id}  |  Pipeline: {gate.pipeline_version}",
        f"Verdict: {gate.gate_verdict}  |  Present: {gate.n_components_present}/{gate.n_components_required}",
    ]
    lines.append("Components:")
    for check in gate.component_checks:
        status = "PRESENT" if check.present else "MISSING"
        aid = check.artifact_id if check.artifact_id else "(none)"
        lines.append(f"  {check.component_type}: {status}  {aid}")
    if gate.missing_component_types:
        lines.append(f"Missing: {', '.join(gate.missing_component_types)}")
    lines.append(f"Created: {gate.created_at}")
    lines.append(f"Limitations: {'; '.join(gate.limitations)}")
    lines.append(f"dry_lab_only: {gate.dry_lab_only}")
    return "\n".join(lines)
