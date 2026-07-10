"""CBR- cheap baseline comparison record schema.

Structured record comparing the pipeline's performance metric against a
cheap baseline (charge-only, length-only, random) on the same candidate set.
Forces every performance claim to name the specific baseline it beat and
provide a machine-readable verdict. No performance claim is credible without
this record.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_CBR_VERDICTS: frozenset[str] = frozenset({
    "pipeline_superior",
    "tied",
    "baseline_superior",
    "insufficient_data",
})

VALID_BASELINE_METHODS: frozenset[str] = frozenset({
    "charge_only_rank",
    "length_only_rank",
    "random_selection",
    "charge_length_combined",
    "hydrophobicity_only_rank",
})

VALID_CBR_METRICS: frozenset[str] = frozenset({
    "auroc",
    "hit_rate",
    "top_k_precision",
    "ndcg",
})

SUPERIORITY_THRESHOLD: float = 0.05
INFERIORITY_THRESHOLD: float = -0.05
MIN_SAMPLE_SIZE: int = 5


@dataclass
class CheapBaselineComparisonRecord:
    cbr_id: str
    pipeline_version: str
    baseline_method: str
    metric_name: str
    pipeline_metric_value: float
    baseline_metric_value: float
    metric_delta: float
    n_candidates_evaluated: int
    pre_registered_threshold: float
    cbr_verdict: str
    comparison_notes: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_cheap_baseline_comparison_record(
    cbr: CheapBaselineComparisonRecord,
) -> None:
    if not cbr.cbr_id.startswith("CBR-"):
        raise ValueError(f"cbr_id must start with 'CBR-': {cbr.cbr_id!r}")
    if not cbr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if cbr.baseline_method not in VALID_BASELINE_METHODS:
        raise ValueError(
            f"baseline_method {cbr.baseline_method!r} not in VALID_BASELINE_METHODS"
        )
    if cbr.metric_name not in VALID_CBR_METRICS:
        raise ValueError(
            f"metric_name {cbr.metric_name!r} not in VALID_CBR_METRICS"
        )
    if not (0.0 <= cbr.pipeline_metric_value <= 1.0):
        raise ValueError(
            f"pipeline_metric_value must be in [0, 1]: {cbr.pipeline_metric_value}"
        )
    if not (0.0 <= cbr.baseline_metric_value <= 1.0):
        raise ValueError(
            f"baseline_metric_value must be in [0, 1]: {cbr.baseline_metric_value}"
        )
    expected_delta = round(cbr.pipeline_metric_value - cbr.baseline_metric_value, 6)
    if abs(cbr.metric_delta - expected_delta) > 1e-5:
        raise ValueError(
            f"metric_delta mismatch: expected {expected_delta}, got {cbr.metric_delta}"
        )
    if cbr.n_candidates_evaluated < 0:
        raise ValueError("n_candidates_evaluated must be non-negative")
    if cbr.cbr_verdict not in VALID_CBR_VERDICTS:
        raise ValueError(
            f"cbr_verdict {cbr.cbr_verdict!r} not in VALID_CBR_VERDICTS"
        )
    if not cbr.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not cbr.limitations:
        raise ValueError("limitations must be non-empty")
    if not cbr.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(
    delta: float,
    n_candidates: int,
    superiority_threshold: float,
) -> str:
    if n_candidates < MIN_SAMPLE_SIZE:
        return "insufficient_data"
    if delta >= superiority_threshold:
        return "pipeline_superior"
    if delta <= INFERIORITY_THRESHOLD:
        return "baseline_superior"
    return "tied"


def build_cheap_baseline_comparison_record(
    *,
    cbr_id: str,
    pipeline_version: str,
    baseline_method: str,
    metric_name: str,
    pipeline_metric_value: float,
    baseline_metric_value: float,
    n_candidates_evaluated: int,
    pre_registered_threshold: float = SUPERIORITY_THRESHOLD,
    comparison_notes: str = "",
    limitations: list[str],
    created_at: str,
) -> CheapBaselineComparisonRecord:
    """Build a CheapBaselineComparisonRecord.

    metric_delta = pipeline_metric_value - baseline_metric_value (auto-computed).
    cbr_verdict is auto-derived from delta vs pre_registered_threshold and n_candidates.
    """
    delta = round(pipeline_metric_value - baseline_metric_value, 6)
    verdict = _compute_verdict(delta, n_candidates_evaluated, pre_registered_threshold)
    cbr = CheapBaselineComparisonRecord(
        cbr_id=cbr_id,
        pipeline_version=pipeline_version,
        baseline_method=baseline_method,
        metric_name=metric_name,
        pipeline_metric_value=float(pipeline_metric_value),
        baseline_metric_value=float(baseline_metric_value),
        metric_delta=delta,
        n_candidates_evaluated=n_candidates_evaluated,
        pre_registered_threshold=float(pre_registered_threshold),
        cbr_verdict=verdict,
        comparison_notes=comparison_notes,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_cheap_baseline_comparison_record(cbr)
    return cbr


def format_cheap_baseline_comparison_record(
    cbr: CheapBaselineComparisonRecord,
) -> str:
    lines = [
        f"Cheap Baseline Comparison Record — {cbr.cbr_id}",
        f"Pipeline: {cbr.pipeline_version}",
        f"Baseline: {cbr.baseline_method}  |  Metric: {cbr.metric_name}",
        f"Verdict: {cbr.cbr_verdict}",
        f"Pipeline {cbr.metric_name}: {cbr.pipeline_metric_value:.4f}",
        f"Baseline {cbr.metric_name}: {cbr.baseline_metric_value:.4f}",
        f"Delta: {cbr.metric_delta:+.4f}  "
        f"(threshold: {cbr.pre_registered_threshold:+.4f})",
        f"Candidates evaluated: {cbr.n_candidates_evaluated}",
    ]
    if cbr.comparison_notes:
        lines.append(f"Notes: {cbr.comparison_notes}")
    lines.append(f"Created: {cbr.created_at}")
    lines.append(f"Limitations: {'; '.join(cbr.limitations)}")
    lines.append(f"dry_lab_only: {cbr.dry_lab_only}")
    return "\n".join(lines)
