"""Recalibration engine: compute proposed weight deltas from intake + gate.

This module implements the *action* step that the intake and gate were
designed to gate:

    pilot predictions + lab actuals
        → intake report (descriptive)
        → gate verdict (may_recalibrate? True/False)
        → ENGINE (compute proposed weight changes)
        → human reviewer inspects + signs decision log
        → (future) weight update applied

The engine alone does NOT apply changes. It returns a proposal.
A human reviewer must inspect the proposal, verify the gate verdict,
sign a decision log entry, and then (separately) apply the update.

Design constraints:

* The engine RAISES ``PolicyViolationError`` when ``may_recalibrate``
  is ``False``. This is a safety floor: if the gate says no, there
  is no engine path that ignores it.
* The engine validates total proposed L1 delta against the policy's
  ``WEIGHT_CHANGE_L1_BUDGET`` rate limit. If the proposal exceeds the
  budget, it returns a ``BudgetExceeded`` verdict instead of a proposal.
* Each proposed delta includes a human-readable rationale string
  showing the computation.
* The engine does NOT modify ``prohibited_actions``, does NOT relax
  novelty/toxicity/hemolysis safety floors, and does NOT change
  success definitions.
* A ``--dry-run`` mode returns the same proposed deltas WITHOUT
  any side effect. The default mode also returns only a proposal
  (no side effects). Side effects require explicit human action.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from openamp_foundry.calibration.recalibration_gate import GateVerdict

# Conservative learning rate: how much of the accuracy gap to correct.
# 0.05 means at most a ±0.05 weight change per recalibration event.
_LEARNING_RATE = 0.05

_TARGET_ACCURACY = 0.5


class PolicyViolationError(RuntimeError):
    """Raised when ``may_recalibrate`` is ``False``.

    The gate verdict is the sole arbiter of whether recalibration may
    proceed. If the gate says no, the engine must refuse.
    """


class BudgetExceededError(RuntimeError):
    """Raised when the proposed L1 weight delta exceeds the policy budget.

    The proposal itself is preserved in the exception so reviewers can
    inspect what was attempted.
    """


@dataclass(frozen=True)
class WeightDelta:
    """A single proposed weight change for one scorer."""

    scorer: str
    current_weight: float
    proposed_weight: float
    delta: float
    precision: float | None
    recall: float | None
    n_positive: int
    n_negative: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WeightUpdateProposal:
    """Complete recalibration proposal from one intake report evaluation."""

    timestamp: str
    policy_version: int
    gate_passed: bool
    n_matched: int
    n_cohort_metrics: int
    l1_total: float
    l1_budget: float
    l1_within_budget: bool
    deltas: tuple[WeightDelta, ...]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "policy_version": self.policy_version,
            "gate_passed": self.gate_passed,
            "n_matched": self.n_matched,
            "n_cohort_metrics": self.n_cohort_metrics,
            "l1_total": self.l1_total,
            "l1_budget": self.l1_budget,
            "l1_within_budget": self.l1_within_budget,
            "deltas": [d.to_dict() for d in self.deltas],
            "notes": list(self.notes),
        }


def _scorer_for_metric(metric_key: str) -> str | None:
    """Map an intake cohort metric key to its corresponding scorer weight name.

    Returns ``None`` for metrics that have no direct scorer weight mapping.
    """
    mapping = {
        "activity_vs_active_mic": "activity",
        "rich_selectivity_vs_high_hemolysis": "safety",
        "synthesis_vs_feasibility": "synthesis",
        "novelty_vs_novel": "novelty",
    }
    return mapping.get(metric_key)


def _compute_delta(
    tp: int,
    fp: int,
    fn: int,
    tn: int,
    current_weight: float,
) -> tuple[float, float | None, float | None, str]:
    """Compute proposed weight delta from a confusion matrix.

    Uses precision (when TP+FP > 0) and recall (when TP+FN > 0) to
    determine direction and magnitude.

    * If precision >= 0.5 and recall >= 0.5, no change (scorer is
      performing adequately).
    * If precision < 0.5 (over-prediction), decrease weight.
    * If recall < 0.5 (under-prediction), increase weight.
    * The delta is ``learning_rate * (accuracy_gap)``, bounded
      so the weight stays in [0.0, 1.0].

    Returns (delta, precision, recall, rationale).
    """
    n_pred_pos = tp + fp
    n_actual_pos = tp + fn

    precision: float | None = tp / n_pred_pos if n_pred_pos > 0 else None
    recall: float | None = tp / n_actual_pos if n_actual_pos > 0 else None

    parts: list[str] = []

    delta = 0.0

    if precision is not None and precision < _TARGET_ACCURACY:
        gap = _TARGET_ACCURACY - precision
        adj = -_LEARNING_RATE * abs(gap)
        if adj < delta:
            delta = adj
        parts.append(
            f"precision={precision:.3f} < {_TARGET_ACCURACY} "
            f"(gap={gap:.3f}, adj={adj:.3f})"
        )

    if recall is not None and recall < _TARGET_ACCURACY:
        gap = _TARGET_ACCURACY - recall
        adj = _LEARNING_RATE * abs(gap)
        if adj > delta:
            delta = adj
        parts.append(
            f"recall={recall:.3f} < {_TARGET_ACCURACY} "
            f"(gap={gap:.3f}, adj={adj:.3f})"
        )

    if not parts:
        parts.append(
            f"precision={precision}, recall={recall} "
            f"both >= {_TARGET_ACCURACY}; no change needed"
        )

    purpose = "decrease" if delta < 0 else ("increase" if delta > 0 else "no change")
    rationale = (
        f"Proposed {purpose} of {abs(delta):.4f}: "
        + "; ".join(parts)
    )

    return delta, precision, recall, rationale


def compute_weight_update(
    intake_report: dict[str, Any],
    gate_verdict: GateVerdict,
    current_weights: dict[str, float],
    policy_l1_budget: float,
    *,
    learning_rate: float = _LEARNING_RATE,
    target_accuracy: float = _TARGET_ACCURACY,
) -> WeightUpdateProposal:
    """Compute proposed weight deltas from intake + gate.

    Args:
        intake_report: Output of
            ``build_calibration_intake_report()``.
        gate_verdict: Output of
            ``evaluate_recalibration_gate()``.
        current_weights: Dict mapping scorer name → current weight
            (e.g. ``{"activity": 0.40, "safety": 0.25, ...}``).
        policy_l1_budget: Maximum allowed L1 weight delta (from
            policy rate limits).
        learning_rate: Fraction of accuracy gap to correct per event.
        target_accuracy: Target precision/recall threshold.

    Returns:
        ``WeightUpdateProposal`` with deltas, L1 summary, and notes.

    Raises:
        ``PolicyViolationError`` if ``gate_verdict.may_recalibrate``
        is ``False``.
        ``BudgetExceededError`` if the raw proposal exceeds the L1
        budget (caller can catch, log, and still inspect the proposal).
    """
    if not gate_verdict.may_recalibrate:
        raise PolicyViolationError(
            "Recalibration forbidden: gate verdict returned "
            f"may_recalibrate=False. {len(gate_verdict.reasons)} "
            f"blocking reason(s): {'; '.join(gate_verdict.reasons)}"
        )

    cohort_metrics: dict[str, Any] = intake_report.get("cohort_metrics", {})
    n_matched: int = intake_report.get("n_matched_candidates", 0)

    deltas: list[WeightDelta] = []
    notes: list[str] = []

    for metric_key, metric in cohort_metrics.items():
        if metric.get("insufficient_data", True):
            notes.append(
                f"{metric_key}: insufficient_data, skipped"
            )
            continue

        tp = metric.get("tp")
        fp = metric.get("fp")
        fn = metric.get("fn")
        tn = metric.get("tn")
        # All int and not None check
        if not all(isinstance(v, int) and v is not None for v in (tp, fp, fn, tn)):
            notes.append(
                f"{metric_key}: incomplete confusion matrix "
                f"(tp={tp}, fp={fp}, fn={fn}, tn={tn}), skipped"
            )
            continue
        assert isinstance(tp, int) and isinstance(fp, int) and isinstance(fn, int) and isinstance(tn, int)

        scorer = _scorer_for_metric(metric_key)
        if scorer is None:
            notes.append(
                f"{metric_key}: no mapped scorer weight, skipped"
            )
            continue

        current_weight = current_weights.get(scorer)
        if current_weight is None:
            notes.append(
                f"{metric_key}: mapped to scorer {scorer!r} but "
                f"current_weights has no such key, skipped"
            )
            continue

        delta, precision, recall, rationale = _compute_delta(
            tp=tp, fp=fp, fn=fn, tn=tn,
            current_weight=current_weight,
        )

        proposed = max(0.0, min(1.0, current_weight + delta))

        deltas.append(WeightDelta(
            scorer=scorer,
            current_weight=current_weight,
            proposed_weight=proposed,
            delta=delta,
            precision=precision,
            recall=recall,
            n_positive=tp + fn,
            n_negative=fp + tn,
            rationale=rationale,
        ))

    l1_total = sum(abs(d.delta) for d in deltas)
    l1_within_budget = l1_total <= policy_l1_budget

    if not l1_within_budget:
        notes.append(
            f"Total L1 delta {l1_total:.4f} exceeds budget "
            f"{policy_l1_budget:.4f}. Proposal must be reduced."
        )

    proposal = WeightUpdateProposal(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        policy_version=gate_verdict.policy_version,
        gate_passed=gate_verdict.may_recalibrate,
        n_matched=n_matched,
        n_cohort_metrics=len(cohort_metrics),
        l1_total=l1_total,
        l1_budget=policy_l1_budget,
        l1_within_budget=l1_within_budget,
        deltas=tuple(deltas),
        notes=tuple(notes),
    )

    if not l1_within_budget:
        raise BudgetExceededError(
            f"Proposed L1 delta {l1_total:.4f} exceeds policy budget "
            f"{policy_l1_budget:.4f}. Proposal: {json.dumps(proposal.to_dict(), indent=2)}"
        )

    return proposal


def write_weight_update_proposal_json(
    proposal: WeightUpdateProposal,
    out_path: str | Path,
) -> Path:
    """Write a WeightUpdateProposal to JSON."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump(proposal.to_dict(), f, indent=2, sort_keys=False)
        f.write("\n")
    return p


