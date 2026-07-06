"""Active-learning benchmark: can the batch-2 selector recover hidden active candidates?

Simulates a multi-round active-learning loop:

1. A pool of candidates is created with known active/inactive labels.
2. A subset of active candidates is "hidden" (their label is unknown to the
   selector, but they remain in the pool as eligible candidates).
3. Each round calls ``select_batch_2`` on the remaining eligible pool (all
   candidates not yet selected, including hidden actives).
4. After each round, we check whether any hidden active candidate was selected.
5. The benchmark reports rounds-to-recovery and recall@k, comparing against
   a random-baseline selector.

The benchmark is a **code-path integrity test**, not a biological claim.
It verifies that the selection heuristic correlates with known activity in
a controlled synthetic setting — a necessary but not sufficient condition
for real-world utility.
"""

from __future__ import annotations

import csv
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_BENCHMARK_VERSION = "0.1.0"

# Pre-registered recovery threshold: a reasonable selector should recover
# at least 1 hidden active within this many rounds.
PREREGISTERED_MAX_ROUNDS_TO_FIRST_RECOVERY = 3

# Pre-registered recall threshold: at least one third of hidden actives
# recovered within max_rounds.
PREREGISTERED_MIN_RECALL = 0.33


@dataclass(frozen=True)
class RecoveryRound:
    """Outcome of a single active-learning round."""

    round_n: int
    batch_ids: tuple[str, ...]
    hidden_recovered_ids: tuple[str, ...]
    n_recovered: int
    cumulative_recall: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_n": self.round_n,
            "batch_ids": list(self.batch_ids),
            "hidden_recovered_ids": list(self.hidden_recovered_ids),
            "n_recovered": self.n_recovered,
            "cumulative_recall": self.cumulative_recall,
        }


@dataclass(frozen=True)
class ActiveLearningBenchmarkResult:
    """Result of a complete active-learning benchmark run."""

    version: str
    n_hidden_actives: int
    pool_size: int
    n_active_total: int
    batch_size: int
    max_rounds: int
    rounds_to_first_recovery: int | None
    final_recall: float
    rounds: tuple[RecoveryRound, ...]
    random_baseline_rounds_to_first: float | None
    random_baseline_final_recall: float
    selector_outperforms_random: bool | None
    passed: bool
    preregistered_max_rounds: int
    preregistered_min_recall: float
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "n_hidden_actives": self.n_hidden_actives,
            "pool_size": self.pool_size,
            "n_active_total": self.n_active_total,
            "batch_size": self.batch_size,
            "max_rounds": self.max_rounds,
            "rounds_to_first_recovery": self.rounds_to_first_recovery,
            "final_recall": self.final_recall,
            "rounds": [r.to_dict() for r in self.rounds],
            "random_baseline_rounds_to_first": self.random_baseline_rounds_to_first,
            "random_baseline_final_recall": self.random_baseline_final_recall,
            "selector_outperforms_random": self.selector_outperforms_random,
            "passed": self.passed,
            "preregistered_max_rounds": self.preregistered_max_rounds,
            "preregistered_min_recall": self.preregistered_min_recall,
            "notes": list(self.notes),
        }


def generate_benchmark_pool(
    *,
    n_total: int = 50,
    n_active: int = 10,
    rng_seed: int = 42,
) -> list[dict]:
    """Generate a synthetic candidate pool for the active-learning benchmark.

    Active candidates are given higher ensemble scores and lower disagreement
    than inactive ones, simulating the signal that ``select_batch_2`` uses.
    """
    rng = random.Random(rng_seed)
    pool: list[dict] = []

    for i in range(n_total):
        is_active = i < n_active
        cid = f"BENCH-CAND-{i:04d}"
        # Active: high ensemble (0.75-0.95), low disagreement (0.05-0.20)
        # Inactive: low ensemble (0.30-0.55), high disagreement (0.20-0.50)
        if is_active:
            ensemble = rng.uniform(0.75, 0.95)
            disagreement = rng.uniform(0.05, 0.20)
        else:
            ensemble = rng.uniform(0.30, 0.55)
            disagreement = rng.uniform(0.20, 0.50)

        pool.append({
            "pilot_rank": str(i + 1),
            "candidate_id": cid,
            "sequence": f"PEPTIDE{i:04d}AKLF",
            "length": 12,
            "seed": "BENCH-SEED",
            "ensemble": round(ensemble, 4),
            "activity": round(ensemble, 4),
            "boman_activity": "0.50",
            "disagreement": round(disagreement, 4),
            "safety": "0.90",
            "synthesis": "0.85",
            "novelty": "0.70",
            "serum_stability": "0.65",
            "selectivity_proxy": "0.60",
            "rich_selectivity": "0.75",
            "pilot_priority": "0.75",
            "amphipathic_score": "1.5",
            "charge_ph74": "4.0",
            "label": 1 if is_active else 0,
        })
    return pool


