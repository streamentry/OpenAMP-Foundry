from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


VALID_SELECTION_BASES = frozenset({
    "score_rank",              # selected primarily by pipeline score rank
    "safety_gate_passed",      # selected because it passed all safety screens
    "novelty_evidence",        # selected due to novelty evidence (CFC/FNR)
    "benchmark_performance",   # selected due to benchmark performance vs baselines
    "expert_review",           # selected following expert human review
    "calibration_signal",      # selected based on calibration-adjusted confidence
    "diversity_criteria",      # selected to maximize batch diversity
    "not_specified",           # selection basis not documented (should be avoided)
})

VALID_LEDGER_COMPLETENESS_GRADES = frozenset({
    "complete",       # all expected artifact references are present
    "partial",        # some expected artifacts are missing but core selection documented
    "incomplete",     # major artifacts missing; selection not fully traceable
    "not_assessed",   # completeness not checked
})

REQUIRED_SELECTION_ARTIFACT_TYPES = frozenset({
    "BSP",   # batch selection proposal
    "SEG",   # score vs enemy gap report
    "SRG",   # scientific review readiness gate
})

VALID_SELECTION_OUTCOME_TYPES = frozenset({
    "selected_for_pilot",
    "selected_for_next_batch",
    "selected_for_external_review",
    "deselected_safety",
    "deselected_low_score",
    "deselected_insufficient_evidence",
    "held_pending_review",
})


@dataclass
class ArtifactReference:
    artifact_type: str
    artifact_id: str
    influence_description: str


@dataclass
class SelectionTransparencyLedger:
    stl_id: str
    run_id: str
    candidate_family_id: str
    selection_basis: str
    selection_outcome: str
    completeness_grade: str
    artifact_references: List[ArtifactReference]
    n_artifacts_referenced: int
    has_required_artifacts: bool
    missing_required_artifact_types: List[str]
    seg_id: Optional[str]
    srg_id: Optional[str]
    bsp_id: Optional[str]
    dry_lab_only: bool
    limitations: str
    notes: str = ""


