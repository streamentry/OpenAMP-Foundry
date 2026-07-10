"""CMC- charge-matched challenge schema.

Documents the charge-matched challenge run for a batch: compares pipeline
AUROC versus a charge-only baseline on the same candidate set with the same
charge distribution. A meaningful gap is required to claim the pipeline adds
value beyond simply preferring cationic sequences.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_CMC_VERDICTS: frozenset[str] = frozenset({
    "gap_meaningful",
    "gap_marginal",
    "gap_absent",
    "challenge_not_run",
})

VALID_CHARGE_BASELINE_METHODS: frozenset[str] = frozenset({
    "charge_only_rank",
    "charge_length_rank",
    "charge_hydrophobicity_rank",
    "logistic_charge_only",
})

MEANINGFUL_GAP_THRESHOLD: float = 0.05
MARGINAL_GAP_LOWER: float = 0.02

MIN_AUROC: float = 0.0
MAX_AUROC: float = 1.0


@dataclass
class ChargeMatchedChallenge:
    cmc_id: str
    batch_id: str
    pipeline_version: str
    baseline_method: str
    pipeline_auroc: float
    baseline_auroc: float
    auroc_gap: float
    n_candidates: int
    mean_charge_pipeline: float
    mean_charge_baseline: float
    charge_distribution_matched: bool
    cmc_verdict: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def validate_charge_matched_challenge(cmc: ChargeMatchedChallenge) -> None:
    if not cmc.cmc_id.startswith("CMC-"):
        raise ValueError(f"cmc_id must start with 'CMC-': {cmc.cmc_id!r}")
    if not cmc.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not cmc.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if cmc.baseline_method not in VALID_CHARGE_BASELINE_METHODS:
        raise ValueError(
            f"baseline_method {cmc.baseline_method!r} not in VALID_CHARGE_BASELINE_METHODS"
        )
    if not (MIN_AUROC <= cmc.pipeline_auroc <= MAX_AUROC):
        raise ValueError(
            f"pipeline_auroc must be in [0, 1]: {cmc.pipeline_auroc}"
        )
    if not (MIN_AUROC <= cmc.baseline_auroc <= MAX_AUROC):
        raise ValueError(
            f"baseline_auroc must be in [0, 1]: {cmc.baseline_auroc}"
        )
    expected_gap = round(cmc.pipeline_auroc - cmc.baseline_auroc, 6)
    if abs(cmc.auroc_gap - expected_gap) > 1e-4:
        raise ValueError(
            f"auroc_gap {cmc.auroc_gap} does not match computed "
            f"{expected_gap} (pipeline_auroc - baseline_auroc)"
        )
    if cmc.n_candidates < 0:
        raise ValueError("n_candidates must be non-negative")
    if cmc.cmc_verdict not in VALID_CMC_VERDICTS:
        raise ValueError(
            f"cmc_verdict {cmc.cmc_verdict!r} not in VALID_CMC_VERDICTS"
        )
    if not cmc.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not cmc.limitations:
        raise ValueError("limitations must be non-empty")
    if not cmc.created_at:
        raise ValueError("created_at must be non-empty")


def _compute_verdict(n_candidates: int, auroc_gap: float) -> str:
    if n_candidates == 0:
        return "challenge_not_run"
    if auroc_gap >= MEANINGFUL_GAP_THRESHOLD:
        return "gap_meaningful"
    if auroc_gap >= MARGINAL_GAP_LOWER:
        return "gap_marginal"
    return "gap_absent"


def build_charge_matched_challenge(
    *,
    cmc_id: str,
    batch_id: str,
    pipeline_version: str,
    baseline_method: str,
    pipeline_auroc: float,
    baseline_auroc: float,
    n_candidates: int,
    mean_charge_pipeline: float,
    mean_charge_baseline: float,
    charge_distribution_matched: bool,
    limitations: list[str],
    created_at: str,
) -> ChargeMatchedChallenge:
    auroc_gap = round(pipeline_auroc - baseline_auroc, 6)
    verdict = _compute_verdict(n_candidates, auroc_gap)
    cmc = ChargeMatchedChallenge(
        cmc_id=cmc_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        baseline_method=baseline_method,
        pipeline_auroc=pipeline_auroc,
        baseline_auroc=baseline_auroc,
        auroc_gap=auroc_gap,
        n_candidates=n_candidates,
        mean_charge_pipeline=mean_charge_pipeline,
        mean_charge_baseline=mean_charge_baseline,
        charge_distribution_matched=charge_distribution_matched,
        cmc_verdict=verdict,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_charge_matched_challenge(cmc)
    return cmc


def format_charge_matched_challenge(cmc: ChargeMatchedChallenge) -> str:
    lines = [
        f"Charge-Matched Challenge — {cmc.cmc_id}",
        f"Batch: {cmc.batch_id}  |  Pipeline: {cmc.pipeline_version}",
        f"Baseline method: {cmc.baseline_method}",
        f"Verdict: {cmc.cmc_verdict}",
        f"Pipeline AUROC: {cmc.pipeline_auroc:.4f}  |  Baseline AUROC: {cmc.baseline_auroc:.4f}  |  Gap: {cmc.auroc_gap:+.4f}",
        f"N candidates: {cmc.n_candidates}",
        f"Mean charge — pipeline: {cmc.mean_charge_pipeline:.2f}  |  baseline: {cmc.mean_charge_baseline:.2f}",
        f"Charge distribution matched: {cmc.charge_distribution_matched}",
        f"Created: {cmc.created_at}",
        f"Limitations: {'; '.join(cmc.limitations)}",
        f"dry_lab_only: {cmc.dry_lab_only}",
    ]
    return "\n".join(lines)