def write_benchmark_pool(pool: list[dict], path: Path) -> Path:
    """Write a benchmark pool to CSV."""
    fieldnames = list(pool[0].keys()) if pool else []
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in pool:
            writer.writerow(row)
    return path


def _simulate_random_selection(
    pool: list[dict],
    hidden_ids: set[str],
    batch_size: int,
    max_rounds: int,
    rng: random.Random,
) -> tuple[int | None, float]:
    """Simulate random batch selection.

    Returns (rounds_to_first_recovery, final_recall).
    """
    remaining_ids = [str(c["candidate_id"]) for c in pool]
    recovered: set[str] = set()
    rounds_to_first: int | None = None

    for round_n in range(1, max_rounds + 1):
        if not remaining_ids:
            break
        n_pick = min(batch_size, len(remaining_ids))
        batch = rng.sample(remaining_ids, n_pick)

        just_recovered = set(batch) & hidden_ids
        recovered.update(just_recovered)

        if just_recovered and rounds_to_first is None:
            rounds_to_first = round_n

        remaining_ids = [cid for cid in remaining_ids if cid not in set(batch)]

    final_recall = len(recovered) / len(hidden_ids) if hidden_ids else 0.0
    return rounds_to_first, final_recall


def run_active_learning_benchmark(
    pool_csv: str | Path,
    *,
    n_hidden_actives: int = 3,
    batch_size: int = 5,
    max_rounds: int = 5,
    rng_seed: int = 42,
) -> ActiveLearningBenchmarkResult:
    """Run the active-learning recovery benchmark.

    Args:
        pool_csv: Path to a CSV with candidates plus a ``label`` column
            (1=active, 0=inactive).
        n_hidden_actives: How many known active candidates to hide.
        batch_size: Number of candidates selected per round.
        max_rounds: Maximum number of selection rounds.
        rng_seed: Seed for reproducibility.

    Returns:
        ``ActiveLearningBenchmarkResult``.
    """
    csv_path = Path(pool_csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"Pool CSV not found: {csv_path}")

    pool = _load_pool(csv_path)
    rng = random.Random(rng_seed)

    active_ids = [
        str(c["candidate_id"])
        for c in pool
        if int(c.get("label", 0)) == 1
    ]
    inactive_ids = [
        str(c["candidate_id"])
        for c in pool
        if int(c.get("label", 0)) == 0
    ]

    if not active_ids:
        raise ValueError("No active candidates (label=1) found in pool CSV")

    n_hide = min(n_hidden_actives, len(active_ids))
    hidden_ids = set(rng.sample(active_ids, n_hide))

    notes: list[str] = []
    notes.append(
        f"Hiding {n_hide}/{len(active_ids)} active candidates: "
        f"{', '.join(sorted(hidden_ids))}"
    )
    notes.append(
        f"Pool: {len(pool)} total, {len(active_ids)} active, "
        f"{len(inactive_ids)} inactive"
    )

    # Simulate rounds
    selected_so_far_ids: list[str] = []
    recovered: set[str] = set()
    rounds_to_first: int | None = None

    rounds: list[RecoveryRound] = []

    for round_n in range(1, max_rounds + 1):
        # Build temp CSV with remaining candidates (include hidden actives)
        remaining = [
            c for c in pool
            if str(c["candidate_id"]) not in set(selected_so_far_ids)
        ]
        if not remaining:
            notes.append(f"Round {round_n}: pool exhausted")
            break

        temp_csv = csv_path.parent / f"_bench_round_{round_n}.csv"
        with open(temp_csv, "w", newline="") as f:
            fieldnames = list(pool[0].keys()) if pool else []
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for c in remaining:
                w.writerow(c)

        from openamp_foundry.active_learning.selector import select_batch_2

        selection = select_batch_2(
            candidates_csv=temp_csv,
            batch_1_ids=[],  # no IDs are "tested" — all are eligible
            n=batch_size,
            safety_threshold=0.0,
            selectivity_threshold=0.0,
        )

        temp_csv.unlink(missing_ok=True)

        selected_ids = [str(c["candidate_id"]) for c in selection.selected]
        selected_so_far_ids.extend(selected_ids)

        just_recovered = set(selected_ids) & hidden_ids
        recovered.update(just_recovered)

        if just_recovered and rounds_to_first is None:
            rounds_to_first = round_n
            notes.append(
                f"Round {round_n}: recovered {len(just_recovered)} hidden active(s): "
                f"{', '.join(sorted(just_recovered))}"
            )

        cumulative_recall = len(recovered) / len(hidden_ids) if hidden_ids else 0.0

        rounds.append(RecoveryRound(
            round_n=round_n,
            batch_ids=tuple(selected_ids),
            hidden_recovered_ids=tuple(sorted(just_recovered)),
            n_recovered=len(just_recovered),
            cumulative_recall=cumulative_recall,
        ))

    final_recall = rounds[-1].cumulative_recall if rounds else 0.0

    # Random baseline (average over 20 trials)
    random_trials = [
        _simulate_random_selection(pool, hidden_ids, batch_size, max_rounds, rng)
        for _ in range(20)
    ]
    valid_rounds = [r for r, _ in random_trials if r is not None]
    random_mean_rounds = (
        sum(valid_rounds) / len(valid_rounds) if valid_rounds else None
    )
    random_mean_recall = (
        sum(recall for _, recall in random_trials) / len(random_trials)
    )

    # Compare against random baseline
    selector_outperforms = None
    if rounds_to_first is not None and random_mean_rounds is not None:
        selector_outperforms = rounds_to_first < random_mean_rounds
    if selector_outperforms is None and final_recall > random_mean_recall:
        selector_outperforms = True

    # Pass/fail against pre-registered thresholds
    passed = True
    if rounds_to_first is not None:
        passed = passed and (rounds_to_first <= PREREGISTERED_MAX_ROUNDS_TO_FIRST_RECOVERY)
    else:
        passed = False
        notes.append(
            f"FAIL: selector did not recover any hidden active within {max_rounds} rounds"
        )

    passed = passed and (final_recall >= PREREGISTERED_MIN_RECALL)

    return ActiveLearningBenchmarkResult(
        version=_BENCHMARK_VERSION,
        n_hidden_actives=n_hide,
        pool_size=len(pool),
        n_active_total=len(active_ids),
        batch_size=batch_size,
        max_rounds=max_rounds,
        rounds_to_first_recovery=rounds_to_first,
        final_recall=round(final_recall, 4),
        rounds=tuple(rounds),
        random_baseline_rounds_to_first=(
            round(random_mean_rounds, 2) if random_mean_rounds is not None else None
        ),
        random_baseline_final_recall=round(random_mean_recall, 4),
        selector_outperforms_random=selector_outperforms,
        passed=passed,
        preregistered_max_rounds=PREREGISTERED_MAX_ROUNDS_TO_FIRST_RECOVERY,
        preregistered_min_recall=PREREGISTERED_MIN_RECALL,
        notes=tuple(notes),
    )


def _load_pool(csv_path: Path) -> list[dict]:
    rows: list[dict[str, Any]] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            parsed: dict[str, Any] = {}
            for k, v in row.items():
                k = k.strip()
                if v is None:
                    parsed[k] = None
                else:
                    v = v.strip()
                try:
                    parsed[k] = float(v)
                except (ValueError, TypeError):
                    try:
                        parsed[k] = int(v)
                    except (ValueError, TypeError):
                        parsed[k] = v
            rows.append(parsed)
    return rows
