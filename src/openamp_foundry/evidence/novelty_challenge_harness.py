"""NCH- novelty challenge harness schema.

Batch-level novelty challenge record: documents what fraction of top
candidates have high sequence identity (≥ threshold) to known AMPs in a
reference database. Blocks 'novel family' claims at the batch level when
the near-neighbor fraction is above the allowed ceiling.

This schema operates at batch level; per-family novelty is captured in
the FNR- (family novelty report) schema. NCH- provides the aggregate
machine-verifiable gate.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_NCH_VERDICTS: frozenset[str] = frozenset({
    "novel_batch",
    "mixed_novelty",
    "near_neighbor_dominated",
    "challenge_not_run",
})

VALID_REFERENCE_DATABASES: frozenset[str] = frozenset({
    "APD3",
    "DRAMP",
    "DBAASP",
    "CAMP",
    "LAMP",
    "custom",
})

NEAR_NEIGHBOR_IDENTITY_THRESHOLD: float = 0.80
NOVEL_BATCH_CEILING: float = 0.20
NEAR_NEIGHBOR_DOMINATED_FLOOR: float = 0.60


@dataclass
class NCHCandidateResult:
    candidate_id: str
    max_identity_to_known: float
    is_near_neighbor: bool
    closest_known_amp_id: str


@dataclass
class NoveltyChallengeHarness:
    nch_id: str
    batch_id: str
    pipeline_version: str
    reference_database: str
    identity_threshold: float
    n_candidates_checked: int
    n_near_neighbors: int
    near_neighbor_fraction: float
    candidate_results: list[NCHCandidateResult]
    nch_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_novelty_challenge_harness(nch: NoveltyChallengeHarness) -> None:
    if not nch.nch_id.startswith("NCH-"):
        raise ValueError(f"nch_id must start with 'NCH-': {nch.nch_id!r}")
    if not nch.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not nch.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if nch.reference_database not in VALID_REFERENCE_DATABASES:
        raise ValueError(
            f"reference_database {nch.reference_database!r} not in VALID_REFERENCE_DATABASES"
        )
    if not (0.0 < nch.identity_threshold <= 1.0):
        raise ValueError(
            f"identity_threshold must be in (0, 1]: {nch.identity_threshold}"
        )
    if nch.n_candidates_checked < 0:
        raise ValueError("n_candidates_checked must be non-negative")
    if nch.n_near_neighbors < 0:
        raise ValueError("n_near_neighbors must be non-negative")
    if nch.n_near_neighbors > nch.n_candidates_checked:
        raise ValueError("n_near_neighbors cannot exceed n_candidates_checked")
    for cr in nch.candidate_results:
        if not (0.0 <= cr.max_identity_to_known <= 1.0):
            raise ValueError(
                f"max_identity_to_known must be in [0, 1]: {cr.max_identity_to_known}"
            )
        expected_nn = cr.max_identity_to_known >= nch.identity_threshold
        if cr.is_near_neighbor != expected_nn:
            raise ValueError(
                f"is_near_neighbor mismatch for {cr.candidate_id!r}: "
                f"identity={cr.max_identity_to_known}, threshold={nch.identity_threshold}"
            )
    if nch.n_candidates_checked != len(nch.candidate_results):
        raise ValueError("n_candidates_checked must equal len(candidate_results)")
    expected_nn_count = sum(1 for cr in nch.candidate_results if cr.is_near_neighbor)
    if nch.n_near_neighbors != expected_nn_count:
        raise ValueError("n_near_neighbors mismatch")
    if nch.n_candidates_checked == 0:
        expected_fraction = 0.0
    else:
        expected_fraction = round(
            nch.n_near_neighbors / nch.n_candidates_checked, 6
        )
    if abs(nch.near_neighbor_fraction - expected_fraction) > 1e-4:
        raise ValueError(
            f"near_neighbor_fraction {nch.near_neighbor_fraction} does not match "
            f"computed {expected_fraction}"
        )
    if nch.nch_verdict not in VALID_NCH_VERDICTS:
        raise ValueError(
            f"nch_verdict {nch.nch_verdict!r} not in VALID_NCH_VERDICTS"
        )
    if not nch.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not nch.limitations:
        raise ValueError("limitations must be non-empty")
    if not nch.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(
    n_candidates: int,
    near_neighbor_fraction: float,
) -> str:
    if n_candidates == 0:
        return "challenge_not_run"
    if near_neighbor_fraction <= NOVEL_BATCH_CEILING:
        return "novel_batch"
    if near_neighbor_fraction >= NEAR_NEIGHBOR_DOMINATED_FLOOR:
        return "near_neighbor_dominated"
    return "mixed_novelty"


def build_novelty_challenge_harness(
    *,
    nch_id: str,
    batch_id: str,
    pipeline_version: str,
    reference_database: str,
    identity_threshold: float = NEAR_NEIGHBOR_IDENTITY_THRESHOLD,
    candidate_result_dicts: list[dict],
    limitations: list[str],
    created_at: str,
) -> NoveltyChallengeHarness:
    """Build a NoveltyChallengeHarness.

    candidate_result_dicts: list of dicts with keys:
        candidate_id (str), max_identity_to_known (float),
        closest_known_amp_id (str, optional, default "")
    """
    candidate_results = []
    for d in candidate_result_dicts:
        identity = float(d["max_identity_to_known"])
        is_nn = identity >= identity_threshold
        candidate_results.append(
            NCHCandidateResult(
                candidate_id=d["candidate_id"],
                max_identity_to_known=identity,
                is_near_neighbor=is_nn,
                closest_known_amp_id=d.get("closest_known_amp_id", ""),
            )
        )
    n = len(candidate_results)
    n_nn = sum(1 for cr in candidate_results if cr.is_near_neighbor)
    fraction = round(n_nn / n, 6) if n > 0 else 0.0
    verdict = _compute_verdict(n, fraction)
    nch = NoveltyChallengeHarness(
        nch_id=nch_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        reference_database=reference_database,
        identity_threshold=identity_threshold,
        n_candidates_checked=n,
        n_near_neighbors=n_nn,
        near_neighbor_fraction=fraction,
        candidate_results=candidate_results,
        nch_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_novelty_challenge_harness(nch)
    return nch


def format_novelty_challenge_harness(nch: NoveltyChallengeHarness) -> str:
    lines = [
        f"Novelty Challenge Harness — {nch.nch_id}",
        f"Batch: {nch.batch_id}  |  Pipeline: {nch.pipeline_version}",
        f"Reference DB: {nch.reference_database}  |  Identity threshold: {nch.identity_threshold:.0%}",
        f"Verdict: {nch.nch_verdict}",
        f"Near-neighbors: {nch.n_near_neighbors}/{nch.n_candidates_checked} "
        f"({nch.near_neighbor_fraction:.1%})",
    ]
    if nch.candidate_results:
        lines.append("Top candidates:")
        for cr in nch.candidate_results[:5]:
            nn_label = "NEAR-NEIGHBOR" if cr.is_near_neighbor else "novel"
            lines.append(
                f"  {cr.candidate_id}: {cr.max_identity_to_known:.1%} identity  [{nn_label}]"
            )
        if len(nch.candidate_results) > 5:
            lines.append(f"  ... ({len(nch.candidate_results) - 5} more)")
    lines.append(f"Created: {nch.created_at}")
    lines.append(f"Limitations: {'; '.join(nch.limitations)}")
    lines.append(f"dry_lab_only: {nch.dry_lab_only}")
    return "\n".join(lines)
