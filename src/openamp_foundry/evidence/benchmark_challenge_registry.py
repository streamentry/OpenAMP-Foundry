"""BCR- benchmark challenge registry schema.

Machine-readable registry of which benchmark challenges (NCH, CMC, SCH) have
been run and passed for a given pipeline version and batch. Aggregates the
per-challenge verdicts into an overall hardness grade. No batch-level
performance claim is credible without a passing BCR- registry entry.
"""

from __future__ import annotations

from dataclasses import dataclass

REQUIRED_CHALLENGE_TYPES: tuple[str, ...] = ("NCH", "CMC", "SCH")

VALID_CHALLENGE_VERDICTS: frozenset[str] = frozenset({
    "pass",
    "marginal",
    "fail",
    "not_run",
})

VALID_BCR_HARDNESS_GRADES: frozenset[str] = frozenset({
    "A",
    "B",
    "C",
    "D",
})

_PASSING_NCH_VERDICTS: frozenset[str] = frozenset({
    "novel_batch",
})
_MARGINAL_NCH_VERDICTS: frozenset[str] = frozenset({
    "mixed_novelty",
})

_PASSING_CMC_VERDICTS: frozenset[str] = frozenset({
    "gap_meaningful",
})
_MARGINAL_CMC_VERDICTS: frozenset[str] = frozenset({
    "gap_marginal",
})

_PASSING_SCH_VERDICTS: frozenset[str] = frozenset({
    "selection_adds_value",
})
_MARGINAL_SCH_VERDICTS: frozenset[str] = frozenset({
    "marginal_improvement",
})


@dataclass
class ChallengeEntry:
    challenge_type: str
    artifact_id: str
    raw_verdict: str
    challenge_verdict: str


@dataclass
class BenchmarkChallengeRegistry:
    bcr_id: str
    batch_id: str
    pipeline_version: str
    challenge_entries: list[ChallengeEntry]
    n_challenges_required: int
    n_challenges_passed: int
    n_challenges_marginal: int
    n_challenges_failed: int
    hardness_grade: str
    dry_lab_only: bool
    limitations: list[str]
    created_at: str


def _map_verdict(challenge_type: str, raw_verdict: str) -> str:
    if challenge_type == "NCH":
        if raw_verdict in _PASSING_NCH_VERDICTS:
            return "pass"
        if raw_verdict in _MARGINAL_NCH_VERDICTS:
            return "marginal"
        if raw_verdict == "challenge_not_run":
            return "not_run"
        return "fail"
    if challenge_type == "CMC":
        if raw_verdict in _PASSING_CMC_VERDICTS:
            return "pass"
        if raw_verdict in _MARGINAL_CMC_VERDICTS:
            return "marginal"
        if raw_verdict == "challenge_not_run":
            return "not_run"
        return "fail"
    if challenge_type == "SCH":
        if raw_verdict in _PASSING_SCH_VERDICTS:
            return "pass"
        if raw_verdict in _MARGINAL_SCH_VERDICTS:
            return "marginal"
        if raw_verdict == "challenge_not_run":
            return "not_run"
        return "fail"
    return "not_run"


def _compute_hardness_grade(
    n_pass: int,
    n_marginal: int,
    n_required: int,
) -> str:
    if n_pass == n_required:
        return "A"
    if n_pass + n_marginal == n_required:
        return "B"
    if n_pass > 0 or n_marginal > 0:
        return "C"
    return "D"


