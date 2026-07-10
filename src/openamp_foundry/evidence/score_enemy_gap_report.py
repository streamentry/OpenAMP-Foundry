from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


VALID_GAP_VERDICTS = frozenset({
    "gap_meaningful",         # pipeline score meaningfully exceeds best cheap baseline
    "gap_marginal",           # pipeline score exceeds baseline but margin is small
    "gap_absent",             # pipeline score does not exceed best cheap baseline
    "comparison_not_run",     # no cheap baseline comparison was performed
})

VALID_CHEAP_ENEMY_TYPES = frozenset({
    "charge_score",
    "length_score",
    "hydrophobicity_score",
    "isoelectric_point_score",
    "aromaticity_score",
    "combined_charge_length",
    "random_baseline",
    "sequence_similarity_to_known",
})

VALID_GAP_ASSESSMENT_METHODS = frozenset({
    "absolute_difference",
    "relative_margin",
    "rank_correlation",
    "precision_at_k_delta",
    "auc_delta",
})

MINIMUM_MEANINGFUL_GAP = 0.05  # absolute score units


@dataclass
class CheapEnemyResult:
    enemy_type: str
    enemy_score: float
    pipeline_score: float
    gap: float
    gap_exceeds_threshold: bool


@dataclass
class ScoreEnemyGapReport:
    seg_id: str
    run_id: str
    candidate_family_id: str
    gap_verdict: str
    gap_assessment_method: str
    pipeline_score: float
    best_enemy_score: float
    best_enemy_type: str
    gap: float
    minimum_meaningful_gap: float
    n_enemies_tested: int
    enemy_results: List[CheapEnemyResult]
    dry_lab_only: bool
    limitations: str
    notes: str = ""
    fnr_id: Optional[str] = None


@dataclass
class SEGValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_score_enemy_gap_report(report: ScoreEnemyGapReport) -> SEGValidationResult:
    violations = []

    if not report.seg_id.startswith("SEG-"):
        violations.append("seg_id must start with 'SEG-'")

    if not report.run_id:
        violations.append("run_id is required")

    if not report.candidate_family_id:
        violations.append("candidate_family_id is required")

    if report.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in real SEG- records")

    if report.gap_verdict not in VALID_GAP_VERDICTS:
        violations.append(
            f"gap_verdict '{report.gap_verdict}' must be one of {sorted(VALID_GAP_VERDICTS)}"
        )

    if report.gap_assessment_method not in VALID_GAP_ASSESSMENT_METHODS:
        violations.append(
            f"gap_assessment_method '{report.gap_assessment_method}' must be one of {sorted(VALID_GAP_ASSESSMENT_METHODS)}"
        )

    if not (0.0 <= report.pipeline_score <= 1.0):
        violations.append(f"pipeline_score must be in [0.0, 1.0], got {report.pipeline_score}")

    if not (0.0 <= report.best_enemy_score <= 1.0):
        violations.append(f"best_enemy_score must be in [0.0, 1.0], got {report.best_enemy_score}")

    if report.best_enemy_type not in VALID_CHEAP_ENEMY_TYPES:
        violations.append(
            f"best_enemy_type '{report.best_enemy_type}' must be one of {sorted(VALID_CHEAP_ENEMY_TYPES)}"
        )

    expected_gap = round(report.pipeline_score - report.best_enemy_score, 6)
    if abs(report.gap - expected_gap) > 1e-4:
        violations.append(
            f"gap ({report.gap}) inconsistent with pipeline_score - best_enemy_score ({expected_gap})"
        )

    if report.minimum_meaningful_gap <= 0.0:
        violations.append("minimum_meaningful_gap must be > 0.0")

    if report.n_enemies_tested < 1:
        violations.append("n_enemies_tested must be >= 1")

    if report.n_enemies_tested != len(report.enemy_results):
        violations.append(
            f"n_enemies_tested ({report.n_enemies_tested}) must match len(enemy_results) ({len(report.enemy_results)})\n"
        )

    # Validate each enemy result
    for i, er in enumerate(report.enemy_results):
        if er.enemy_type not in VALID_CHEAP_ENEMY_TYPES:
            violations.append(f"enemy_results[{i}].enemy_type '{er.enemy_type}' not in VALID_CHEAP_ENEMY_TYPES")
        if not (0.0 <= er.enemy_score <= 1.0):
            violations.append(f"enemy_results[{i}].enemy_score must be in [0.0, 1.0]")
        if not (0.0 <= er.pipeline_score <= 1.0):
            violations.append(f"enemy_results[{i}].pipeline_score must be in [0.0, 1.0]")

    # gap_meaningful requires gap >= minimum_meaningful_gap
    if report.gap_verdict == "gap_meaningful" and report.gap < report.minimum_meaningful_gap:
        violations.append(
            f"gap_verdict='gap_meaningful' requires gap ({report.gap}) >= minimum_meaningful_gap ({report.minimum_meaningful_gap})"
        )

    # gap_absent requires gap <= 0
    if report.gap_verdict == "gap_absent" and report.gap > 0.0:
        violations.append(
            f"gap_verdict='gap_absent' requires gap ({report.gap}) <= 0.0"
        )

    # comparison_not_run requires n_enemies_tested == 0 (or we block it with n_enemies check above)
    # Actually allow comparison_not_run with enemy_results=[] but n_enemies_tested=0
    if report.gap_verdict == "comparison_not_run" and report.n_enemies_tested > 0:
        violations.append(
            "gap_verdict='comparison_not_run' requires n_enemies_tested == 0"
        )

    if not report.dry_lab_only:
        violations.append("dry_lab_only must be True for SEG- records")

    if not report.limitations or len(report.limitations.strip()) < 10:
        violations.append("limitations must be a non-empty string (at least 10 characters)")

    if report.fnr_id is not None and not report.fnr_id.startswith("FNR-"):
        violations.append("fnr_id must start with 'FNR-' when provided")

    return SEGValidationResult(valid=len(violations) == 0, violations=violations)


