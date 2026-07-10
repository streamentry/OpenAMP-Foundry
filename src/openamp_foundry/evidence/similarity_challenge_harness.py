"""SCH- similarity challenge harness schema.

Documents whether pipeline-selected candidates are systematically more similar
to known AMPs than a random draw from the same sequence space. Flags selection
bias from proximity clustering: if the pipeline is essentially selecting
near-neighbors of known AMPs rather than exploring new space, novelty claims
are not credible.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_SCH_VERDICTS: frozenset[str] = frozenset({
    "selection_adds_value",
    "marginal_improvement",
    "proximity_driven",
    "challenge_not_run",
})

VALID_SIMILARITY_METRICS: frozenset[str] = frozenset({
    "sequence_identity",
    "blosum62_score",
    "edit_distance",
    "physicochemical_distance",
})

SELECTION_VALUE_GAP_THRESHOLD: float = 0.10
MARGINAL_IMPROVEMENT_LOWER: float = 0.03


@dataclass
class SimilarityGroupStats:
    group_label: str
    mean_similarity_to_known: float
    n_sequences: int


@dataclass
class SimilarityChallengeHarness:
    sch_id: str
    batch_id: str
    pipeline_version: str
    similarity_metric: str
    pipeline_group: SimilarityGroupStats
    random_group: SimilarityGroupStats
    similarity_gap: float
    sch_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_similarity_challenge_harness(sch: SimilarityChallengeHarness) -> None:
    if not sch.sch_id.startswith("SCH-"):
        raise ValueError(f"sch_id must start with 'SCH-': {sch.sch_id!r}")
    if not sch.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not sch.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if sch.similarity_metric not in VALID_SIMILARITY_METRICS:
        raise ValueError(
            f"similarity_metric {sch.similarity_metric!r} not in VALID_SIMILARITY_METRICS"
        )
    for group in (sch.pipeline_group, sch.random_group):
        if not (0.0 <= group.mean_similarity_to_known <= 1.0):
            raise ValueError(
                f"mean_similarity_to_known must be in [0, 1]: {group.mean_similarity_to_known}"
            )
        if group.n_sequences < 0:
            raise ValueError(
                f"n_sequences must be non-negative: {group.n_sequences}"
            )
    expected_gap = round(
        sch.pipeline_group.mean_similarity_to_known
        - sch.random_group.mean_similarity_to_known,
        6,
    )
    if abs(sch.similarity_gap - expected_gap) > 1e-4:
        raise ValueError(
            f"similarity_gap {sch.similarity_gap} does not match computed "
            f"{expected_gap}"
        )
    if sch.sch_verdict not in VALID_SCH_VERDICTS:
        raise ValueError(
            f"sch_verdict {sch.sch_verdict!r} not in VALID_SCH_VERDICTS"
        )
    if not sch.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not sch.limitations:
        raise ValueError("limitations must be non-empty")
    if not sch.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(
    n_pipeline: int,
    n_random: int,
    similarity_gap: float,
) -> str:
    if n_pipeline == 0 or n_random == 0:
        return "challenge_not_run"
    if similarity_gap >= SELECTION_VALUE_GAP_THRESHOLD:
        return "selection_adds_value"
    if similarity_gap >= MARGINAL_IMPROVEMENT_LOWER:
        return "marginal_improvement"
    return "proximity_driven"


def build_similarity_challenge_harness(
    *,
    sch_id: str,
    batch_id: str,
    pipeline_version: str,
    similarity_metric: str,
    pipeline_mean_similarity: float,
    pipeline_n_sequences: int,
    random_mean_similarity: float,
    random_n_sequences: int,
    limitations: list[str],
    created_at: str,
) -> SimilarityChallengeHarness:
    pipeline_group = SimilarityGroupStats(
        group_label="pipeline_selected",
        mean_similarity_to_known=pipeline_mean_similarity,
        n_sequences=pipeline_n_sequences,
    )
    random_group = SimilarityGroupStats(
        group_label="random_draw",
        mean_similarity_to_known=random_mean_similarity,
        n_sequences=random_n_sequences,
    )
    gap = round(pipeline_mean_similarity - random_mean_similarity, 6)
    verdict = _compute_verdict(pipeline_n_sequences, random_n_sequences, gap)
    sch = SimilarityChallengeHarness(
        sch_id=sch_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        similarity_metric=similarity_metric,
        pipeline_group=pipeline_group,
        random_group=random_group,
        similarity_gap=gap,
        sch_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_similarity_challenge_harness(sch)
    return sch


def format_similarity_challenge_harness(sch: SimilarityChallengeHarness) -> str:
    lines = [
        f"Similarity Challenge Harness — {sch.sch_id}",
        f"Batch: {sch.batch_id}  |  Pipeline: {sch.pipeline_version}",
        f"Similarity metric: {sch.similarity_metric}",
        f"Verdict: {sch.sch_verdict}",
        f"Pipeline selected: mean={sch.pipeline_group.mean_similarity_to_known:.4f}  "
        f"(n={sch.pipeline_group.n_sequences})",
        f"Random draw:       mean={sch.random_group.mean_similarity_to_known:.4f}  "
        f"(n={sch.random_group.n_sequences})",
        f"Gap (pipeline - random): {sch.similarity_gap:+.4f}",
        f"Created: {sch.created_at}",
        f"Limitations: {'; '.join(sch.limitations)}",
        f"dry_lab_only: {sch.dry_lab_only}",
    ]
    return "\n".join(lines)
