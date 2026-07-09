"""Active-learning strategy comparison report.

Compares multiple selection strategies (exploitation, exploration, diversity,
combined, random) on the same synthetic pool with the same hidden active
candidates, producing a structured report that makes selection bias transparent.

Each strategy is a wrapper around ``select_batch_2`` with different weights:

- **exploitation**: ensemble_weight=1.0, others=0 — picks highest-scoring
  candidates regardless of uncertainty or novelty.
- **exploration**: uncertainty_weight=1.0 — picks candidates where the model
  is most unsure.
- **diversity**: diversity_weight=1.0 — picks candidates most dissimilar to
  batch 1, exploring new sequence space.
- **combined**: default weights (ensemble=0.40, uncertainty=0.30,
  diversity=0.30) — the production selector.
- **random**: random selection — cheap baseline for comparison.

The report records per-strategy recovery metrics, ranks strategies by recall,
and identifies whether the production selector is meaningfully different from
simpler alternatives.
"""

from __future__ import annotations

import csv
import logging
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_VERSION = "0.1.0"

# Strategy definitions: human-readable label -> (ensemble, uncertainty, diversity)
STRATEGY_WEIGHTS: dict[str, tuple[float, float, float]] = {
    "exploitation": (1.0, 0.0, 0.0),
    "exploration": (0.0, 1.0, 0.0),
    "diversity": (0.0, 0.0, 1.0),
    "combined": (0.40, 0.30, 0.30),
    "random": (0.0, 0.0, 0.0),  # random uses no weights — handled separately
}


@dataclass(frozen=True)
class StrategyResult:
    """Recovery metrics for a single strategy."""

    strategy_name: str
    rounds_to_first_recovery: int | None
    final_recall: float
    n_hidden_recovered: int
    n_hidden_actives: int
    total_rounds_run: int
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "rounds_to_first_recovery": self.rounds_to_first_recovery,
            "final_recall": self.final_recall,
            "n_hidden_recovered": self.n_hidden_recovered,
            "n_hidden_actives": self.n_hidden_actives,
            "total_rounds_run": self.total_rounds_run,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class StrategyComparisonReport:
    """Report comparing all active-learning strategies."""

    version: str
    pool_size: int
    n_active_total: int
    n_hidden_actives: int
    batch_size: int
    max_rounds: int
    results: tuple[StrategyResult, ...]
    ranked_by_recall: tuple[str, ...]
    best_strategy: str | None
    production_strategy: str
    production_outperforms_random: bool | None
    production_vs_exploitation: str | None
    production_vs_exploration: str | None
    production_vs_diversity: str | None
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "pool_size": self.pool_size,
            "n_active_total": self.n_active_total,
            "n_hidden_actives": self.n_hidden_actives,
            "batch_size": self.batch_size,
            "max_rounds": self.max_rounds,
            "results": [r.to_dict() for r in self.results],
            "ranked_by_recall": list(self.ranked_by_recall),
            "best_strategy": self.best_strategy,
            "production_strategy": self.production_strategy,
            "production_outperforms_random": self.production_outperforms_random,
            "production_vs_exploitation": self.production_vs_exploitation,
            "production_vs_exploration": self.production_vs_exploration,
            "production_vs_diversity": self.production_vs_diversity,
            "notes": list(self.notes),
        }


def _generate_pool(
    *,
    n_total: int = 50,
    n_active: int = 10,
    rng_seed: int = 42,
) -> list[dict]:
    """Generate a synthetic candidate pool for strategy comparison.

    Active candidates get higher ensemble scores and lower disagreement.
    """
    rng = random.Random(rng_seed)
    pool: list[dict] = []
    for i in range(n_total):
        is_active = i < n_active
        cid = f"BENCH-CAND-{i:04d}"
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


def _write_pool(pool: list[dict], path: Path) -> Path:
    fieldnames = list(pool[0].keys()) if pool else []
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in pool:
            writer.writerow(row)
    return path


def _simulate_random_selection(
    hidden_ids: set[str],
    remaining_ids: list[str],
    batch_size: int,
    max_rounds: int,
    rng: random.Random,
) -> tuple[int | None, float, int]:
    """Simulate random batch selection.

    Returns (rounds_to_first_recovery, final_recall, n_recovered).
    """
    available = list(remaining_ids)
    recovered: set[str] = set()
    rounds_to_first: int | None = None
    rounds_run = 0

    for round_n in range(1, max_rounds + 1):
        if not available:
            break
        rounds_run = round_n
        n_pick = min(batch_size, len(available))
        batch = rng.sample(available, n_pick)
        just_recovered = set(batch) & hidden_ids
        recovered.update(just_recovered)
        if just_recovered and rounds_to_first is None:
            rounds_to_first = round_n
        available = [cid for cid in available if cid not in set(batch)]

    final_recall = len(recovered) / len(hidden_ids) if hidden_ids else 0.0
    return rounds_to_first, final_recall, len(recovered)


