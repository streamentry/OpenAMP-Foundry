from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


VALID_BASELINE_COMPARISON_OUTCOMES = frozenset({
    "outside_known_space",   # charge/length/hydrophobicity outside all known AMP families
    "within_known_space",    # candidates fall inside known AMP property space
    "edge_of_known_space",   # candidates at the boundary — ambiguous
    "comparison_not_run",    # baseline comparison was not performed
})

VALID_NOVELTY_STRENGTH_GRADES = frozenset({
    "strong",       # multiple independent hard evidence sources agree
    "moderate",     # one hard evidence source, baseline outside known space
    "weak",         # only soft evidence (expert) or edge of known space
    "not_supported", # evidence argues against novelty
})

VALID_CHEAP_BASELINES_CHECKED = frozenset({
    "charge_distribution",
    "length_distribution",
    "hydrophobicity_profile",
    "isoelectric_point",
    "aromaticity",
})


@dataclass
class FamilyNoveltyReport:
    fnr_id: str
    cfc_id: str
    family_name: str
    cheap_baselines_checked: List[str]
    baseline_comparison_outcome: str
    novelty_strength_grade: str
    n_known_families_compared: int
    known_families_compared: List[str]
    cheap_enemy_score: Optional[float]
    family_score: Optional[float]
    dry_lab_only: bool
    limitations: str
    notes: str = ""


@dataclass
class FNRValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_family_novelty_report(report: FamilyNoveltyReport) -> FNRValidationResult:
    violations = []

    if not report.fnr_id.startswith("FNR-"):
        violations.append("fnr_id must start with 'FNR-'")

    if not report.cfc_id.startswith("CFC-"):
        violations.append("cfc_id must start with 'CFC-'")

    if not report.family_name or len(report.family_name.strip()) < 3:
        violations.append("family_name must be at least 3 characters")

    if not report.cheap_baselines_checked:
        violations.append("at least one cheap_baseline must be checked")

    for cb in report.cheap_baselines_checked:
        if cb not in VALID_CHEAP_BASELINES_CHECKED:
            violations.append(
                f"cheap_baseline '{cb}' must be one of {sorted(VALID_CHEAP_BASELINES_CHECKED)}"
            )

    if report.baseline_comparison_outcome not in VALID_BASELINE_COMPARISON_OUTCOMES:
        violations.append(
            f"baseline_comparison_outcome '{report.baseline_comparison_outcome}' must be one of "
            f"{sorted(VALID_BASELINE_COMPARISON_OUTCOMES)}"
        )

    if report.novelty_strength_grade not in VALID_NOVELTY_STRENGTH_GRADES:
        violations.append(
            f"novelty_strength_grade '{report.novelty_strength_grade}' must be one of "
            f"{sorted(VALID_NOVELTY_STRENGTH_GRADES)}"
        )

    if report.n_known_families_compared < 0:
        violations.append("n_known_families_compared must be >= 0")

    # strong novelty grade requires outside_known_space outcome
    if report.novelty_strength_grade == "strong" and report.baseline_comparison_outcome != "outside_known_space":
        violations.append(
            "novelty_strength_grade='strong' requires baseline_comparison_outcome='outside_known_space'"
        )

    # not_supported grade should not have outside_known_space
    if report.novelty_strength_grade == "not_supported" and report.baseline_comparison_outcome == "outside_known_space":
        violations.append(
            "novelty_strength_grade='not_supported' is inconsistent with baseline_comparison_outcome='outside_known_space'"
        )

    # comparison_not_run outcome must not claim strong grade
    if report.baseline_comparison_outcome == "comparison_not_run" and report.novelty_strength_grade == "strong":
        violations.append(
            "novelty_strength_grade='strong' requires a completed baseline comparison (not 'comparison_not_run')"
        )

    # cheap_enemy_score and family_score consistency
    if report.cheap_enemy_score is not None:
        if not (0.0 <= report.cheap_enemy_score <= 1.0):
            violations.append(f"cheap_enemy_score {report.cheap_enemy_score} must be in [0.0, 1.0]")

    if report.family_score is not None:
        if not (0.0 <= report.family_score <= 1.0):
            violations.append(f"family_score {report.family_score} must be in [0.0, 1.0]")

    if not report.dry_lab_only:
        violations.append("dry_lab_only must be True for FNR- records (novelty report is computational)")

    if not report.limitations or len(report.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    return FNRValidationResult(valid=len(violations) == 0, violations=violations)


def build_family_novelty_report(
    fnr_id: str,
    cfc_id: str,
    family_name: str,
    cheap_baselines_checked: List[str],
    baseline_comparison_outcome: str,
    novelty_strength_grade: str,
    n_known_families_compared: int,
    known_families_compared: List[str],
    limitations: str,
    cheap_enemy_score: Optional[float] = None,
    family_score: Optional[float] = None,
    notes: str = "",
) -> FamilyNoveltyReport:
    report = FamilyNoveltyReport(
        fnr_id=fnr_id,
        cfc_id=cfc_id,
        family_name=family_name,
        cheap_baselines_checked=cheap_baselines_checked,
        baseline_comparison_outcome=baseline_comparison_outcome,
        novelty_strength_grade=novelty_strength_grade,
        n_known_families_compared=n_known_families_compared,
        known_families_compared=known_families_compared,
        cheap_enemy_score=cheap_enemy_score,
        family_score=family_score,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
    )
    result = validate_family_novelty_report(report)
    if not result.valid:
        raise ValueError(f"Invalid FNR: {result.violations}")
    return report


def format_family_novelty_report(report: FamilyNoveltyReport) -> str:
    lines = [
        f"Family Novelty Report — {report.fnr_id}",
        f"Family: {report.family_name}  |  CFC: {report.cfc_id}",
        f"Novelty Strength: {report.novelty_strength_grade}",
        f"Baseline Outcome: {report.baseline_comparison_outcome}",
        f"Cheap Baselines Checked: {', '.join(report.cheap_baselines_checked)}",
        f"Known Families Compared: {report.n_known_families_compared}",
    ]
    if report.known_families_compared:
        lines.append(f"Families: {', '.join(report.known_families_compared)}")
    if report.cheap_enemy_score is not None:
        lines.append(f"Cheap Enemy Score: {report.cheap_enemy_score:.3f}")
    if report.family_score is not None:
        lines.append(f"Family Score: {report.family_score:.3f}")
    lines.append(f"Limitations: {report.limitations}")
    if report.notes:
        lines.append(f"Notes: {report.notes}")
    lines.append("dry_lab_only: True (computational novelty assessment)")
    return "\n".join(lines)
