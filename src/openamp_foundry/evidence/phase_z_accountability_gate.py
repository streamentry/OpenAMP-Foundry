"""ZAG- Phase Z accountability gate schema.

Top-level gate asserting all four Phase Z components are
present: FBH + BXR + ARG + CBF.

No external pilot claim or adapter governance claim is credible
without passing this gate.
Verdict: accountability_verified / accountability_partial / accountability_not_established.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_Z_COMPONENTS: tuple[str, ...] = ("FBH", "BXR", "ARG", "CBF")

VALID_ZAG_VERDICTS: frozenset[str] = frozenset({
    "accountability_verified",
    "accountability_partial",
    "accountability_not_established",
})

ACCOUNTABILITY_VERIFIED_REQUIRED_PRESENT: int = 4
ACCOUNTABILITY_PARTIAL_MIN_PRESENT: int = 2


@dataclass
class ZComponentCheck:
    component_type: str
    artifact_id: str
    is_present: bool


@dataclass
class PhaseZAccountabilityGate:
    zag_id: str
    pipeline_version: str
    fbh_id: str
    bxr_id: str
    arg_id: str
    cbf_id: str
    component_checks: list[ZComponentCheck]
    n_components_present: int
    verdict: str
    dry_lab_only: bool
    created_at: str


def _compute_verdict(n_present: int) -> str:
    if n_present >= ACCOUNTABILITY_VERIFIED_REQUIRED_PRESENT:
        return "accountability_verified"
    if n_present >= ACCOUNTABILITY_PARTIAL_MIN_PRESENT:
        return "accountability_partial"
    return "accountability_not_established"


def build_phase_z_accountability_gate(
    *,
    zag_id: str,
    pipeline_version: str,
    fbh_id: str = "",
    bxr_id: str = "",
    arg_id: str = "",
    cbf_id: str = "",
    created_at: str,
) -> PhaseZAccountabilityGate:
    checks = [
        ZComponentCheck(
            component_type="FBH",
            artifact_id=fbh_id,
            is_present=bool(fbh_id) and fbh_id.startswith("FBH-"),
        ),
        ZComponentCheck(
            component_type="BXR",
            artifact_id=bxr_id,
            is_present=bool(bxr_id) and bxr_id.startswith("BXR-"),
        ),
        ZComponentCheck(
            component_type="ARG",
            artifact_id=arg_id,
            is_present=bool(arg_id) and arg_id.startswith("ARG-"),
        ),
        ZComponentCheck(
            component_type="CBF",
            artifact_id=cbf_id,
            is_present=bool(cbf_id) and cbf_id.startswith("CBF-"),
        ),
    ]
    n_present = sum(1 for c in checks if c.is_present)
    verdict = _compute_verdict(n_present)
    zag = PhaseZAccountabilityGate(
        zag_id=zag_id,
        pipeline_version=pipeline_version,
        fbh_id=fbh_id,
        bxr_id=bxr_id,
        arg_id=arg_id,
        cbf_id=cbf_id,
        component_checks=checks,
        n_components_present=n_present,
        verdict=verdict,
        dry_lab_only=True,
        created_at=created_at,
    )
    validate_phase_z_accountability_gate(zag)
    return zag


def validate_phase_z_accountability_gate(zag: PhaseZAccountabilityGate) -> None:
    if not zag.zag_id.startswith("ZAG-"):
        raise ValueError(f"zag_id must start with 'ZAG-': {zag.zag_id!r}")
    if not zag.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if len(zag.component_checks) != len(REQUIRED_Z_COMPONENTS):
        raise ValueError(
            f"component_checks must have exactly {len(REQUIRED_Z_COMPONENTS)} entries"
        )
    for check in zag.component_checks:
        if check.component_type not in REQUIRED_Z_COMPONENTS:
            raise ValueError(
                f"component_type {check.component_type!r} not in REQUIRED_Z_COMPONENTS"
            )
        expected_prefix = f"{check.component_type}-"
        if check.artifact_id and not check.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id {check.artifact_id!r} must start with {expected_prefix!r}"
            )
    for component_type, id_field, expected_prefix in [
        ("FBH", zag.fbh_id, "FBH-"),
        ("BXR", zag.bxr_id, "BXR-"),
        ("ARG", zag.arg_id, "ARG-"),
        ("CBF", zag.cbf_id, "CBF-"),
    ]:
        if id_field and not id_field.startswith(expected_prefix):
            raise ValueError(
                f"{component_type.lower()}_id {id_field!r} must start with {expected_prefix!r}"
            )
    n_present = sum(1 for c in zag.component_checks if c.is_present)
    if zag.n_components_present != n_present:
        raise ValueError("n_components_present mismatch")
    if zag.verdict not in VALID_ZAG_VERDICTS:
        raise ValueError(f"verdict {zag.verdict!r} not in VALID_ZAG_VERDICTS")
    expected_verdict = _compute_verdict(zag.n_components_present)
    if zag.verdict != expected_verdict:
        raise ValueError(
            f"verdict {zag.verdict!r} inconsistent with n_components_present={zag.n_components_present}"
        )
    if not zag.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not zag.created_at:
        raise ValueError("created_at must be non-empty")


def format_phase_z_accountability_gate(zag: PhaseZAccountabilityGate) -> str:
    lines = [
        f"Phase Z Accountability Gate — {zag.zag_id}",
        f"Pipeline: {zag.pipeline_version}",
        f"Verdict: {zag.verdict}",
        f"Components present: {zag.n_components_present}/{len(REQUIRED_Z_COMPONENTS)}",
    ]
    lines.append("Component checks:")
    for check in zag.component_checks:
        status = "PRESENT" if check.is_present else "ABSENT"
        artifact = f"  [{check.artifact_id}]" if check.artifact_id else ""
        lines.append(f"  {check.component_type}: {status}{artifact}")
    lines.append(f"Created: {zag.created_at}")
    lines.append(f"dry_lab_only: {zag.dry_lab_only}")
    return "\n".join(lines)