def _run_strategy(
    strategy_name: str,
    ensemble_w: float,
    uncertainty_w: float,
    diversity_w: float,
    pool_csv: Path,
    hidden_ids: set[str],
    all_candidate_ids: list[str],
    batch_size: int,
    max_rounds: int,
    rng: random.Random,
) -> StrategyResult:
    """Run a single strategy and return its recovery metrics."""
    if strategy_name == "random":
        result_data = _simulate_random_selection(
            hidden_ids,
            all_candidate_ids,
            batch_size,
            max_rounds,
            rng,
        )
        rounds_to_first, final_recall, n_recovered = result_data
        notes: list[str] = []
        return StrategyResult(
            strategy_name=strategy_name,
            rounds_to_first_recovery=rounds_to_first,
            final_recall=round(final_recall, 4),
            n_hidden_recovered=n_recovered,
            n_hidden_actives=len(hidden_ids),
            total_rounds_run=max_rounds if rounds_to_first is None else (
                rounds_to_first if final_recall >= 1.0 else max_rounds
            ),
            notes=tuple(notes),
        )

    from openamp_foundry.active_learning.selector import select_batch_2

    selected_so_far_ids: list[str] = []
    recovered: set[str] = set()
    rounds_to_first: int | None = None
    notes = []
    rounds_run = 0

    for round_n in range(1, max_rounds + 1):
        remaining = [
            cid for cid in all_candidate_ids
            if cid not in set(selected_so_far_ids)
        ]
        if not remaining:
            notes.append(f"Round {round_n}: pool exhausted")
            break
        rounds_run = round_n

        temp_csv = pool_csv.parent / f"_strategy_{strategy_name}_round_{round_n}.csv"
        _write_remaining_pool(pool_csv, remaining, temp_csv)

        try:
            selection = select_batch_2(
                candidates_csv=temp_csv,
                batch_1_ids=[],
                n=batch_size,
                safety_threshold=0.0,
                selectivity_threshold=0.0,
                ensemble_weight=ensemble_w,
                uncertainty_weight=uncertainty_w,
                diversity_weight=diversity_w,
                min_uncertainty_probes=0,
            )
        finally:
            temp_csv.unlink(missing_ok=True)

        selected_ids = [str(c.get("candidate_id", "")) for c in selection.selected]
        selected_so_far_ids.extend(selected_ids)

        just_recovered = set(selected_ids) & hidden_ids
        recovered.update(just_recovered)

        if just_recovered and rounds_to_first is None:
            rounds_to_first = round_n

    final_recall = len(recovered) / len(hidden_ids) if hidden_ids else 0.0

    return StrategyResult(
        strategy_name=strategy_name,
        rounds_to_first_recovery=rounds_to_first,
        final_recall=round(final_recall, 4),
        n_hidden_recovered=len(recovered),
        n_hidden_actives=len(hidden_ids),
        total_rounds_run=rounds_run,
        notes=tuple(notes),
    )


