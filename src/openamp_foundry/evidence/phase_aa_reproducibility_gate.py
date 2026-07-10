"""AARG- Phase AA reproducibility gate schema.

Top-level gate for Phase AA — Run reproducibility manifests.
Asserts all four AA components are present: RMC + DCR + CFP + SBW.

No pipeline run is reproducibility-certified without passing this gate.
Verdict: reproducibility_verified / reproducibility_partial / reproducibility_not_established.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_AA_COMPONENTS: tuple[str, ...] = ("RMC", "DCR", "CFP", "SBW")

VALID_AARG_VERDICTS: frozenset[str] = frozenset({
    "reproducibility_verified",
    "reproducibility_partial",
    "reproducibility_not_established",
})

REPRODUCIBILITY_VERIFIED_REQUIRED_PRESENT: int = 4
REPRODUCIBILITY_PARTIAL_MIN_PRESENT: int = 2


@dataclass
class AAComponentCheck:
    component_type: str
    artifact_id: str
    is_present: bool


@dataclass
class PhaseAaReproducibilityGate:
    aarg_id: str
    pipeline_version: str
    rmc_id: str
    dcr_id: str
    cfp_id: str
    sbw_id: str
    component_checks: list[AAComponentCheck]
    n_components_present: int
    verdict: str
    dry_lab_only: bool
    created_at: str


def _compute_verdict(n_present: int) -> str:
    if n_present >= REPRODUCIBILITY_VERIFIED_REQUIRED_PRESENT:
        return "reproducibility_verified"
    if n_present >= REPRODUCIBILITY_PARTIAL_MIN_PRESENT:
        return "reproducibility_partial"
    return "reproducibility_not_established"


def build_phase_aa_reproducibility_gate(
    *,
    aarg_id: str,
    pipeline_version: str,
    rmc_id: str = "",
    dcr_id: str = "",
    cfp_id: str = "",
    sbw_id: str = "",
    created_at: str,
) -> PhaseAaReproducibilityGate:
    checks = [
        AAComponentCheck(
            component_type="RMC",
            artifact_id=rmc_id,
            is_present=bool(rmc_id) and rmc_id.startswith("RMC-"),
        ),
        AAComponentCheck(
            component_type="DCR",
            artifact_id=dcr_id,
            is_present=bool(dcr_id) and dcr_id.startswith("DCR-"),
        ),
        AAComponentCheck(
            component_type="CFP",
            artifact_id=cfp_id,
            is_present=bool(cfp_id) and cfp_id.startswith("CFP-"),
        ),
        AAComponentCheck(
            component_type="SBW",
            artifact_id=sbw_id,
            is_present=bool(sbw_id) and sbw_id.startswith("SBW-"),
        ),
    ]
    n_present = sum(1 for c in checks if c.is_present)
    verdict = _compute_verdict(n_present)
    aarg = PhaseAaReproducibilityGate(
        aarg_id=aarg_id,
        pipeline_version=pipeline_version,
        rmc_id=rmc_id,
        dcr_id=dcr_id,
        cfp_id=cfp_id,
        sbw_id=sbw_id,
        component_checks=checks,
        n_components_present=n_present,
        verdict=verdict,
        dry_lab_only=True,
        created_at=created_at,
    )
    validate_phase_aa_reproducibility_gate(aarg)
    return aarg


def validate_phase_aa_reproducibility_gate(aarg: PhaseAaReproducibilityGate) -> None:
    if not aarg.aarg_id.startswith("AARG-"):
        raise ValueError(f"aarg_id must start with 'AARG-': {aarg.aarg_id!r}")
    if not aarg.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if len(aarg.component_checks) != len(REQUIRED_AA_COMPONENTS):
        raise ValueError(
            f"component_checks must have exactly {len(REQUIRED_AA_COMPONENTS)} entries"
        )
    for check in aarg.component_checks:
        if check.component_type not in REQUIRED_AA_COMPONENTS:
            raise ValueError(
                f"component_type {check.component_type!r} not in REQUIRED_AA_COMPONENTS"
            )
        expected_prefix = f"{check.component_type}-"
        if check.artifact_id and not check.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id {check.artifact_id!r} must start with {expected_prefix!r}"
            )
    for component_type, id_field, expected_prefix in [
        ("RMC", aarg.rmc_id, "RMC-"),
        ("DCR", aarg.dcr_id, "DCR-"),
        ("CFP", aarg.cfp_id, "CFP-"),
        ("SBW", aarg.sbw_id, "SBW-"),
    ]:
        if id_field and not id_field.startswith(expected_prefix):
            raise ValueError(
                f"{component_type.lower()}_id {id_field!r} must start with {expected_prefix!r}"
            )
    n_present = sum(1 for c in aarg.component_checks if c.is_present)
    if aarg.n_components_present != n_present:
        raise ValueError("n_components_present mismatch")
    if aarg.verdict not in VALID_AARG_VERDICTS:
        raise ValueError(f"verdict {aarg.verdict!r} not in VALID_AARG_VERDICTS")
    expected_verdict = _compute_verdict(aarg.n_components_present)
    if aarg.verdict != expected_verdict:
        raise ValueError(
            f"verdict {aarg.verdict!r} inconsistent with n_components_present={aarg.n_components_present}"
        )
    if not aarg.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not aarg.created_at:
        raise ValueError("created_at must be non-empty")


def format_phase_aa_reproducibility_gate(aarg: PhaseAaReproducibilityGate) -> str:
    lines = [
        f"Phase AA Reproducibility Gate — {aarg.aarg_id}",
        f"Pipeline: {aarg.pipeline_version}",
        f"Verdict: {aarg.verdict}",
        f"Components present: {aarg.n_components_present}/{len(REQUIRED_AA_COMPONENTS)}",
    ]
    lines.append("Component checks:")
    for check in aarg.component_checks:
        status = "PRESENT" if check.is_present else "ABSENT"
        artifact = f"  [{check.artifact_id}]" if check.artifact_id else ""
        lines.append(f"  {check.component_type}: {status}{artifact}")
    lines.append(f"Created: {aarg.created_at}")
    lines.append(f"dry_lab_only: {aarg.dry_lab_only}")
    return "\n".join(lines)