def write_weight_update_proposal_markdown(
    proposal: WeightUpdateProposal,
    out_path: str | Path,
) -> Path:
    """Write a human-readable markdown recalibration proposal report."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# Recalibration Weight Update Proposal")
    lines.append("")
    lines.append("> This is a **proposal only**. It does NOT modify any")
    lines.append("> scoring weights, ensemble composition, or selection rules.")
    lines.append("> A human reviewer must inspect the proposal, verify the")
    lines.append("> gate verdict, sign a dated decision log entry, and THEN")
    lines.append("> manually apply the approved weight changes.")
    lines.append("")
    lines.append(f"- Proposed at: **{proposal.timestamp}**")
    lines.append(f"- Policy version: **{proposal.policy_version}**")
    lines.append(f"- Gate passed: **{proposal.gate_passed}**")
    lines.append(f"- Matched candidates: **{proposal.n_matched}**")
    lines.append(f"- Cohort metrics evaluated: **{proposal.n_cohort_metrics}**")
    lines.append("")
    lines.append("## L1 Budget")
    lines.append("")
    lines.append(f"- Total proposed L1 delta: **{proposal.l1_total:.4f}**")
    lines.append(f"- Policy budget: **{proposal.l1_budget}**")
    lines.append(
        f"- Within budget: **{proposal.l1_within_budget}**"
    )
    lines.append("")
    if not proposal.l1_within_budget:
        lines.append(
            "⚠ **Budget exceeded.** This proposal cannot be applied "
            "without reducing the total L1 delta."
        )
        lines.append("")

    if proposal.deltas:
        lines.append("## Proposed Weight Deltas")
        lines.append("")
        lines.append(
            "| Scorer | Current | Proposed | Delta | "
            "Precision | Recall | Pos/Neg | Rationale |"
        )
        lines.append(
            "|--------|---------|----------|-------|"
            "-----------|--------|---------|-----------|"
        )
        for d in proposal.deltas:
            p_str = f"{d.precision:.3f}" if d.precision is not None else "N/A"
            r_str = f"{d.recall:.3f}" if d.recall is not None else "N/A"
            lines.append(
                f"| {d.scorer} | {d.current_weight:.4f} | "
                f"{d.proposed_weight:.4f} | {d.delta:+.4f} | "
                f"{p_str} | {r_str} | "
                f"{d.n_positive}/{d.n_negative} | {d.rationale} |"
            )
        lines.append("")
    else:
        lines.append("**No weight changes proposed.**")
        lines.append("")

    if proposal.notes:
        lines.append("## Notes")
        lines.append("")
        for note in proposal.notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. A human reviewer must read this proposal.")
    lines.append("2. Verify the gate verdict at the referenced path.")
    lines.append("3. If approved, sign a dated decision log entry")
    lines.append("   (see ``docs/DECISION_RULES.md``).")
    lines.append("4. Apply the approved weight changes by editing")
    lines.append("   the scoring config file.")
    lines.append("5. Regenerate all benchmark outputs after applying.")
    lines.append("6. Record the new benchmark results alongside the")
    lines.append("   decision log.")
    lines.append("")

    p.write_text("\n".join(lines))
    return p
