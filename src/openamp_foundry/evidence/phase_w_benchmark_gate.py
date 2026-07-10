"""WBG- Phase W benchmark gate schema.

Top-level gate asserting all four Phase W benchmark challenge artifacts
(NCH, CMC, SCH, BCR) are present for a batch. Produces an overall
verdict: hardened/partially_hardened/not_hardened. No batch-level
performance claim is credible without a passing WBG-.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_W_COMPONENTS: tuple[str, ...] = ("NCH", "CMC", "SCH", "BCR")

VALID_WBG_VERDICTS: frozenset[str] = frozenset({
    "hardened",
    "partially_hardened",
    "not_hardened",
})

_COMPONENT_ID_PREFIXES: dict[str, str] = {
    "NCH": "NCH-",
    "CMC": "CMC-",
    "SCH": "SCH-",
    "BCR": "BCR-",
}

HARDENED_REQUIRED_PRESENT: int = 4
PARTIALLY_HARDENED_MIN_PRESENT: int = 2


@dataclass
class WComponentCheck:
    component_type: str
    artifact_id: str
    present: bool


@dataclass
class PhaseWBenchmarkGate:
    wbg_id: str
    batch_id: str
    pipeline_version: str
    component_checks: list[WComponentCheck]
    n_components_required: int
    n_components_present: int
    missing_component_types: list[str]
    gate_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_phase_w_benchmark_gate(gate: PhaseWBenchmarkGate) -> None:
    if not gate.wbg_id.startswith("WBG-"):
        raise ValueError(f"wbg_id must start with 'WBG-': {gate.wbg_id!r}")
    if not gate.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not gate.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    seen: set[str] = set()
    for check in gate.component_checks:
        if check.component_type not in REQUIRED_W_COMPONENTS:
            raise ValueError(
                f"component_type {check.component_type!r} not in REQUIRED_W_COMPONENTS"
            )
        if check.component_type in seen:
            raise ValueError(f"duplicate component_type: {check.component_type!r}")
        seen.add(check.component_type)
        expected_prefix = _COMPONENT_ID_PREFIXES[check.component_type]
        if check.present and not check.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id for {check.component_type} must start with "
                f"'{expected_prefix}': {check.artifact_id!r}"
            )
    if gate.n_components_required != len(REQUIRED_W_COMPONENTS):
        raise ValueError(
            f"n_components_required must be {len(REQUIRED_W_COMPONENTS)}"
        )
    present_count = sum(1 for c in gate.component_checks if c.present)
    if gate.n_components_present != present_count:
        raise ValueError("n_components_present mismatch")
    expected_missing = sorted(
        c.component_type for c in gate.component_checks if not c.present
    )
    if gate.missing_component_types != expected_missing:
        raise ValueError("missing_component_types mismatch")
    if gate.gate_verdict not in VALID_WBG_VERDICTS:
        raise ValueError(
            f"gate_verdict {gate.gate_verdict!r} not in VALID_WBG_VERDICTS"
        )
    if not gate.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not gate.limitations:
        raise ValueError("limitations must be non-empty")
    if not gate.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(n_present: int) -> str:
    if n_present == HARDENED_REQUIRED_PRESENT:
        return "hardened"
    if n_present >= PARTIALLY_HARDENED_MIN_PRESENT:
        return "partially_hardened"
    return "not_hardened"


def build_phase_w_benchmark_gate(
    *,
    wbg_id: str,
    batch_id: str,
    pipeline_version: str,
    nch_artifact_id: str = "",
    cmc_artifact_id: str = "",
    sch_artifact_id: str = "",
    bcr_artifact_id: str = "",
    limitations: list[str],
    created_at: str,
) -> PhaseWBenchmarkGate:
    artifact_map = {
        "NCH": nch_artifact_id,
        "CMC": cmc_artifact_id,
        "SCH": sch_artifact_id,
        "BCR": bcr_artifact_id,
    }
    checks = [
        WComponentCheck(
            component_type=ctype,
            artifact_id=artifact_map[ctype],
            present=bool(artifact_map[ctype]),
        )
        for ctype in REQUIRED_W_COMPONENTS
    ]
    n_present = sum(1 for c in checks if c.present)
    missing = sorted(c.component_type for c in checks if not c.present)
    verdict = _compute_verdict(n_present)
    gate = PhaseWBenchmarkGate(
        wbg_id=wbg_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        component_checks=checks,
        n_components_required=len(REQUIRED_W_COMPONENTS),
        n_components_present=n_present,
        missing_component_types=missing,
        gate_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_phase_w_benchmark_gate(gate)
    return gate


def format_phase_w_benchmark_gate(gate: PhaseWBenchmarkGate) -> str:
    lines = [
        f"Phase W Benchmark Gate — {gate.wbg_id}",
        f"Batch: {gate.batch_id}  |  Pipeline: {gate.pipeline_version}",
        f"Verdict: {gate.gate_verdict}  |  Present: {gate.n_components_present}/{gate.n_components_required}",
        "Components:",
    ]
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
