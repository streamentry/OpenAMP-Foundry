"""CBF- cheap baseline flag schema.

Per-scorer gate ensuring every external adapter declares its cheapest
meaningful baseline before influencing candidate ranking. Blocks ranking
when baseline is missing or AUROC delta < 0.05.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_CBF_VERDICTS: frozenset[str] = frozenset({
    "baseline_declared",
    "baseline_missing",
    "baseline_insufficient",
})

VALID_CBF_BASELINE_TYPES: frozenset[str] = frozenset({
    "charge_only_rank",
    "length_only_rank",
    "random_selection",
    "charge_length_combined",
    "hydrophobicity_only_rank",
    "sequence_identity_to_known",
})

VALID_CBF_SCORER_CLASSES: frozenset[str] = frozenset({
    "sequence_scorer",
    "structure_predictor",
    "toxicity_filter",
    "novelty_ranker",
    "simulation_runner",
    "embedding_provider",
})

MINIMUM_MEANINGFUL_DELTA: float = 0.05

BLOCKS_RANKING: bool = True


def _compute_verdict(
    baseline_type: str,
    baseline_auroc: float,
    scorer_auroc: float,
    auroc_delta: float,
) -> str:
    if baseline_type == "" or baseline_auroc == -1.0 or scorer_auroc == -1.0:
        return "baseline_missing"
    if auroc_delta >= MINIMUM_MEANINGFUL_DELTA:
        return "baseline_declared"
    return "baseline_insufficient"


def _compute_auroc_delta(
    baseline_auroc: float, scorer_auroc: float
) -> float:
    if baseline_auroc == -1.0 or scorer_auroc == -1.0:
        return 0.0
    return scorer_auroc - baseline_auroc


def _compute_delta_is_meaningful(auroc_delta: float) -> bool:
    return auroc_delta >= MINIMUM_MEANINGFUL_DELTA


def _compute_blocks_ranking(verdict: str) -> bool:
    return verdict in ("baseline_missing", "baseline_insufficient")


@dataclass
class CheapBaselineFlag:
    cbf_id: str
    scorer_id: str
    scorer_class: str
    pipeline_version: str
    baseline_type: str
    baseline_auroc: float
    scorer_auroc: float
    auroc_delta: float
    delta_is_meaningful: bool
    verdict: str
    blocks_ranking: bool
    cbr_ref: str
    limitations: list[str]
    created_at: str
    dry_lab_only: bool = True


def validate_cheap_baseline_flag(cbf: CheapBaselineFlag) -> None:
    if not cbf.cbf_id.startswith("CBF-"):
        raise ValueError(
            f"cbf_id must start with 'CBF-': {cbf.cbf_id!r}"
        )
    if not cbf.scorer_id:
        raise ValueError("scorer_id must be non-empty")
    if cbf.scorer_class not in VALID_CBF_SCORER_CLASSES:
        raise ValueError(
            f"scorer_class {cbf.scorer_class!r} not in "
            f"VALID_CBF_SCORER_CLASSES"
        )
    if not cbf.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if cbf.baseline_type != "":
        if cbf.baseline_type not in VALID_CBF_BASELINE_TYPES:
            raise ValueError(
                f"baseline_type {cbf.baseline_type!r} not in "
                f"VALID_CBF_BASELINE_TYPES"
            )
    if not (-1.0 <= cbf.baseline_auroc <= 1.0):
        raise ValueError(
            f"baseline_auroc must be in [-1.0, 1.0]: {cbf.baseline_auroc}"
        )
    if not (-1.0 <= cbf.scorer_auroc <= 1.0):
        raise ValueError(
            f"scorer_auroc must be in [-1.0, 1.0]: {cbf.scorer_auroc}"
        )
    if cbf.baseline_auroc != -1.0 and cbf.scorer_auroc != -1.0:
        expected_delta = cbf.scorer_auroc - cbf.baseline_auroc
        if abs(cbf.auroc_delta - expected_delta) > 0.001:
            raise ValueError(
                f"auroc_delta mismatch: got {cbf.auroc_delta}, "
                f"expected {expected_delta}"
            )
    else:
        if cbf.auroc_delta != 0.0:
            raise ValueError(
                f"auroc_delta must be 0.0 when either auroc is -1.0: "
                f"got {cbf.auroc_delta}"
            )
    expected_meaningful = _compute_delta_is_meaningful(cbf.auroc_delta)
    if cbf.delta_is_meaningful != expected_meaningful:
        raise ValueError(
            f"delta_is_meaningful mismatch: got {cbf.delta_is_meaningful}, "
            f"expected {expected_meaningful}"
        )
    expected_verdict = _compute_verdict(
        cbf.baseline_type,
        cbf.baseline_auroc,
        cbf.scorer_auroc,
        cbf.auroc_delta,
    )
    if cbf.verdict != expected_verdict:
        raise ValueError(
            f"verdict mismatch: got {cbf.verdict!r}, "
            f"expected {expected_verdict!r}"
        )
    expected_blocks = _compute_blocks_ranking(cbf.verdict)
    if cbf.blocks_ranking != expected_blocks:
        raise ValueError(
            f"blocks_ranking mismatch: got {cbf.blocks_ranking}, "
            f"expected {expected_blocks}"
        )
    if cbf.verdict == "baseline_declared" and cbf.cbr_ref != "":
        if not cbf.cbr_ref.startswith("CBR-") and not cbf.cbr_ref.startswith("SEG-"):
            raise ValueError(
                f"cbr_ref for baseline_declared verdict must start "
                f"with CBR- or SEG-: {cbf.cbr_ref!r}"
            )
    if not cbf.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not cbf.limitations:
        raise ValueError("limitations must be non-empty")
    if not cbf.created_at:
        raise ValueError("created_at must be non-empty")


def build_cheap_baseline_flag(
    *,
    cbf_id: str,
    scorer_id: str,
    scorer_class: str,
    pipeline_version: str,
    baseline_type: str = "",
    baseline_auroc: float = -1.0,
    scorer_auroc: float = -1.0,
    cbr_ref: str = "",
    limitations: list[str],
    created_at: str,
) -> CheapBaselineFlag:
    auroc_delta = _compute_auroc_delta(baseline_auroc, scorer_auroc)
    delta_is_meaningful = _compute_delta_is_meaningful(auroc_delta)
    verdict = _compute_verdict(
        baseline_type, baseline_auroc, scorer_auroc, auroc_delta
    )
    blocks_ranking = _compute_blocks_ranking(verdict)

    cbf = CheapBaselineFlag(
        cbf_id=cbf_id,
        scorer_id=scorer_id,
        scorer_class=scorer_class,
        pipeline_version=pipeline_version,
        baseline_type=baseline_type,
        baseline_auroc=baseline_auroc,
        scorer_auroc=scorer_auroc,
        auroc_delta=auroc_delta,
        delta_is_meaningful=delta_is_meaningful,
        verdict=verdict,
        blocks_ranking=blocks_ranking,
        cbr_ref=cbr_ref,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_cheap_baseline_flag(cbf)
    return cbf


def format_cheap_baseline_flag(cbf: CheapBaselineFlag) -> str:
    lines = [
        f"Cheap Baseline Flag — {cbf.cbf_id}",
        f"Scorer: {cbf.scorer_id} ({cbf.scorer_class})",
        f"Pipeline: {cbf.pipeline_version}",
    ]
    if cbf.baseline_type:
        lines.append(f"Baseline type: {cbf.baseline_type}")
    else:
        lines.append("Baseline type: (none — not declared)")
    if cbf.baseline_auroc != -1.0 and cbf.scorer_auroc != -1.0:
        lines.append(
            f"Baseline AUROC: {cbf.baseline_auroc:.3f}, "
            f"Scorer AUROC: {cbf.scorer_auroc:.3f}, "
            f"Delta: {cbf.auroc_delta:+.3f}"
        )
    else:
        lines.append("AUROC: not evaluated")
    lines.append(f"Delta meaningful: {cbf.delta_is_meaningful}")
    lines.append(f"Verdict: {cbf.verdict}")
    lines.append(f"Blocks ranking: {cbf.blocks_ranking}")
    if cbf.cbr_ref:
        lines.append(f"Supporting record: {cbf.cbr_ref}")
    if cbf.limitations:
        lines.append(f"Limitations: {'; '.join(cbf.limitations)}")
    lines.append(f"Created: {cbf.created_at}")
    lines.append(f"dry_lab_only: {cbf.dry_lab_only}")
    return "\n".join(lines)
