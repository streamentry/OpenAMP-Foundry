"""DCR- Determinism check record schema.

Records the result of running the same pipeline step twice and comparing
outputs. A pipeline step is not trustworthy for external review until it
passes a determinism check.
Verdict: deterministic / nondeterministic / single_run_only / seed_dependent.
"""

from __future__ import annotations

from dataclasses import dataclass

VALID_DCR_VERDICTS: frozenset[str] = frozenset({
    "deterministic",
    "nondeterministic",
    "single_run_only",
    "seed_dependent",
})

VALID_DCR_STEP_TYPES: frozenset[str] = frozenset({
    "scoring",
    "ranking",
    "embedding",
    "filtering",
    "clustering",
    "selection",
    "evidence_generation",
})

VALID_DCR_COMPARISON_METHODS: frozenset[str] = frozenset({
    "exact_match",
    "rank_correlation",
    "score_delta",
    "set_equality",
})


@dataclass
class DeterminismCheckRecord:
    dcr_id: str
    pipeline_version: str
    step_type: str
    step_id: str
    random_seed: str
    run1_output_hash: str
    run2_output_hash: str
    comparison_method: str
    outputs_match: bool
    verdict: str
    similarity_score: float
    n_runs: int
    limitations: list[str]
    created_at: str
    dry_lab_only: bool = True


def _compute_outputs_match(
    n_runs: int,
    run2_output_hash: str,
    run1_output_hash: str,
) -> bool:
    return (
        n_runs >= 2
        and run2_output_hash != ""
        and run1_output_hash == run2_output_hash
    )


def _compute_verdict(
    n_runs: int,
    run2_output_hash: str,
    run1_output_hash: str,
    outputs_match: bool,
    override_verdict: str | None = None,
) -> str:
    if override_verdict is not None and override_verdict in VALID_DCR_VERDICTS:
        return override_verdict
    if n_runs == 1 or run2_output_hash == "":
        return "single_run_only"
    if outputs_match:
        return "deterministic"
    return "nondeterministic"


def build_determinism_check_record(
    *,
    dcr_id: str,
    pipeline_version: str,
    step_type: str,
    step_id: str,
    random_seed: str,
    run1_output_hash: str,
    run2_output_hash: str = "",
    comparison_method: str,
    n_runs: int,
    similarity_score: float,
    limitations: list[str],
    created_at: str,
    verdict: str | None = None,
) -> DeterminismCheckRecord:
    outputs_match = _compute_outputs_match(n_runs, run2_output_hash, run1_output_hash)
    computed_verdict = _compute_verdict(
        n_runs, run2_output_hash, run1_output_hash, outputs_match, override_verdict=verdict
    )
    dcr = DeterminismCheckRecord(
        dcr_id=dcr_id,
        pipeline_version=pipeline_version,
        step_type=step_type,
        step_id=step_id,
        random_seed=random_seed,
        run1_output_hash=run1_output_hash,
        run2_output_hash=run2_output_hash,
        comparison_method=comparison_method,
        outputs_match=outputs_match,
        verdict=computed_verdict,
        similarity_score=similarity_score,
        n_runs=n_runs,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_determinism_check_record(dcr)
    return dcr


def validate_determinism_check_record(dcr: DeterminismCheckRecord) -> None:
    if not dcr.dcr_id.startswith("DCR-"):
        raise ValueError(f"dcr_id must start with 'DCR-': {dcr.dcr_id!r}")
    if not dcr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    if dcr.step_type not in VALID_DCR_STEP_TYPES:
        raise ValueError(
            f"step_type {dcr.step_type!r} not in VALID_DCR_STEP_TYPES"
        )
    if not dcr.step_id:
        raise ValueError("step_id must be non-empty")
    if not dcr.random_seed:
        raise ValueError("random_seed must be non-empty")
    if not dcr.run1_output_hash:
        raise ValueError("run1_output_hash must be non-empty")
    if dcr.comparison_method not in VALID_DCR_COMPARISON_METHODS:
        raise ValueError(
            f"comparison_method {dcr.comparison_method!r} not in "
            f"VALID_DCR_COMPARISON_METHODS"
        )
    if dcr.n_runs not in (1, 2):
        raise ValueError(f"n_runs must be 1 or 2, got {dcr.n_runs}")
    if dcr.n_runs == 2 and not dcr.run2_output_hash:
        raise ValueError("n_runs=2 requires non-empty run2_output_hash")
    if dcr.n_runs == 1 and dcr.run2_output_hash != "":
        raise ValueError("n_runs=1 requires run2_output_hash to be empty")
    expected_outputs_match = _compute_outputs_match(
        dcr.n_runs, dcr.run2_output_hash, dcr.run1_output_hash
    )
    if dcr.outputs_match != expected_outputs_match:
        raise ValueError(
            f"outputs_match {dcr.outputs_match} inconsistent with "
            f"n_runs={dcr.n_runs}, run1={dcr.run1_output_hash!r}, "
            f"run2={dcr.run2_output_hash!r}"
        )
    if dcr.verdict not in VALID_DCR_VERDICTS:
        raise ValueError(f"verdict {dcr.verdict!r} not in VALID_DCR_VERDICTS")
    if dcr.verdict == "single_run_only" and dcr.n_runs != 1:
        raise ValueError(
            "verdict single_run_only requires n_runs=1"
        )
    if dcr.verdict == "deterministic" and not dcr.outputs_match:
        raise ValueError(
            "verdict deterministic requires outputs_match=True"
        )
    if dcr.verdict == "nondeterministic" and dcr.outputs_match:
        raise ValueError(
            "verdict nondeterministic requires outputs_match=False"
        )
    if dcr.verdict == "seed_dependent":
        if dcr.n_runs != 2:
            raise ValueError("seed_dependent verdict requires n_runs=2")
        if not dcr.run2_output_hash:
            raise ValueError("seed_dependent verdict requires non-empty run2_output_hash")
    if not (-1.0 <= dcr.similarity_score <= 1.0):
        raise ValueError(
            f"similarity_score must be in [-1.0, 1.0], got {dcr.similarity_score}"
        )
    if not dcr.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not dcr.limitations:
        raise ValueError("limitations must be non-empty")
    if not dcr.created_at:
        raise ValueError("created_at must be non-empty")


def format_determinism_check_record(dcr: DeterminismCheckRecord) -> str:
    lines = [
        f"Determinism Check Record — {dcr.dcr_id}",
        f"Pipeline: {dcr.pipeline_version}",
        f"Step: {dcr.step_type} / {dcr.step_id}",
        f"Seed: {dcr.random_seed}",
        f"Comparison: {dcr.comparison_method}",
        f"Runs: {dcr.n_runs}",
        f"Outputs match: {dcr.outputs_match}",
        f"Run 1 hash: {dcr.run1_output_hash}",
    ]
    if dcr.n_runs == 2 and dcr.run2_output_hash:
        lines.append(f"Run 2 hash: {dcr.run2_output_hash}")
    lines.append(f"Similarity: {dcr.similarity_score}")
    lines.append(f"Verdict: {dcr.verdict}")
    if dcr.limitations:
        lines.append(f"Limitations: {'; '.join(dcr.limitations)}")
    lines.append(f"Created: {dcr.created_at}")
    lines.append(f"dry_lab_only: {dcr.dry_lab_only}")
    return "\n".join(lines)
