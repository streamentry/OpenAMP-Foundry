from __future__ import annotations


def _seed_from_source(source: str) -> str:
    """Extract seed ID from a source string like 'template_mutation_from_SEED-003'."""
    prefix = "template_mutation_from_"
    if source.startswith(prefix):
        return source[len(prefix):]
    return source


def _pilot_priority(scores: dict) -> float:
    """Higher is better: reward ensemble score, penalise scorer disagreement."""
    ensemble = scores.get("ensemble", 0.0)
    disagreement = scores.get("disagreement", 0.5)
    return round(ensemble - 0.3 * disagreement, 6)


def select_pilot_panel(
    candidates: list[dict],
    n: int = 20,
) -> list[dict]:
    """Select an n-candidate first-synthesis-wave panel from a list of nominees.

    Selection rules (in order):
    1. One representative per distinct seed, chosen by pilot_priority.
    2. Remaining slots filled from the rest of the pool, highest priority first.
    3. If n < number of seeds, take the top-n seeds by priority.

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
    seen_seeds: set[str] = set()
    remainder: list[dict] = []

    # Phase 1 — one per seed (best by priority)
    for c in enriched:
        seed = c["seed"]
        if seed not in seen_seeds:
            selected.append(c)
            seen_seeds.add(seed)
        else:
            remainder.append(c)
        if len(selected) == n:
            break

    # Phase 2 — fill remaining slots
    for c in remainder:
        if len(selected) >= n:
            break
        selected.append(c)

    # Final sort: highest priority first
    selected.sort(key=lambda x: x["pilot_priority"], reverse=True)
    for rank, c in enumerate(selected, start=1):
        c["pilot_rank"] = rank

    return selected
