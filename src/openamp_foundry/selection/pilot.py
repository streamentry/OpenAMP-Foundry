from __future__ import annotations

import logging

_log = logging.getLogger(__name__)


def _seed_from_source(source: str) -> str:
    """Extract seed ID from a source string like 'template_mutation_from_SEED-003'."""
    prefix = "template_mutation_from_"
    if source.startswith(prefix):
        return source[len(prefix):]
    return source


def _pilot_priority(scores: dict) -> float:
    """Higher is better: reward ensemble, reward serum stability, penalise disagreement.

    Serum stability is weighted lightly (0.05) so it acts as a tiebreaker without
    overriding the ensemble score.  A candidate with stability=1.0 gains at most +0.05.
    """
    ensemble = scores.get("ensemble", 0.0)
    disagreement = scores.get("disagreement", 0.5)
    stability = scores.get("serum_stability", 0.5)
    return round(ensemble - 0.3 * disagreement + 0.05 * stability, 6)


def select_pilot_panel(
    candidates: list[dict],
    n: int = 20,
    max_per_seed: int | None = None,
) -> list[dict]:
    """Select an n-candidate first-synthesis-wave panel from a list of nominees.

    Selection rules (in order):
    1. One representative per distinct seed, chosen by pilot_priority.
    2. Remaining slots filled from the rest of the pool, highest priority first,
       subject to the per-seed cap (max_per_seed).
    3. If n < number of seeds, take the top-n seeds by priority.

    Args:
        candidates: List of scored candidate dicts (must have "scores" and "source").
        n: Total panel size.
        max_per_seed: If set, cap the number of nominees from any single seed family.
            Without this cap, a large high-scoring family can dominate the panel.
            Recommended: n // number_of_seeds (e.g. 4 for a 20-member, 5-seed panel).

    Each returned dict gets an added `pilot_priority` and `seed` key.
    """
    if not candidates:
        return []

    enriched = []
    for c in candidates:
        ec = dict(c)
        ec["seed"] = _seed_from_source(c.get("source", ""))
        ec["pilot_priority"] = _pilot_priority(c.get("scores", {}))
        enriched.append(ec)

    enriched.sort(key=lambda x: x["pilot_priority"], reverse=True)

    selected: list[dict] = []
    seed_counts: dict[str, int] = {}
    remainder: list[dict] = []

    # Phase 1 — one per seed (best by priority)
    seen_seeds: set[str] = set()
    phase2_candidates: list[dict] = []
    for c in enriched:
        seed = c["seed"]
        if seed not in seen_seeds:
            selected.append(c)
            seen_seeds.add(seed)
            seed_counts[seed] = 1
        else:
            phase2_candidates.append(c)
        if len(selected) == n:
            break

    # Phase 2 — fill remaining slots, honouring max_per_seed cap
    for c in phase2_candidates:
        if len(selected) >= n:
            break
        seed = c["seed"]
        count = seed_counts.get(seed, 0)
        if max_per_seed is not None and count >= max_per_seed:
            remainder.append(c)
            continue
        selected.append(c)
        seed_counts[seed] = count + 1

    # Phase 3 — if max_per_seed left unfilled slots, fill from remainder without cap
    if remainder and len(selected) < n and max_per_seed is not None:
        _log.warning(
            "max_per_seed=%d cap could not be honoured for all slots; "
            "filling %d remaining slot(s) from cap-overflow candidates.",
            max_per_seed,
            n - len(selected),
        )
    for c in remainder:
        if len(selected) >= n:
            break
        selected.append(c)

    # Final sort: highest priority first
    selected.sort(key=lambda x: x["pilot_priority"], reverse=True)
    for rank, c in enumerate(selected, start=1):
        c["pilot_rank"] = rank

    return selected