def _write_remaining_pool(
    original_csv: Path,
    remaining_ids: list[str],
    output_csv: Path,
) -> None:
    """Write a CSV containing only the remaining candidate IDs."""
    id_set = set(remaining_ids)
    rows: list[dict] = []
    with open(original_csv, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("candidate_id") in id_set:
                rows.append(row)

    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _compare_recall(
    production_recall: float,
    other_recall: float,
) -> str | None:
    """Compare production recall to another strategy's recall."""
    delta = production_recall - other_recall
    if delta > 0.01:
        return "better"
    if delta < -0.01:
        return "worse"
    return "similar"


def run_strategy_comparison(
    *,
    rng_seed: int = 42,
    n_total: int = 50,
    n_active: int = 10,
    n_hidden_actives: int = 3,
    batch_size: int = 5,
    max_rounds: int = 5,
) -> StrategyComparisonReport:
    """Run the active-learning strategy comparison report.

    All strategies share the same synthetic pool and hidden active candidates.
    Each strategy is evaluated on multi-round recovery of hidden actives.

    Returns:
        ``StrategyComparisonReport`` with per-strategy results and rankings.
    """
    rng = random.Random(rng_seed)

    pool = _generate_pool(
        n_total=n_total,
        n_active=n_active,
        rng_seed=rng_seed,
    )

    active_ids = [
        str(c["candidate_id"]) for c in pool if int(c.get("label", 0)) == 1
    ]
    if not active_ids:
        raise ValueError("No active candidates in generated pool")

    all_candidate_ids = [str(c["candidate_id"]) for c in pool]
    n_hide = min(n_hidden_actives, len(active_ids))
    hidden_ids = set(rng.sample(active_ids, n_hide))

    notes: list[str] = []
    notes.append(
        f"Pool: {len(pool)} total, {len(active_ids)} active, "
        f"{len(pool) - len(active_ids)} inactive"
    )
    notes.append(
        f"Hiding {n_hide}/{len(active_ids)} active candidates"
    )

    import tempfile
    pool_csv = Path(tempfile.mktemp(suffix=".csv"))
    try:
        _write_pool(pool, pool_csv)

        strategy_names = list(STRATEGY_WEIGHTS.keys())
        results: list[StrategyResult] = []

        for sname in strategy_names:
            if sname == "random":
                # Average over 20 random trials
                random_trials = [
                    _run_strategy(
                        "random", 0.0, 0.0, 0.0,
                        pool_csv, hidden_ids, all_candidate_ids,
                        batch_size, max_rounds, rng,
                    )
                    for _ in range(20)
                ]
                avg_recall = sum(
                    r.final_recall for r in random_trials
                ) / len(random_trials)
                valid_rounds = [
                    r.rounds_to_first_recovery
                    for r in random_trials
                    if r.rounds_to_first_recovery is not None
                ]
                avg_rounds = (
                    sum(valid_rounds) / len(valid_rounds)
                    if valid_rounds else None
                )
                avg_recovered = sum(
                    r.n_hidden_recovered for r in random_trials
                ) // len(random_trials)
                results.append(StrategyResult(
                    strategy_name="random",
                    rounds_to_first_recovery=(
                        round(avg_rounds, 2) if avg_rounds is not None else None
                    ),
                    final_recall=round(avg_recall, 4),
                    n_hidden_recovered=avg_recovered,
                    n_hidden_actives=len(hidden_ids),
                    total_rounds_run=max_rounds,
                    notes=("Averaged over 20 random trials",),
                ))
            else:
                ew, uw, dw = STRATEGY_WEIGHTS[sname]
                result = _run_strategy(
                    sname, ew, uw, dw,
                    pool_csv, hidden_ids, all_candidate_ids,
                    batch_size, max_rounds, rng,
                )
                results.append(result)
    finally:
        pool_csv.unlink(missing_ok=True)

    # Rank by recall descending
    ranked = sorted(results, key=lambda r: r.final_recall, reverse=True)
    ranked_names = tuple(r.strategy_name for r in ranked)

    # Best strategy
    best = ranked[0].strategy_name if ranked else None

    # Comparison between production ("combined") and others
    combined_result = next(
        (r for r in results if r.strategy_name == "combined"), None
    )
    random_result = next(
        (r for r in results if r.strategy_name == "random"), None
    )
    exploitation_result = next(
        (r for r in results if r.strategy_name == "exploitation"), None
    )
    exploration_result = next(
        (r for r in results if r.strategy_name == "exploration"), None
    )
    diversity_result = next(
        (r for r in results if r.strategy_name == "diversity"), None
    )

    prod_beats_random: bool | None = None
    if combined_result is not None and random_result is not None:
        prod_beats_random = (
            combined_result.final_recall > random_result.final_recall
        )

    return StrategyComparisonReport(
        version=_VERSION,
        pool_size=len(pool),
        n_active_total=len(active_ids),
        n_hidden_actives=n_hide,
        batch_size=batch_size,
        max_rounds=max_rounds,
        results=tuple(results),
        ranked_by_recall=ranked_names,
        best_strategy=best,
        production_strategy="combined",
        production_outperforms_random=prod_beats_random,
        production_vs_exploitation=(
            _compare_recall(
                combined_result.final_recall if combined_result else 0.0,
                exploitation_result.final_recall if exploitation_result else 0.0,
            ) if combined_result and exploitation_result else None
        ),
        production_vs_exploration=(
            _compare_recall(
                combined_result.final_recall if combined_result else 0.0,
                exploration_result.final_recall if exploration_result else 0.0,
            ) if combined_result and exploration_result else None
        ),
        production_vs_diversity=(
            _compare_recall(
                combined_result.final_recall if combined_result else 0.0,
                diversity_result.final_recall if diversity_result else 0.0,
            ) if combined_result and diversity_result else None
        ),
        notes=tuple(notes),
    )


def write_comparison_json(
    report: StrategyComparisonReport,
    path: Path,
) -> Path:
    """Write the comparison report to a JSON file."""
    import json
    path.write_text(json.dumps(report.to_dict(), indent=2) + "\n")
    return path


def write_comparison_markdown(
    report: StrategyComparisonReport,
    path: Path,
) -> Path:
    """Write a human-readable Markdown summary."""
    lines: list[str] = []
    lines.append("# Active-Learning Strategy Comparison Report")
    lines.append("")
    lines.append(f"> **Version:** {report.version}")
    lines.append(f"> **Generated:** auto")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(
        f"Compared {len(report.results)} strategies on a synthetic pool of "
        f"**{report.pool_size}** candidates "
        f"(**{report.n_active_total}** active, "
        f"**{report.n_hidden_actives}** hidden)."
    )
    lines.append(f"Batch size: **{report.batch_size}**, Max rounds: **{report.max_rounds}**.")
    lines.append("")

    # Strategy descriptions
    lines.append("## Strategies")
    lines.append("")
    lines.append("| Strategy | Ensemble weight | Uncertainty weight | Diversity weight | Description |")
    lines.append("|----------|:---------------:|:-----------------:|:----------------:|-------------|")
    for sname in STRATEGY_WEIGHTS:
        ew, uw, dw = STRATEGY_WEIGHTS[sname]
        if sname == "random":
            desc = "Random selection (20-trial average)"
        elif sname == "combined":
            desc = "Production selector with default weights"
        elif sname == "exploitation":
            desc = "Highest ensemble score only"
        elif sname == "exploration":
            desc = "Highest uncertainty only"
        elif sname == "diversity":
            desc = "Most diverse vs batch 1 only"
        else:
            desc = ""
        lines.append(f"| {sname} | {ew} | {uw} | {dw} | {desc} |")
    lines.append("")

    # Per-strategy results
    lines.append("## Per-Strategy Recovery Results")
    lines.append("")
    lines.append("| Strategy | Rounds to first recovery | Final recall | Hidden recovered | Notes |")
    lines.append("|----------|:------------------------:|:------------:|:----------------:|-------|")
    for r in report.results:
        rtf = (
            f"{r.rounds_to_first_recovery}"
            if r.rounds_to_first_recovery is not None
            else "N/A"
        )
        note = r.notes[0] if r.notes else ""
        lines.append(
            f"| {r.strategy_name} | {rtf} | {r.final_recall} | "
            f"{r.n_hidden_recovered}/{r.n_hidden_actives} | {note} |"
        )
    lines.append("")

    # Ranking
    lines.append("## Ranking by Recall")
    lines.append("")
    lines.append(f"Best strategy: **{report.best_strategy}**")
    lines.append("")
    for i, sname in enumerate(report.ranked_by_recall, 1):
        r = next(r for r in report.results if r.strategy_name == sname)
        marker = " ← production" if sname == "combined" else ""
        lines.append(f"{i}. **{sname}**: recall={r.final_recall}{marker}")
    lines.append("")

    # Production comparison
    lines.append("## Production Selector Comparison")
    lines.append("")
    lines.append(
        f"The production strategy (**{report.production_strategy}**) "
        f"{'outperforms' if report.production_outperforms_random else 'does NOT outperform'} "
        f"random selection."
    )
    lines.append("")
    comparisons = [
        ("vs exploitation", report.production_vs_exploitation),
        ("vs exploration", report.production_vs_exploration),
        ("vs diversity", report.production_vs_diversity),
    ]
    for label, value in comparisons:
        if value is not None:
            lines.append(f"- **{label}**: {value}")
    lines.append("")

    # Caveat
    lines.append("## Caveats")
    lines.append("")
    lines.append(
        "- This report uses **synthetic data** with known active/inactive labels. "
        "Results reflect code-path integrity, not biological performance."
    )
    lines.append(
        "- All strategies were run with safety/selectivity gates disabled "
        "(threshold=0.0) to isolate strategy effects."
    )
    lines.append(
        "- Random baseline is averaged over 20 Monte Carlo trials; "
        "deterministic strategies use a single run."
    )
    lines.append(
        "- The production selector optimizes for multiple objectives "
        "(activity, safety, diversity) that this benchmark does not fully measure."
    )
    lines.append(
        "- A strategy that ranks highest on recall may not be the best choice "
        "for real candidate selection — domain-specific constraints matter."
    )
    lines.append(
        "- This comparison is informational and requires qualified human review "
        "before influencing selection decisions."
    )

    path.write_text("\n".join(lines) + "\n")
    return path
