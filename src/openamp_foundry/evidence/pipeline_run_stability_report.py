from __future__ import annotations
import statistics
from dataclasses import dataclass, field
from typing import List


VALID_STABILITY_VERDICTS = frozenset({
    "stable",
    "borderline",
    "unstable",
    "single_run",
})

VALID_COMPARISON_METHODS = frozenset({
    "identical_inputs",
    "bootstrap_resampling",
    "different_seeds",
    "different_subsets",
    "held_out_split",
})

DEFAULT_STABILITY_THRESHOLD = 2.0


@dataclass
class RunRankRecord:
    run_id: str
    rank: int
    score: float
    included_in_selection: bool


@dataclass
class PipelineRunStabilityReport:
    rsr_id: str
    candidate_family_id: str
    pipeline_version: str
    n_runs_compared: int
    run_records: List[RunRankRecord]
    rank_min: int
    rank_max: int
    rank_std: float
    score_mean: float
    score_std: float
    stability_verdict: str
    stability_threshold: float
    always_selected: bool
    never_selected: bool
    selection_consistency_rate: float
    dry_lab_only: bool
    limitations: List[str]
    created_at: str
    comparison_method: str
    n_candidate_families_in_run: int


@dataclass
class RSRValidationResult:
    valid: bool
    violations: List[str] = field(default_factory=list)


def validate_pipeline_run_stability_report(report: PipelineRunStabilityReport) -> RSRValidationResult:
    violations = []

    if not report.rsr_id.startswith("RSR-"):
        violations.append("rsr_id must start with 'RSR-'")

    if report.candidate_family_id.startswith("TOY-"):
        violations.append("TOY- candidate_family_id is not allowed in RSR- records")

    if not report.dry_lab_only:
        violations.append("dry_lab_only must be True for RSR- records")

    if report.n_runs_compared < 2:
        violations.append(f"n_runs_compared must be >= 2, got {report.n_runs_compared}")

    if len(report.run_records) != report.n_runs_compared:
        violations.append(
            f"len(run_records) ({len(report.run_records)}) must equal n_runs_compared ({report.n_runs_compared})"
        )

    if report.run_records:
        ranks = [r.rank for r in report.run_records]
        scores = [r.score for r in report.run_records]

        expected_rank_min = min(ranks)
        if report.rank_min != expected_rank_min:
            violations.append(
                f"rank_min ({report.rank_min}) must equal min rank ({expected_rank_min})"
            )

        expected_rank_max = max(ranks)
        if report.rank_max != expected_rank_max:
            violations.append(
                f"rank_max ({report.rank_max}) must equal max rank ({expected_rank_max})"
            )

        if len(ranks) >= 2:
            expected_rank_std = statistics.stdev(ranks)
            if abs(report.rank_std - expected_rank_std) > 0.01:
                violations.append(
                    f"rank_std ({report.rank_std}) inconsistent with stdev(ranks) ({expected_rank_std})"
                )

        expected_score_mean = statistics.mean(scores)
        if abs(report.score_mean - expected_score_mean) > 0.01:
            violations.append(
                f"score_mean ({report.score_mean}) inconsistent with mean(scores) ({expected_score_mean})"
            )

        if len(scores) >= 2:
            expected_score_std = statistics.stdev(scores)
            if abs(report.score_std - expected_score_std) > 0.01:
                violations.append(
                    f"score_std ({report.score_std}) inconsistent with stdev(scores) ({expected_score_std})"
                )

    if report.stability_verdict not in VALID_STABILITY_VERDICTS:
        violations.append(
            f"stability_verdict '{report.stability_verdict}' must be one of {sorted(VALID_STABILITY_VERDICTS)}"
        )

    if report.stability_threshold <= 0:
        violations.append(f"stability_threshold must be > 0, got {report.stability_threshold}")

    # stability_verdict consistency with rank_std and threshold
    if report.stability_verdict == "stable" and report.rank_std >= report.stability_threshold:
        violations.append(
            f"stability_verdict='stable' requires rank_std ({report.rank_std}) < stability_threshold ({report.stability_threshold})"
        )
    elif report.stability_verdict == "borderline":
        if not (report.stability_threshold <= report.rank_std < report.stability_threshold * 2):
            violations.append(
                f"stability_verdict='borderline' requires "
                f"stability_threshold ({report.stability_threshold}) <= rank_std ({report.rank_std}) "
                f"< stability_threshold * 2 ({report.stability_threshold * 2})"
            )
    elif report.stability_verdict == "unstable" and report.rank_std < report.stability_threshold * 2:
        violations.append(
            f"stability_verdict='unstable' requires rank_std ({report.rank_std}) "
            f">= stability_threshold * 2 ({report.stability_threshold * 2})"
        )
    elif report.stability_verdict == "single_run":
        violations.append("stability_verdict='single_run' is blocked; n_runs_compared >= 2 is required")

    if report.run_records:
        expected_always_selected = all(r.included_in_selection for r in report.run_records)
        if report.always_selected != expected_always_selected:
            violations.append(
                f"always_selected ({report.always_selected}) must be {expected_always_selected}"
            )

        expected_never_selected = not any(r.included_in_selection for r in report.run_records)
        if report.never_selected != expected_never_selected:
            violations.append(
                f"never_selected ({report.never_selected}) must be {expected_never_selected}"
            )

        expected_consistency = (
            sum(1 for r in report.run_records if r.included_in_selection)
            / len(report.run_records)
        )
        if abs(report.selection_consistency_rate - expected_consistency) > 0.001:
            violations.append(
                f"selection_consistency_rate ({report.selection_consistency_rate}) "
                f"inconsistent with expected ({expected_consistency})"
            )

    if not report.limitations:
        violations.append("limitations must be non-empty")

    if report.comparison_method not in VALID_COMPARISON_METHODS:
        violations.append(
            f"comparison_method '{report.comparison_method}' must be one of {sorted(VALID_COMPARISON_METHODS)}"
        )

    if report.n_candidate_families_in_run < 1:
        violations.append(
            f"n_candidate_families_in_run must be >= 1, got {report.n_candidate_families_in_run}"
        )

    return RSRValidationResult(valid=len(violations) == 0, violations=violations)