def validate_benchmark_challenge_registry(bcr: BenchmarkChallengeRegistry) -> None:
    if not bcr.bcr_id.startswith("BCR-"):
        raise ValueError(f"bcr_id must start with 'BCR-': {bcr.bcr_id!r}")
    if not bcr.batch_id:
        raise ValueError("batch_id must be non-empty")
    if not bcr.pipeline_version:
        raise ValueError("pipeline_version must be non-empty")
    seen_types: set[str] = set()
    for entry in bcr.challenge_entries:
        if entry.challenge_type not in REQUIRED_CHALLENGE_TYPES:
            raise ValueError(
                f"challenge_type {entry.challenge_type!r} not in REQUIRED_CHALLENGE_TYPES"
            )
        if entry.challenge_type in seen_types:
            raise ValueError(
                f"duplicate challenge_type: {entry.challenge_type!r}"
            )
        seen_types.add(entry.challenge_type)
        if entry.challenge_verdict not in VALID_CHALLENGE_VERDICTS:
            raise ValueError(
                f"challenge_verdict {entry.challenge_verdict!r} not in VALID_CHALLENGE_VERDICTS"
            )
    if bcr.n_challenges_required != len(REQUIRED_CHALLENGE_TYPES):
        raise ValueError(
            f"n_challenges_required must be {len(REQUIRED_CHALLENGE_TYPES)}"
        )
    n_pass = sum(1 for e in bcr.challenge_entries if e.challenge_verdict == "pass")
    n_marginal = sum(1 for e in bcr.challenge_entries if e.challenge_verdict == "marginal")
    n_fail = sum(
        1 for e in bcr.challenge_entries
        if e.challenge_verdict in ("fail", "not_run")
    )
    if bcr.n_challenges_passed != n_pass:
        raise ValueError("n_challenges_passed mismatch")
    if bcr.n_challenges_marginal != n_marginal:
        raise ValueError("n_challenges_marginal mismatch")
    if bcr.n_challenges_failed != n_fail:
        raise ValueError("n_challenges_failed mismatch")
    if bcr.hardness_grade not in VALID_BCR_HARDNESS_GRADES:
        raise ValueError(
            f"hardness_grade {bcr.hardness_grade!r} not in VALID_BCR_HARDNESS_GRADES"
        )
    if not bcr.dry_lab_only:
        raise ValueError("dry_lab_only must be True")
    if not bcr.limitations:
        raise ValueError("limitations must be non-empty")
    if not bcr.created_at:
        raise ValueError("created_at must be non-empty")


def build_benchmark_challenge_registry(
    *,
    bcr_id: str,
    batch_id: str,
    pipeline_version: str,
    nch_artifact_id: str = "",
    nch_raw_verdict: str = "challenge_not_run",
    cmc_artifact_id: str = "",
    cmc_raw_verdict: str = "challenge_not_run",
    sch_artifact_id: str = "",
    sch_raw_verdict: str = "challenge_not_run",
    limitations: list[str],
    created_at: str,
) -> BenchmarkChallengeRegistry:
    raw = {
        "NCH": (nch_artifact_id, nch_raw_verdict),
        "CMC": (cmc_artifact_id, cmc_raw_verdict),
        "SCH": (sch_artifact_id, sch_raw_verdict),
    }
    entries = [
        ChallengeEntry(
            challenge_type=ctype,
            artifact_id=raw[ctype][0],
            raw_verdict=raw[ctype][1],
            challenge_verdict=_map_verdict(ctype, raw[ctype][1]),
        )
        for ctype in REQUIRED_CHALLENGE_TYPES
    ]
    n_pass = sum(1 for e in entries if e.challenge_verdict == "pass")
    n_marginal = sum(1 for e in entries if e.challenge_verdict == "marginal")
    n_fail = sum(1 for e in entries if e.challenge_verdict in ("fail", "not_run"))
    grade = _compute_hardness_grade(n_pass, n_marginal, len(REQUIRED_CHALLENGE_TYPES))
    bcr = BenchmarkChallengeRegistry(
        bcr_id=bcr_id,
        batch_id=batch_id,
        pipeline_version=pipeline_version,
        challenge_entries=entries,
        n_challenges_required=len(REQUIRED_CHALLENGE_TYPES),
        n_challenges_passed=n_pass,
        n_challenges_marginal=n_marginal,
        n_challenges_failed=n_fail,
        hardness_grade=grade,
        dry_lab_only=True,
        limitations=limitations,
        created_at=created_at,
    )
    validate_benchmark_challenge_registry(bcr)
    return bcr


def format_benchmark_challenge_registry(bcr: BenchmarkChallengeRegistry) -> str:
    lines = [
        f"Benchmark Challenge Registry — {bcr.bcr_id}",
        f"Batch: {bcr.batch_id}  |  Pipeline: {bcr.pipeline_version}",
        f"Hardness grade: {bcr.hardness_grade}  |  "
        f"Passed: {bcr.n_challenges_passed}/{bcr.n_challenges_required}  "
        f"Marginal: {bcr.n_challenges_marginal}  Failed: {bcr.n_challenges_failed}",
        "Challenges:",
    ]
    for entry in bcr.challenge_entries:
        aid = entry.artifact_id if entry.artifact_id else "(none)"
        lines.append(
            f"  {entry.challenge_type}: {entry.challenge_verdict.upper()}"
            f"  [{entry.raw_verdict}]  {aid}"
        )
    lines.append(f"Created: {bcr.created_at}")
    lines.append(f"Limitations: {'; '.join(bcr.limitations)}")
    lines.append(f"dry_lab_only: {bcr.dry_lab_only}")
    return "\n".join(lines)