def build_score_enemy_gap_report(
    seg_id: str,
    run_id: str,
    candidate_family_id: str,
    gap_assessment_method: str,
    pipeline_score: float,
    enemy_results: List[CheapEnemyResult],
    limitations: str,
    notes: str = "",
    fnr_id: Optional[str] = None,
    minimum_meaningful_gap: float = MINIMUM_MEANINGFUL_GAP,
) -> ScoreEnemyGapReport:
    if not enemy_results:
        best_enemy_score = 0.0
        best_enemy_type = "random_baseline"
        gap = pipeline_score
        gap_verdict = "comparison_not_run"
        n_enemies_tested = 0
    else:
        best_er = max(enemy_results, key=lambda er: er.enemy_score)
        best_enemy_score = best_er.enemy_score
        best_enemy_type = best_er.enemy_type
        gap = round(pipeline_score - best_enemy_score, 6)
        n_enemies_tested = len(enemy_results)
        if gap <= 0.0:
            gap_verdict = "gap_absent"
        elif gap < minimum_meaningful_gap:
            gap_verdict = "gap_marginal"
        else:
            gap_verdict = "gap_meaningful"

    report = ScoreEnemyGapReport(
        seg_id=seg_id,
        run_id=run_id,
        candidate_family_id=candidate_family_id,
        gap_verdict=gap_verdict,
        gap_assessment_method=gap_assessment_method,
        pipeline_score=pipeline_score,
        best_enemy_score=best_enemy_score,
        best_enemy_type=best_enemy_type,
        gap=gap,
        minimum_meaningful_gap=minimum_meaningful_gap,
        n_enemies_tested=n_enemies_tested,
        enemy_results=enemy_results,
        dry_lab_only=True,
        limitations=limitations,
        notes=notes,
        fnr_id=fnr_id,
    )
    result = validate_score_enemy_gap_report(report)
    if not result.valid:
        raise ValueError(f"Invalid SEG: {result.violations}")
    return report


def format_score_enemy_gap_report(report: ScoreEnemyGapReport) -> str:
    lines = [
        f"Score vs Cheap-Enemy Gap Report — {report.seg_id}",
        f"Run: {report.run_id}  |  Family: {report.candidate_family_id}",
        f"Verdict: {report.gap_verdict}",
        f"Pipeline Score: {report.pipeline_score:.4f}  |  Best Enemy ({report.best_enemy_type}): {report.best_enemy_score:.4f}",
        f"Gap: {report.gap:.4f}  |  Minimum Meaningful Gap: {report.minimum_meaningful_gap:.4f}",
        f"Enemies Tested: {report.n_enemies_tested}",
        f"Assessment Method: {report.gap_assessment_method}",
    ]
    if report.fnr_id:
        lines.append(f"FNR Link: {report.fnr_id}")
    lines.append(f"Limitations: {report.limitations}")
    if report.notes:
        lines.append(f"Notes: {report.notes}")
    lines.append("dry_lab_only: True")
    return "\n".join(lines)
