"""Cheap enemy comparison report — Phase C C9.

Standardizes anti-hype: compares an advanced scorer's metric against every
declared cheap enemy baseline from a benchmark card. An advanced scorer
earns ranking authority ONLY if it beats ALL cheap enemies on the primary metric.

This prevents performance claims that would be matched or exceeded by trivial
heuristics (charge threshold, length filter, hydrophobicity cutoff).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EnemyResult:
    enemy_name: str
    enemy_score: float
    advanced_score: float
    margin: float
    beats_enemy: bool


@dataclass
class CheapEnemyComparisonReport:
    bmc_id: str
    metric: str
    advanced_scorer_name: str
    advanced_scorer_score: float
    enemy_results: list[EnemyResult] = field(default_factory=list)
    n_enemies: int = 0
    n_beaten: int = 0
    n_failed: int = 0
    all_enemies_beaten: bool = False
    ranking_authority_granted: bool = False
    comparison_summary: str = ""
    failed_enemies: list[str] = field(default_factory=list)


def compute_cheap_enemy_comparison(
    bmc_id: str,
    metric: str,
    advanced_scorer_name: str,
    advanced_scorer_score: float,
    enemy_scores: dict[str, float],
    higher_is_better: bool = True,
) -> CheapEnemyComparisonReport:
    """Compare an advanced scorer against all declared cheap enemy baselines.

    Args:
        bmc_id: BMC- card ID that governs this benchmark.
        metric: The evaluation metric being compared (e.g. "precision_at_k").
        advanced_scorer_name: Name of the advanced scoring method being evaluated.
        advanced_scorer_score: The advanced scorer's metric value.
        enemy_scores: Dict mapping cheap enemy name to its metric value.
        higher_is_better: Whether higher metric values are better (True for precision,
                         AUC, etc.; False for calibration error, etc.).

    Returns:
        CheapEnemyComparisonReport with per-enemy pass/fail and overall authority decision.

    Raises:
        ValueError: If bmc_id does not start with 'BMC-'.
        ValueError: If enemy_scores is empty.
    """
    if not bmc_id.startswith("BMC-"):
        raise ValueError(f"bmc_id must start with 'BMC-', got '{bmc_id}'")
    if not enemy_scores:
        raise ValueError("enemy_scores must not be empty — at least one cheap enemy is required")

    results: list[EnemyResult] = []
    failed: list[str] = []

    for enemy_name, enemy_score in sorted(enemy_scores.items()):
        if higher_is_better:
            beats = advanced_scorer_score > enemy_score
            margin = advanced_scorer_score - enemy_score
        else:
            beats = advanced_scorer_score < enemy_score
            margin = enemy_score - advanced_scorer_score

        result = EnemyResult(
            enemy_name=enemy_name,
            enemy_score=enemy_score,
            advanced_score=advanced_scorer_score,
            margin=margin,
            beats_enemy=beats,
        )
        results.append(result)
        if not beats:
            failed.append(enemy_name)

    n_beaten = sum(1 for r in results if r.beats_enemy)
    n_failed = len(failed)
    all_beaten = n_failed == 0
    authority = all_beaten

    direction = "↑ higher" if higher_is_better else "↓ lower"
    if all_beaten:
        summary = (
            f"{advanced_scorer_name} beats ALL {len(results)} cheap enemies on {metric} "
            f"({direction} is better). Ranking authority GRANTED for {bmc_id}."
        )
    else:
        failed_str = ", ".join(failed)
        summary = (
            f"{advanced_scorer_name} FAILS to beat {n_failed}/{len(results)} cheap enemies "
            f"on {metric} ({direction} is better): [{failed_str}]. "
            f"Ranking authority DENIED for {bmc_id}. "
            "Do not promote this scorer until all enemies are beaten."
        )

    return CheapEnemyComparisonReport(
        bmc_id=bmc_id,
        metric=metric,
        advanced_scorer_name=advanced_scorer_name,
        advanced_scorer_score=advanced_scorer_score,
        enemy_results=results,
        n_enemies=len(results),
        n_beaten=n_beaten,
        n_failed=n_failed,
        all_enemies_beaten=all_beaten,
        ranking_authority_granted=authority,
        comparison_summary=summary,
        failed_enemies=failed,
    )


def format_cheap_enemy_comparison(report: CheapEnemyComparisonReport) -> str:
    """Format a CheapEnemyComparisonReport as a human-readable string."""
    lines = [
        "=== CHEAP ENEMY COMPARISON REPORT ===",
        f"Benchmark card: {report.bmc_id}",
        f"Metric: {report.metric}",
        f"Advanced scorer: {report.advanced_scorer_name} ({report.advanced_scorer_score:.4f})",
        "",
        f"-- CHEAP ENEMY RESULTS ({report.n_beaten}/{report.n_enemies} beaten) --",
    ]
    for result in sorted(report.enemy_results, key=lambda r: r.enemy_name):
        status = "PASS" if result.beats_enemy else "FAIL"
        sign = "+" if result.margin >= 0 else ""
        lines.append(
            f"  [{status}] {result.enemy_name}: "
            f"enemy={result.enemy_score:.4f}, "
            f"advanced={result.advanced_score:.4f}, "
            f"margin={sign}{result.margin:.4f}"
        )
    lines.extend([
        "",
        f"ALL ENEMIES BEATEN: {'YES' if report.all_enemies_beaten else 'NO'}",
        f"RANKING AUTHORITY: {'GRANTED' if report.ranking_authority_granted else 'DENIED'}",
        "",
        report.comparison_summary,
        "",
        "NOTICE: Ranking authority requires beating ALL declared cheap enemies.",
        "Partial victory is NOT sufficient — see CLAUDE.md anti-hype clause.",
    ])
    return "\n".join(lines)
