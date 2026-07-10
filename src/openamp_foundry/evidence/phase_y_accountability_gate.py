"""YAG- Phase Y accountability gate schema.

Top-level gate asserting all four Phase Y accountability components are
present: CBR + FIA + SDA + PMC.

No external pilot claim is credible without passing this gate.
Verdict: accountability_verified / accountability_partial / accountability_not_established.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_Y_COMPONENTS: tuple[str, ...] = ("CBR", "FIA", "SDA", "PMC")

VALID_YAG_VERDICTS: frozenset[str] = frozenset({
    "accountability_verified",
    "accountability_partial",
    "accountability_not_established",
})

ACCOUNTABILITY_VERIFIED_REQUIRED_PRESENT: int = 4
ACCOUNTABILITY_PARTIAL_MIN_PRESENT: int = 2


@dataclass
class YComponentCheck:
    component_type: str
    artifact_id: str
    present: bool


@dataclass
class PhaseYAccountabilityGate:
    yag_id: str
    pipeline_version: str
    component_checks: list[YComponentCheck]
    n_components_present: int
    yag_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_phase_y_accountability_gate(yag: PhaseYAccountabilityGate) -> None:
    if not yag.yag_id.startswith("YAG-"):
        raise ValueError(f"yag_id must start with 'YAG-': {yag.yag_id!r}")
    if not yag.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if len(yag.component_checks) != len(REQUIRED_Y_COMPONENTS):
        raise ValueError(
            f"component_checks must have exactly {len(REQUIRED_Y_COMPONENTS)} entries"
        )
    for check in yag.component_checks:
        if check.component_type not in REQUIRED_Y_COMPONENTS:
            raise ValueError(
                f"component_type {check.component_type!r} not in REQUIRED_Y_COMPONENTS"
            )
        expected_prefix = f"{check.component_type}-"
        if check.artifact_id and not check.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id {check.artifact_id!r} must start with {expected_prefix!r}"
            )
    n_present = sum(1 for c in yag.component_checks if c.present)
    if yag.n_components_present != n_present:
        raise ValueError("n_components_present mismatch")
    if yag.yag_verdict not in VALID_YAG_VERDICTS:
        raise ValueError(
            f"yag_verdict {yag.yag_verdict!r} not in VALID_YAG_VERDICTS"
        )
    if not yag.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not yag.limitations:
        raise ValueError("limitations must be non-empty")
    if not yag.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(n_present: int) -> str:
    if n_present >= ACCOUNTABILITY_VERIFIED_REQUIRED_PRESENT:
        return "accountability_verified"
    if n_present >= ACCOUNTABILITY_PARTIAL_MIN_PRESENT:
        return "accountability_partial"
    return "accountability_not_established"


def build_phase_y_accountability_gate(
    *,
    yag_id: str,
    pipeline_version: str,
    cbr_artifact_id: str = "",
    fia_artifact_id: str = "",
    sda_artifact_id: str = "",
    pmc_artifact_id: str = "",
    limitations: list[str],
    created_at: str,
) -> PhaseYAccountabilityGate:
    """Build a PhaseYAccountabilityGate.

    Pass non-empty artifact_id for each component that is present.
    Empty artifact_id means the component is absent (present=False).
    """
    checks = [
        YComponentCheck(
            component_type="CBR",
            artifact_id=cbr_artifact_id,
            present=bool(cbr_artifact_id),
        ),
        YComponentCheck(
            component_type="FIA",
            artifact_id=fia_artifact_id,
            present=bool(fia_artifact_id),
        ),
        YComponentCheck(
            component_type="SDA",
            artifact_id=sda_artifact_id,
            present=bool(sda_artifact_id),
        ),
        YComponentCheck(
            component_type="PMC",
            artifact_id=pmc_artifact_id,
            present=bool(pmc_artifact_id),
        ),
    ]
    n_present = sum(1 for c in checks if c.present)
    verdict = _compute_verdict(n_present)
    yag = PhaseYAccountabilityGate(
        yag_id=yag_id,
        pipeline_version=pipeline_version,
        component_checks=checks,
        n_components_present=n_present,
        yag_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_phase_y_accountability_gate(yag)
    return yag


def format_phase_y_accountability_gate(yag: PhaseYAccountabilityGate) -> str:
    lines = [
        f"Phase Y Accountability Gate — {yag.yag_id}",
        f"Pipeline: {yag.pipeline_version}",
        f"Verdict: {yag.yag_verdict}",
        f"Components present: {yag.n_components_present}/{len(REQUIRED_Y_COMPONENTS)}",
    ]
    lines.append("Component checks:")
    for check in yag.component_checks:
        status = "PRESENT" if check.present else "ABSENT"
        artifact = f"  [{check.artifact_id}]" if check.artifact_id else ""
        lines.append(f"  {check.component_type}: {status}{artifact}")
    lines.append(f"Created: {yag.created_at}")
    lines.append(f"Limitations: {'; '.join(yag.limitations)}")
    lines.append(f"dry_lab_only: {yag.dry_lab_only}")
    return "\n".join(lines)
