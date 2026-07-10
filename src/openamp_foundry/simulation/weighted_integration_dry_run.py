"""Weighted integration dry-run report schema (Phase H H8).

WDR- records show what would change in candidate rankings IF the weighted
simulation integration module were given ranking authority — without
applying that change. The integration gate remains closed.

This is a COUNTERFACTUAL report. It does not alter rankings, scores,
or evidence certificates. It exists only to make the potential impact
of enabling weighted integration visible to human reviewers.

Purpose: let reviewers see what would move before deciding whether to
open the integration gate.
"""

from dataclasses import dataclass, field

WEIGHTED_INTEGRATION_DRY_RUN_ID_PREFIX = "WDR-"

VALID_INTEGRATION_GATE_STATUSES: frozenset = frozenset({
    "closed",
    "open_for_review",
    "approved",
    "rejected",
})

VALID_RANK_CHANGE_MAGNITUDES: frozenset = frozenset({
    "none",
    "minor",
    "moderate",
    "major",
    "unknown",
})

VALID_DRY_RUN_OUTCOMES: frozenset = frozenset({
    "no_change",
    "reordering_only",
    "candidates_added",
    "candidates_removed",
    "mixed_changes",
    "insufficient_data",
})

MAJOR_RANK_CHANGE_THRESHOLD: int = 5
SIGNIFICANT_FRACTION_THRESHOLD: float = 0.20
FRACTION_TOLERANCE: float = 0.01

GATE_CLOSED_DISCLAIMER = (
    "This is a counterfactual dry-run report. "
    "The weighted integration gate is closed. "
    "No ranking changes have been applied. "
    "Computational dry-lab only."
)


@dataclass
class WeightedIntegrationDryRunReport:
    report_id: str
    batch_id: str
    integration_gate_status: str
    n_candidates_evaluated: int
    n_candidates_would_change_rank: int
    fraction_would_change_rank: float
    max_rank_delta: int
    rank_change_magnitude: str
    dry_run_outcome: str
    integration_gate_currently_closed: bool
    results_applied_to_ranking: bool
    dry_lab_only: bool
    gate_closed_disclaimer: str
    notes: str
    created_at: str


def validate_weighted_integration_dry_run_report(
    report: WeightedIntegrationDryRunReport,
) -> list[str]:
    errors: list[str] = []

    if not report.report_id.startswith(WEIGHTED_INTEGRATION_DRY_RUN_ID_PREFIX):
        errors.append(
            f"report_id must start with '{WEIGHTED_INTEGRATION_DRY_RUN_ID_PREFIX}', "
            f"got: {report.report_id!r}"
        )

    if report.integration_gate_status not in VALID_INTEGRATION_GATE_STATUSES:
        errors.append(
            f"integration_gate_status {report.integration_gate_status!r} "
            f"not in VALID_INTEGRATION_GATE_STATUSES"
        )

    if report.rank_change_magnitude not in VALID_RANK_CHANGE_MAGNITUDES:
        errors.append(
            f"rank_change_magnitude {report.rank_change_magnitude!r} "
            f"not in VALID_RANK_CHANGE_MAGNITUDES"
        )

    if report.dry_run_outcome not in VALID_DRY_RUN_OUTCOMES:
        errors.append(
            f"dry_run_outcome {report.dry_run_outcome!r} not in VALID_DRY_RUN_OUTCOMES"
        )

    if not (0.0 <= report.fraction_would_change_rank <= 1.0):
        errors.append(
            f"fraction_would_change_rank must be in [0.0, 1.0], "
            f"got: {report.fraction_would_change_rank}"
        )

    if report.n_candidates_evaluated > 0:
        computed = report.n_candidates_would_change_rank / report.n_candidates_evaluated
        if abs(computed - report.fraction_would_change_rank) > FRACTION_TOLERANCE:
            errors.append(
                f"fraction_would_change_rank {report.fraction_would_change_rank} does not match "
                f"n_candidates_would_change_rank / n_candidates_evaluated = {computed:.4f} "
                f"(tolerance {FRACTION_TOLERANCE})"
            )

    if report.n_candidates_would_change_rank > report.n_candidates_evaluated:
        errors.append(
            f"n_candidates_would_change_rank ({report.n_candidates_would_change_rank}) "
            f"cannot exceed n_candidates_evaluated ({report.n_candidates_evaluated})"
        )

    if not report.dry_lab_only:
        errors.append("dry_lab_only must be True for all weighted integration dry-run reports")

    if report.results_applied_to_ranking:
        errors.append(
            "results_applied_to_ranking must be False: "
            "this is a dry-run report; results must NOT be applied to ranking"
        )

    if report.integration_gate_status == "closed" and not report.integration_gate_currently_closed:
        errors.append(
            "integration_gate_currently_closed must be True when "
            "integration_gate_status is 'closed'"
        )

    if "dry-run" not in report.gate_closed_disclaimer.lower() and \
       "counterfactual" not in report.gate_closed_disclaimer.lower():
        errors.append(
            "gate_closed_disclaimer must mention 'dry-run' or 'counterfactual' "
            "to clearly label this as a non-applied report"
        )

    if not report.batch_id.strip():
        errors.append("batch_id must not be blank")

    if not report.created_at.strip():
        errors.append("created_at must not be blank")

    return errors


def format_weighted_integration_dry_run_report(
    report: WeightedIntegrationDryRunReport,
) -> str:
    lines = [
        f"Weighted Integration Dry-Run Report {report.report_id}",
        f"[COUNTERFACTUAL — NO CHANGES APPLIED]",
        f"Batch: {report.batch_id}",
        f"Integration gate: {report.integration_gate_status}",
        f"Candidates evaluated: {report.n_candidates_evaluated}",
        f"  Would change rank: {report.n_candidates_would_change_rank} "
        f"({report.fraction_would_change_rank:.1%})",
        f"  Max rank delta: {report.max_rank_delta}",
        f"Rank change magnitude: {report.rank_change_magnitude}",
        f"Dry-run outcome: {report.dry_run_outcome}",
        f"Results applied to ranking: {report.results_applied_to_ranking}",
        f"Dry-lab only: {report.dry_lab_only}",
    ]
    lines.append(f"Disclaimer: {report.gate_closed_disclaimer}")
    if report.notes:
        lines.append(f"Notes: {report.notes}")
    lines.append(f"Created: {report.created_at}")
    return "\n".join(lines)