def build_pipeline_run_stability_report(
    rsr_id: str,
    candidate_family_id: str,
    pipeline_version: str,
    run_records: List[RunRankRecord],
    comparison_method: str,
    n_candidate_families_in_run: int,
    limitations: List[str],
    created_at: str,
    stability_threshold: float = DEFAULT_STABILITY_THRESHOLD,
) -> PipelineRunStabilityReport:
    n_runs_compared = len(run_records)

    if n_runs_compared < 2:
        raise ValueError(f"At least 2 run_records required, got {n_runs_compared}")

    ranks = [r.rank for r in run_records]
    scores = [r.score for r in run_records]

    rank_min = min(ranks)
    rank_max = max(ranks)
    rank_std = statistics.stdev(ranks) if n_runs_compared >= 2 else 0.0
    score_mean = statistics.mean(scores)
    score_std = statistics.stdev(scores) if n_runs_compared >= 2 else 0.0

    if rank_std < stability_threshold:
        stability_verdict = "stable"
    elif rank_std < stability_threshold * 2:
        stability_verdict = "borderline"
    else:
        stability_verdict = "unstable"

    always_selected = all(r.included_in_selection for r in run_records)
    never_selected = not any(r.included_in_selection for r in run_records)
    selection_consistency_rate = (
        sum(1 for r in run_records if r.included_in_selection) / n_runs_compared
    )

    report = PipelineRunStabilityReport(
        rsr_id=rsr_id,
        candidate_family_id=candidate_family_id,
        pipeline_version=pipeline_version,
        n_runs_compared=n_runs_compared,
        run_records=run_records,
        rank_min=rank_min,
        rank_max=rank_max,
        rank_std=rank_std,
        score_mean=score_mean,
        score_std=score_std,
        stability_verdict=stability_verdict,
        stability_threshold=stability_threshold,
        always_selected=always_selected,
        never_selected=never_selected,
        selection_consistency_rate=selection_consistency_rate,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
        comparison_method=comparison_method,
        n_candidate_families_in_run=n_candidate_families_in_run,
    )

    result = validate_pipeline_run_stability_report(report)
    if not result.valid:
        raise ValueError(f"Invalid RSR: {result.violations}")
    return report


def format_pipeline_run_stability_report(report: PipelineRunStabilityReport) -> str:
    lines = [
        f"Pipeline Run Stability Report — {report.rsr_id}",
        f"Candidate Family: {report.candidate_family_id}  |  Pipeline: {report.pipeline_version}",
        f"Verdict: {report.stability_verdict}  |  Runs Compared: {report.n_runs_compared}",
        f"Rank Range: [{report.rank_min}–{report.rank_max}]  |  Std: {report.rank_std:.2f}  |  Threshold: {report.stability_threshold:.2f}",
        f"Score Mean: {report.score_mean:.4f}  |  Score Std: {report.score_std:.4f}",
        f"Always Selected: {report.always_selected}  |  Never Selected: {report.never_selected}",
        f"Selection Consistency: {report.selection_consistency_rate:.3f}",
        f"Comparison Method: {report.comparison_method}",
        f"Total Families in Run: {report.n_candidate_families_in_run}",
        f"Created: {report.created_at}",
        f"Limitations: {'; '.join(report.limitations)}",
        "dry_lab_only: True",
    ]
    return "\n".join(lines)