@dataclass
class STLValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_selection_transparency_ledger(ledger: SelectionTransparencyLedger) -> STLValidationResult:
    violations = []

    if not ledger.stl_id.startswith("STL-"):
        violations.append("stl_id must start with 'STL-'")

    if not ledger.run_id:
        violations.append("run_id is required")

    if not ledger.candidate_family_id:
        violations.append("candidate_family_id is required")

    if ledger.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in real STL- records")

    if ledger.selection_basis not in VALID_SELECTION_BASES:
        violations.append(
            f"selection_basis '{ledger.selection_basis}' must be one of {sorted(VALID_SELECTION_BASES)}"
        )

    if ledger.selection_outcome not in VALID_SELECTION_OUTCOME_TYPES:
        violations.append(
            f"selection_outcome '{ledger.selection_outcome}' must be one of {sorted(VALID_SELECTION_OUTCOME_TYPES)}"
        )

    if ledger.completeness_grade not in VALID_LEDGER_COMPLETENESS_GRADES:
        violations.append(
            f"completeness_grade '{ledger.completeness_grade}' must be one of {sorted(VALID_LEDGER_COMPLETENESS_GRADES)}"
        )

    if ledger.n_artifacts_referenced != len(ledger.artifact_references):
        violations.append(
            f"n_artifacts_referenced ({ledger.n_artifacts_referenced}) must match len(artifact_references) ({len(ledger.artifact_references)})"
        )

    if ledger.n_artifacts_referenced < 1:
        violations.append("at least one artifact_reference is required")

    # Validate each artifact reference
    for i, ref in enumerate(ledger.artifact_references):
        if not ref.artifact_type:
            violations.append(f"artifact_references[{i}].artifact_type is required")
        if not ref.artifact_id:
            violations.append(f"artifact_references[{i}].artifact_id is required")
        if not ref.influence_description or len(ref.influence_description.strip()) < 5:
            violations.append(f"artifact_references[{i}].influence_description must be at least 5 chars")

    # Check presence of required artifacts
    present_types = {ref.artifact_type for ref in ledger.artifact_references}
    missing = sorted(REQUIRED_SELECTION_ARTIFACT_TYPES - present_types)
    if sorted(ledger.missing_required_artifact_types) != missing:
        violations.append(
            f"missing_required_artifact_types {ledger.missing_required_artifact_types} does not match computed {missing}"
        )

    expected_has_required = len(missing) == 0
    if ledger.has_required_artifacts != expected_has_required:
        violations.append(
            f"has_required_artifacts ({ledger.has_required_artifacts}) inconsistent with missing types ({missing})"
        )

    # complete grade requires has_required_artifacts
    if ledger.completeness_grade == "complete" and not ledger.has_required_artifacts:
        violations.append(
            "completeness_grade='complete' requires has_required_artifacts=True"
        )

    # incomplete grade must not have all required artifacts
    if ledger.completeness_grade == "incomplete" and ledger.has_required_artifacts and not missing:
        violations.append(
            "completeness_grade='incomplete' should not have all required artifacts present"
        )

    # not_specified selection_basis is a weak signal
    if ledger.selection_basis == "not_specified":
        violations.append(
            "selection_basis='not_specified' is not allowed; document the actual selection basis"
        )

    # ID field prefix checks
    if ledger.seg_id is not None and not ledger.seg_id.startswith("SEG-"):
        violations.append("seg_id must start with 'SEG-' when provided")

    if ledger.srg_id is not None and not ledger.srg_id.startswith("SRG-"):
        violations.append("srg_id must start with 'SRG-' when provided")

    if ledger.bsp_id is not None and not ledger.bsp_id.startswith("BSP-"):
        violations.append("bsp_id must start with 'BSP-' when provided")

    if not ledger.dry_lab_only:
        violations.append("dry_lab_only must be True for STL- records")

    if not ledger.limitations or len(ledger.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    return STLValidationResult(valid=len(violations) == 0, violations=violations)


def build_selection_transparency_ledger(
    stl_id: str,
    run_id: str,
    candidate_family_id: str,
    selection_basis: str,
    selection_outcome: str,
    artifact_references: List[ArtifactReference],
    limitations: str,
    notes: str = "",
    seg_id: Optional[str] = None,
    srg_id: Optional[str] = None,
    bsp_id: Optional[str] = None,
) -> SelectionTransparencyLedger:
    present_types = {ref.artifact_type for ref in artifact_references}
    missing = sorted(REQUIRED_SELECTION_ARTIFACT_TYPES - present_types)
    has_required = len(missing) == 0

    if has_required and len(artifact_references) >= len(REQUIRED_SELECTION_ARTIFACT_TYPES):
        completeness_grade = "complete"
    elif missing and len(missing) < len(REQUIRED_SELECTION_ARTIFACT_TYPES):
        completeness_grade = "partial"
    elif not artifact_references:
        completeness_grade = "incomplete"
    else:
        completeness_grade = "partial"

    ledger = SelectionTransparencyLedger(
        stl_id=stl_id,
        run_id=run_id,
        candidate_family_id=candidate_family_id,
        selection_basis=selection_basis,
        selection_outcome=selection_outcome,
        completeness_grade=completeness_grade,
        artifact_references=artifact_references,
        n_artifacts_referenced=len(artifact_references),
        has_required_artifacts=has_required,
        missing_required_artifact_types=missing,
        seg_id=seg_id,
        srg_id=srg_id,
        bsp_id=bsp_id,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
    )
    result = validate_selection_transparency_ledger(ledger)
    if not result.valid:
        raise ValueError(f"Invalid STL: {result.violations}")
    return ledger


def format_selection_transparency_ledger(ledger: SelectionTransparencyLedger) -> str:
    lines = [
        f"Selection Transparency Ledger — {ledger.stl_id}",
        f"Run: {ledger.run_id}  |  Family: {ledger.candidate_family_id}",
        f"Selection Basis: {ledger.selection_basis}",
        f"Outcome: {ledger.selection_outcome}",
        f"Completeness Grade: {ledger.completeness_grade}",
        f"Artifacts Referenced: {ledger.n_artifacts_referenced}",
        f"Required Artifacts Present: {ledger.has_required_artifacts}",
    ]
    if ledger.missing_required_artifact_types:
        lines.append(f"Missing Required: {', '.join(ledger.missing_required_artifact_types)}")
    for ref in ledger.artifact_references:
        lines.append(f"  [{ref.artifact_type}] {ref.artifact_id}: {ref.influence_description}")
    if ledger.seg_id:
        lines.append(f"SEG Link: {ledger.seg_id}")
    if ledger.srg_id:
        lines.append(f"SRG Link: {ledger.srg_id}")
    if ledger.bsp_id:
        lines.append(f"BSP Link: {ledger.bsp_id}")
    lines.append(f"Limitations: {ledger.limitations}")
    if ledger.notes:
        lines.append(f"Notes: {ledger.notes}")
    lines.append("dry_lab_only: True")
    return "\n".join(lines)
