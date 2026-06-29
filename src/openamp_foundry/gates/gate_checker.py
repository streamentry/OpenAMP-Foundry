"""Pipeline decision gates — pass/fail checks for pre-wet-lab readiness.

Each gate has a hardcoded threshold (anti-cherry-picking). To change a threshold,
modify the source and create a new commit — no config file override allowed.
"""

from __future__ import annotations

from typing import Any, NamedTuple


class GateResult(NamedTuple):
    gate: int
    name: str
    passed: bool
    value: float | str | None
    threshold: str
    detail: str


def check_gate_1_auroc(validation_data: dict[str, Any]) -> GateResult:
    """AUROC > 0.70 (synthesis gate)."""
    auroc = validation_data.get("auroc", 0.0)
    passed = auroc >= 0.70
    return GateResult(
        gate=1,
        name="AUROC benchmark",
        passed=passed,
        value=f"{auroc:.4f}",
        threshold=">= 0.70",
        detail=f"Pipeline AUROC = {auroc:.4f} — {'PASS' if passed else 'FAIL'}",
    )


def check_gate_2_leakage(validation_data: dict[str, Any]) -> GateResult:
    """Benchmark has no near-duplicate contamination (soft check)."""
    recall_43 = validation_data.get("recall_at_43", 0.0)
    # A recall@43 of > 0.60 suggests possible reference-set memorisation
    passed = recall_43 < 0.60
    return GateResult(
        gate=2,
        name="Leakage guard",
        passed=passed,
        value=f"{recall_43:.3f}",
        threshold="Recall@43 < 0.60",
        detail=f"Recall@43 = {recall_43:.3f} — {'PASS (no evidence of memorisation)' if passed else f'WARNING: high recall ({recall_43:.3f}) suggests near-duplicate leakage'}",
    )


def check_gate_3_disagreement(validation_data: dict[str, Any]) -> GateResult:
    """Model disagreement within acceptable range."""
    top_ranked = validation_data.get("top_ranked", [])
    if not top_ranked:
        return GateResult(
            gate=3, name="Model disagreement",
            passed=True, value="N/A",
            threshold="Top candidate disagreement < 0.45",
            detail="No top-ranked data available — gate skipped",
        )
    # Check the top 3 candidates' disagreement scores
    high_disagreement = any(
        c.get("boman_activity", 0.0) is not None
        and abs(c.get("activity", 0.0) - c.get("boman_activity", 0.0)) > 0.45
        for c in top_ranked[:3]
    )
    passed = not high_disagreement
    return GateResult(
        gate=3,
        name="Model disagreement",
        passed=passed,
        value="< 0.45" if passed else "> 0.45 detected",
        threshold="Top-3 disagreement < 0.45",
        detail=f"{'PASS' if passed else 'FAIL: high disagreement in top-ranked candidates'}",
    )


def check_gate_4_top10_positive_recall(validation_data: dict[str, Any]) -> GateResult:
    """At least some positives in top 10."""
    recall_10 = validation_data.get("recall_at_10", 0.0)
    # Expected: at least 1 positive in top 10 for a 95-positive set = recall@10 >= 0.01
    passed = recall_10 > 0.0
    return GateResult(
        gate=4,
        name="Top-10 positive recall",
        passed=passed,
        value=f"{recall_10:.4f}",
        threshold="> 0.0",
        detail=f"Recall@10 = {recall_10:.4f} — {'PASS' if passed else 'FAIL: no positives in top 10'}",
    )


def check_gate_5_interpretation(validation_data: dict[str, Any]) -> GateResult:
    """Benchmark interpretation is STRONG."""
    interpretation = validation_data.get("interpretation", "")
    passed = "STRONG" in interpretation
    return GateResult(
        gate=5,
        name="Benchmark interpretation",
        passed=passed,
        value=interpretation,
        threshold="STRONG",
        detail=f"Interpretation: {interpretation}",
    )


def _gate_pending(gate: int, name: str, detail: str) -> GateResult:
    """Create a GateResult with passed=False for intentionally pending gates.
    
    Pending gates are NOT passed — they are unresolved and block synthesis
    readiness until completed. This prevents a false sense of readiness.
    """
    return GateResult(
        gate=gate, name=name, passed=False, value="PENDING",
        threshold="Must be resolved before synthesis",
        detail=f"{detail} (PENDING — does not pass until completed)",
    )


def _gate_6_pending(_val: Any) -> GateResult:
    return _gate_pending(
        6, "External predictor consensus",
        "Submit FASTA to CAMPR4, AMPScanner, dbAMP, AntiCP2, Macrel. "
        "See outputs/external_predict_checklist.md.",
    )


def _gate_7_pending(_val: Any) -> GateResult:
    return _gate_pending(
        7, "Human expert review",
        "Generate reviewer questionnaires via 'make questionnaire', distribute, "
        "and collect APPROVE/CONDITIONAL/REJECT verdicts.",
    )


_ALL_GATES = [
    check_gate_1_auroc,
    check_gate_2_leakage,
    check_gate_3_disagreement,
    check_gate_4_top10_positive_recall,
    check_gate_5_interpretation,
    _gate_6_pending,
    _gate_7_pending,
]


def check_all_gates(
    validation_data: dict[str, Any],
    specific_gate: int = 0,
) -> list[GateResult]:
    """Run all (or one specific) pipeline gates.

    Args:
        validation_data: Dict from validate_scoring_report.json.
        specific_gate: If > 0, run only that gate number. If 0, run all.

    Returns:
        List of GateResult namedtuples.
    """
    if specific_gate > 0:
        if specific_gate <= len(_ALL_GATES):
            return [_ALL_GATES[specific_gate - 1](validation_data)]
        return [GateResult(
            gate=specific_gate, name=f"Gate {specific_gate}",
            passed=False, value=None,
            threshold="N/A", detail=f"Gate {specific_gate} not implemented",
        )]
    return [gate_fn(validation_data) for gate_fn in _ALL_GATES]
