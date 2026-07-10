"""PMC- pipeline maturity certificate schema.

Aggregates CBR (baseline comparison), FIA (feature importance audit), and
SDA (selection diversity audit) results into an A/B/C/D maturity grade.
Anchors pre-registration: the grade is frozen before results are interpreted
so it cannot be retroactively adjusted. No "mature pipeline" claim is
credible without this certificate.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_PMC_GRADES: frozenset[str] = frozenset({
    "A",
    "B",
    "C",
    "D",
})

VALID_PMC_VERDICTS: frozenset[str] = frozenset({
    "pipeline_validated",
    "pipeline_provisional",
    "pipeline_unvalidated",
    "insufficient_evidence",
})

REQUIRED_PMC_COMPONENTS: tuple[str, ...] = ("CBR", "FIA", "SDA")

GRADE_A_REQUIRED_SUPERIOR_VERDICTS: int = 3
GRADE_B_REQUIRED_SUPERIOR_VERDICTS: int = 2
GRADE_C_REQUIRED_SUPERIOR_VERDICTS: int = 1


@dataclass
class PMCComponentCheck:
    component_type: str
    artifact_id: str
    verdict: str
    contributes_to_grade: bool


@dataclass
class PipelineMaturityCertificate:
    pmc_id: str
    pipeline_version: str
    component_checks: list[PMCComponentCheck]
    n_components_assessed: int
    n_superior_verdicts: int
    pmc_grade: str
    pmc_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_pipeline_maturity_certificate(pmc: PipelineMaturityCertificate) -> None:
    if not pmc.pmc_id.startswith("PMC-"):
        raise ValueError(f"pmc_id must start with 'PMC-': {pmc.pmc_id!r}")
    if not pmc.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if len(pmc.component_checks) != len(REQUIRED_PMC_COMPONENTS):
        raise ValueError(
            f"component_checks must have exactly {len(REQUIRED_PMC_COMPONENTS)} entries"
        )
    for check in pmc.component_checks:
        if check.component_type not in REQUIRED_PMC_COMPONENTS:
            raise ValueError(
                f"component_type {check.component_type!r} not in REQUIRED_PMC_COMPONENTS"
            )
        expected_prefix = f"{check.component_type}-"
        if check.artifact_id and not check.artifact_id.startswith(expected_prefix):
            raise ValueError(
                f"artifact_id {check.artifact_id!r} must start with {expected_prefix!r}"
            )
    n_assessed = sum(1 for c in pmc.component_checks if c.artifact_id)
    if pmc.n_components_assessed != n_assessed:
        raise ValueError("n_components_assessed mismatch")
    n_superior = sum(1 for c in pmc.component_checks if c.contributes_to_grade)
    if pmc.n_superior_verdicts != n_superior:
        raise ValueError("n_superior_verdicts mismatch")
    if pmc.pmc_grade not in VALID_PMC_GRADES:
        raise ValueError(f"pmc_grade {pmc.pmc_grade!r} not in VALID_PMC_GRADES")
    if pmc.pmc_verdict not in VALID_PMC_VERDICTS:
        raise ValueError(
            f"pmc_verdict {pmc.pmc_verdict!r} not in VALID_PMC_VERDICTS"
        )
    if not pmc.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not pmc.limitations:
        raise ValueError("limitations must be non-empty")
    if not pmc.created_at:
        raise ValueError("created_at must be non-empty")


_SUPERIOR_VERDICTS: frozenset[str] = frozenset({
    "pipeline_superior",
    "multi_feature_signal",
    "diverse_panel",
})


def _contributes_to_grade(component_type: str, verdict: str) -> bool:
    return verdict in _SUPERIOR_VERDICTS


def _compute_grade_and_verdict(
    n_assessed: int,
    n_superior: int,
) -> tuple[str, str]:
    if n_assessed == 0:
        return "D", "insufficient_evidence"
    if n_superior >= GRADE_A_REQUIRED_SUPERIOR_VERDICTS:
        return "A", "pipeline_validated"
    if n_superior >= GRADE_B_REQUIRED_SUPERIOR_VERDICTS:
        return "B", "pipeline_provisional"
    if n_superior >= GRADE_C_REQUIRED_SUPERIOR_VERDICTS:
        return "C", "pipeline_unvalidated"
    return "D", "pipeline_unvalidated"


def build_pipeline_maturity_certificate(
    *,
    pmc_id: str,
    pipeline_version: str,
    cbr_artifact_id: str = "",
    cbr_verdict: str = "",
    fia_artifact_id: str = "",
    fia_verdict: str = "",
    sda_artifact_id: str = "",
    sda_verdict: str = "",
    limitations: list[str],
    created_at: str,
) -> PipelineMaturityCertificate:
    """Build a PipelineMaturityCertificate.

    Pass non-empty artifact_id + verdict for each assessed component.
    Empty artifact_id means the component was not assessed.
    """
    checks = [
        PMCComponentCheck(
            component_type="CBR",
            artifact_id=cbr_artifact_id,
            verdict=cbr_verdict,
            contributes_to_grade=_contributes_to_grade("CBR", cbr_verdict),
        ),
        PMCComponentCheck(
            component_type="FIA",
            artifact_id=fia_artifact_id,
            verdict=fia_verdict,
            contributes_to_grade=_contributes_to_grade("FIA", fia_verdict),
        ),
        PMCComponentCheck(
            component_type="SDA",
            artifact_id=sda_artifact_id,
            verdict=sda_verdict,
            contributes_to_grade=_contributes_to_grade("SDA", sda_verdict),
        ),
    ]
    n_assessed = sum(1 for c in checks if c.artifact_id)
    n_superior = sum(1 for c in checks if c.contributes_to_grade)
    grade, verdict = _compute_grade_and_verdict(n_assessed, n_superior)
    pmc = PipelineMaturityCertificate(
        pmc_id=pmc_id,
        pipeline_version=pipeline_version,
        component_checks=checks,
        n_components_assessed=n_assessed,
        n_superior_verdicts=n_superior,
        pmc_grade=grade,
        pmc_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_pipeline_maturity_certificate(pmc)
    return pmc


def format_pipeline_maturity_certificate(pmc: PipelineMaturityCertificate) -> str:
    lines = [
        f"Pipeline Maturity Certificate — {pmc.pmc_id}",
        f"Pipeline: {pmc.pipeline_version}",
        f"Grade: {pmc.pmc_grade}  |  Verdict: {pmc.pmc_verdict}",
        f"Components assessed: {pmc.n_components_assessed}/{len(REQUIRED_PMC_COMPONENTS)}  "
        f"|  Superior verdicts: {pmc.n_superior_verdicts}",
    ]
    lines.append("Component checks:")
    for check in pmc.component_checks:
        status = "ASSESSED" if check.artifact_id else "NOT_ASSESSED"
        contrib = " [contributes]" if check.contributes_to_grade else ""
        lines.append(
            f"  {check.component_type}: {status} "
            f"verdict={check.verdict or 'N/A'}{contrib}"
        )
    lines.append(f"Created: {pmc.created_at}")
    lines.append(f"Limitations: {'; '.join(pmc.limitations)}")
    lines.append(f"dry_lab_only: {pmc.dry_lab_only}")
    return "\n".join(lines)
