"""SDA- selection diversity audit schema.

Tracks sequence diversity of selected candidate panel vs random draw from
the same pool. Detects proximity-driven selection masquerading as discovery.
Required before any novelty claim: if selected candidates cluster as tightly
as random, the selection is not adding diversity value.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_SDA_VERDICTS: frozenset[str] = frozenset({
    "diverse_panel",
    "moderately_diverse",
    "proximity_driven",
    "insufficient_data",
})

VALID_DIVERSITY_METRICS: frozenset[str] = frozenset({
    "mean_pairwise_identity",
    "mean_pairwise_distance",
    "clustering_coefficient",
    "effective_sequence_count",
})

DIVERSE_PANEL_THRESHOLD: float = 0.10
PROXIMITY_DRIVEN_THRESHOLD: float = -0.05
MIN_PANEL_SIZE: int = 3


@dataclass
class SelectionDiversityAudit:
    sda_id: str
    pipeline_version: str
    diversity_metric: str
    n_selected: int
    panel_diversity_score: float
    random_baseline_diversity_score: float
    diversity_delta: float
    sda_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_selection_diversity_audit(sda: SelectionDiversityAudit) -> None:
    if not sda.sda_id.startswith("SDA-"):
        raise ValueError(f"sda_id must start with 'SDA-': {sda.sda_id!r}")
    if not sda.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if sda.diversity_metric not in VALID_DIVERSITY_METRICS:
        raise ValueError(
            f"diversity_metric {sda.diversity_metric!r} not in VALID_DIVERSITY_METRICS"
        )
    if sda.n_selected < 0:
        raise ValueError("n_selected must be non-negative")
    expected_delta = round(
        sda.panel_diversity_score - sda.random_baseline_diversity_score, 6
    )
    if abs(sda.diversity_delta - expected_delta) > 1e-5:
        raise ValueError(
            f"diversity_delta mismatch: expected {expected_delta}, got {sda.diversity_delta}"
        )
    if sda.sda_verdict not in VALID_SDA_VERDICTS:
        raise ValueError(
            f"sda_verdict {sda.sda_verdict!r} not in VALID_SDA_VERDICTS"
        )
    if not sda.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not sda.limitations:
        raise ValueError("limitations must be non-empty")
    if not sda.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(
    n_selected: int,
    delta: float,
) -> str:
    if n_selected < MIN_PANEL_SIZE:
        return "insufficient_data"
    if delta >= DIVERSE_PANEL_THRESHOLD:
        return "diverse_panel"
    if delta <= PROXIMITY_DRIVEN_THRESHOLD:
        return "proximity_driven"
    return "moderately_diverse"


def build_selection_diversity_audit(
    *,
    sda_id: str,
    pipeline_version: str,
    diversity_metric: str,
    n_selected: int,
    panel_diversity_score: float,
    random_baseline_diversity_score: float,
    limitations: list[str],
    created_at: str,
) -> SelectionDiversityAudit:
    """Build a SelectionDiversityAudit.

    diversity_delta = panel_diversity_score - random_baseline_diversity_score (auto-computed).
    For mean_pairwise_distance: higher score = more diverse.
    For mean_pairwise_identity: lower score = more diverse (so delta>0 means less identity = more diversity).
    Verdict: diverse_panel (delta>=0.10), proximity_driven (delta<=-0.05), else moderately_diverse.
    """
    delta = round(panel_diversity_score - random_baseline_diversity_score, 6)
    verdict = _compute_verdict(n_selected, delta)
    sda = SelectionDiversityAudit(
        sda_id=sda_id,
        pipeline_version=pipeline_version,
        diversity_metric=diversity_metric,
        n_selected=n_selected,
        panel_diversity_score=float(panel_diversity_score),
        random_baseline_diversity_score=float(random_baseline_diversity_score),
        diversity_delta=delta,
        sda_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_selection_diversity_audit(sda)
    return sda


def format_selection_diversity_audit(sda: SelectionDiversityAudit) -> str:
    lines = [
        f"Selection Diversity Audit — {sda.sda_id}",
        f"Pipeline: {sda.pipeline_version}",
        f"Metric: {sda.diversity_metric}  |  Verdict: {sda.sda_verdict}",
        f"Panel diversity: {sda.panel_diversity_score:.4f}",
        f"Random baseline diversity: {sda.random_baseline_diversity_score:.4f}",
        f"Delta: {sda.diversity_delta:+.4f}  "
        f"(diverse>=+{DIVERSE_PANEL_THRESHOLD}, "
        f"proximity<={PROXIMITY_DRIVEN_THRESHOLD})",
        f"Candidates selected: {sda.n_selected}",
        f"Created: {sda.created_at}",
        f"Limitations: {'; '.join(sda.limitations)}",
        f"dry_lab_only: {sda.dry_lab_only}",
    ]
    return "\n".join(lines)
