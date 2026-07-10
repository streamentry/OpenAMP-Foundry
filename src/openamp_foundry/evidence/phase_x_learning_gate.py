"""XLG- Phase X learning gate schema.

Top-level gate asserting all four Phase X components are present and
the learning loop is closed: MBL + CIT + LPR + RCC.

No calibration improvement claim is credible without passing this gate.
Verdict: learning_verified / learning_in_progress / learning_not_started.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_X_COMPONENTS: tuple[str, ...] = ("MBL", "CIT", "LPR", "RCC")

VALID_XLG_VERDICTS: frozenset[str] = frozenset({
    "learning_verified",
    "learning_in_progress",
    "learning_not_started",
})

LEARNING_VERIFIED_REQUIRED_PRESENT: int = 4
LEARNING_IN_PROGRESS_MIN_PRESENT: int = 2


@dataclass
class XComponentCheck:
    component_type: str
    artifact_id: str
    present: bool


@dataclass
class PhaseXLearningGate:
    xlg_id: str
    pipeline_version: str
    component_checks: list[XComponentCheck]
    n_components_present: int
    xlg_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_phase_x_learning_gate(xlg: PhaseXLearningGate) -> None:
    if not xlg.xlg_id.startswith("XLG-"):
        raise ValueError(f"xlg_id must start with 'XLG-': {xlg.xlg_id!r}")
    if not xlg.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if len(xlg.component_checks) != len(REQUIRED_X_COMPONENTS):
        raise ValueError(
            f"component_checks must have exactly {len(REQUIRED_X_COMPONENTS)} entries"
        )
    for check in xlg.component_checks:
        if check.component_type not in REQUIRED_X_COMPONENTS:
            raise ValueError(
                f"component_type {check.component_type!r} not in REQUIRED_X_COMPONENTS"
            )
        expected_prefix = f"{check.component_type}-"
        if check.artifact_id and not check.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id {check.artifact_id!r} must start with {expected_prefix!r}"
            )
    n_present = sum(1 for c in xlg.component_checks if c.present)
    if xlg.n_components_present != n_present:
        raise ValueError("n_components_present mismatch")
    if xlg.xlg_verdict not in VALID_XLG_VERDICTS:
        raise ValueError(
            f"xlg_verdict {xlg.xlg_verdict!r} not in VALID_XLG_VERDICTS"
        )
    if not xlg.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not xlg.limitations:
        raise ValueError("limitations must be non-empty")
    if not xlg.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(n_present: int) -> str:
    if n_present >= LEARNING_VERIFIED_REQUIRED_PRESENT:
        return "learning_verified"
    if n_present >= LEARNING_IN_PROGRESS_MIN_PRESENT:
        return "learning_in_progress"
    return "learning_not_started"


def build_phase_x_learning_gate(
    *,
    xlg_id: str,
    pipeline_version: str,
    mbl_artifact_id: str = "",
    cit_artifact_id: str = "",
    lpr_artifact_id: str = "",
    rcc_artifact_id: str = "",
    limitations: list[str],
    created_at: str,
) -> PhaseXLearningGate:
    """Build a PhaseXLearningGate.

    Pass non-empty artifact_id for each component that is present.
    An empty artifact_id means the component is absent (present=False).
    """
    checks = [
        XComponentCheck(
            component_type="MBL",
            artifact_id=mbl_artifact_id,
            present=bool(mbl_artifact_id),
        ),
        XComponentCheck(
            component_type="CIT",
            artifact_id=cit_artifact_id,
            present=bool(cit_artifact_id),
        ),
        XComponentCheck(
            component_type="LPR",
            artifact_id=lpr_artifact_id,
            present=bool(lpr_artifact_id),
        ),
        XComponentCheck(
            component_type="RCC",
            artifact_id=rcc_artifact_id,
            present=bool(rcc_artifact_id),
        ),
    ]
    n_present = sum(1 for c in checks if c.present)
    verdict = _compute_verdict(n_present)
    xlg = PhaseXLearningGate(
        xlg_id=xlg_id,
        pipeline_version=pipeline_version,
        component_checks=checks,
        n_components_present=n_present,
        xlg_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_phase_x_learning_gate(xlg)
    return xlg


def format_phase_x_learning_gate(xlg: PhaseXLearningGate) -> str:
    lines = [
        f"Phase X Learning Gate — {xlg.xlg_id}",
        f"Pipeline: {xlg.pipeline_version}",
        f"Verdict: {xlg.xlg_verdict}",
        f"Components present: {xlg.n_components_present}/{len(REQUIRED_X_COMPONENTS)}",
    ]
    lines.append("Component checks:")
    for check in xlg.component_checks:
        status = "PRESENT" if check.present else "ABSENT"
        artifact = f"  [{check.artifact_id}]" if check.artifact_id else ""
        lines.append(f"  {check.component_type}: {status}{artifact}")
    lines.append(f"Created: {xlg.created_at}")
    lines.append(f"Limitations: {'; '.join(xlg.limitations)}")
    lines.append(f"dry_lab_only: {xlg.dry_lab_only}")
    return "\n".join(lines)
