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
    """Higher is better: reward ensemble, stability, novelty, selectivity; penalise disagreement.

    Formula:
        ensemble − 0.30×disagreement + 0.05×serum_stability + 0.05×novelty
                 + 0.05×rich_selectivity − cytotox_penalty

    The cytotox_penalty is non-zero only for candidates in the HIGH_CYTOTOX_RISK tier
    (rich_selectivity < 0.5). It applies an additional −0.05 × (0.5 − rich_sel) / 0.5
    penalty on top of the reduced bonus, totalling a max additional demerit of −0.05 vs
    the soft-bonus formulation.

    Weights are intentionally equal for the three bonus terms (0.05 each) so no single
    physicochemical axis dominates over the ensemble activity prediction. The ensemble
    score remains the dominant term.

    rich_selectivity [0,1]: evidence-based composite of 8 physicochemical features
    identified as statistically significant for selective_vs_hemolytic discrimination
    (feature decomposition benchmark v0.5.15). Detection AUROC=0.7138 (CI 0.63-0.80)
    — the first pipeline score with CI excluding 0.5. Replaces the old
    selectivity_proxy (AUROC=0.5744, CI 0.50-0.66, not significant). Falls back to
    selectivity_proxy when rich_selectivity is absent (backward compatibility).

    Literature: Dathe & Wieprecht (1999) BBA 1462:71-87; Carotenuto et al. (2008) J Med Chem.
    """
    ensemble = scores.get("ensemble", 0.0)
    disagreement = scores.get("disagreement", 0.5)
    stability = scores.get("serum_stability", 0.5)
    novelty = scores.get("novelty", 0.0)
    selectivity = scores.get("rich_selectivity")
    if selectivity is None:
        selectivity = scores.get("selectivity_proxy", 1.0)
    # Additional penalty for HIGH_CYTOTOX_RISK tier (selectivity < 0.5)
    cytotox_penalty = 0.0 if selectivity >= 0.5 else 0.05 * (0.5 - selectivity) / 0.5
    return round(
        ensemble - 0.3 * disagreement + 0.05 * stability + 0.05 * novelty
        + 0.05 * selectivity - cytotox_penalty,
        6,
    )


def _is_diverse_vs_panel(
    candidate: dict,
    panel: list[dict],
    similarity_threshold: float,
) -> bool:
    """Return True if candidate is below similarity_threshold with every panel member."""
    from openamp_foundry.scoring.novelty import normalized_similarity
    seq = candidate.get("sequence", "")
    return all(
        normalized_similarity(seq, sel.get("sequence", "")) <= similarity_threshold
        for sel in panel
    )


def select_pilot_panel(
    candidates: list[dict],
    n: int = 20,
    max_per_seed: int | None = None,
    similarity_threshold: float | None = None,
    min_per_structural_class: int = 0,
) -> list[dict]:
    """Select an n-candidate first-synthesis-wave panel from a list of nominees.

    Selection rules (in order):
    1. If min_per_structural_class > 0, reserve up to that many top-priority
       candidates per heuristic structural class.
    2. One representative per distinct seed, chosen by pilot_priority.
    3. Remaining slots filled from the rest of the pool, highest priority first,
       subject to the per-seed cap (max_per_seed).
    4. If n < number of seeds, take the top-n seeds by priority.
    5. (Optional) If similarity_threshold is provided, each candidate added in
       phases 1–3 is additionally required to be below similarity_threshold with
       every already-selected candidate. This eliminates near-duplicate siblings
       that crossed seed boundaries through conservative substitution.

    Args:
        candidates: List of scored candidate dicts (must have "scores" and "source").
        n: Total panel size.
        max_per_seed: If set, cap the number of nominees from any single seed family.
            Recommended: n // number_of_seeds (e.g. 4 for a 20-member, 8-seed panel).
        similarity_threshold: Levenshtein similarity ceiling between any two selected
            candidates (e.g. 0.75). Candidates that are too similar to an
            already-selected candidate are skipped. None = no filter (default).
        min_per_structural_class: Optional floor for coarse AMP structural classes
            (`cysteine_rich`, `short`, `proline_rich`, `highly_cationic`,
            `moderately_cationic`, `low_charge`). This compensates for the
            documented v0.5.37 helic/charge ranking bias; it is a diversity
            guard, not evidence of biological activity.

    Each returned dict gets an added `pilot_priority`, `seed`, and `pilot_rank` key.
    """
    if not candidates:
        return []

    enriched = []
    from openamp_foundry.selection.structural_class import classify_structural_class

    for c in candidates:
        ec = dict(c)
        ec["seed"] = _seed_from_source(c.get("source", ""))
        ec["pilot_priority"] = _pilot_priority(c.get("scores", {}))
        ec["structural_class"] = classify_structural_class(
            c.get("sequence", ""),
            c.get("features", {}),
        )
        enriched.append(ec)

    enriched.sort(key=lambda x: x["pilot_priority"], reverse=True)

    selected: list[dict] = []
    seed_counts: dict[str, int] = {}
    remainder: list[dict] = []

    def _diverse(c: dict) -> bool:
        if similarity_threshold is None:
            return True
        return _is_diverse_vs_panel(c, selected, similarity_threshold)

    selected_ids: set[str] = set()

    def _candidate_key(c: dict) -> str:
        return str(c.get("candidate_id") or c.get("sequence") or id(c))

    def _append(c: dict) -> bool:
        key = _candidate_key(c)
        if key in selected_ids or not _diverse(c):
            return False
        selected.append(c)
        selected_ids.add(key)
        seed = c["seed"]
        seed_counts[seed] = seed_counts.get(seed, 0) + 1
        return True

    # Phase 0 — bias-aware floor by heuristic structural class.
    if min_per_structural_class > 0:
        class_counts: dict[str, int] = {}
        for c in enriched:
            if len(selected) >= n:
                break
            cls = c["structural_class"]
            if class_counts.get(cls, 0) >= min_per_structural_class:
                continue
            if max_per_seed is not None and seed_counts.get(c["seed"], 0) >= max_per_seed:
                continue
            if _append(c):
                class_counts[cls] = class_counts.get(cls, 0) + 1

    # Phase 1 — one per seed (best by priority)
    seen_seeds: set[str] = set()
    phase2_candidates: list[dict] = []
    for c in enriched:
        seed = c["seed"]
        if _candidate_key(c) in selected_ids:
            seen_seeds.add(seed)
            continue
        if seed not in seen_seeds:
            if _append(c):
                seen_seeds.add(seed)
            else:
                # Too similar to an already-selected candidate from a different seed.
                # Still mark seed as seen so Phase 2 can fill from its other variants.
                seen_seeds.add(seed)
                phase2_candidates.append(c)
        else:
            phase2_candidates.append(c)
        if len(selected) == n:
            break

    # Phase 2 — fill remaining slots, honouring max_per_seed and diversity caps
    for c in phase2_candidates:
        if len(selected) >= n:
            break
        seed = c["seed"]
        count = seed_counts.get(seed, 0)
        if max_per_seed is not None and count >= max_per_seed:
            remainder.append(c)
            continue
        if not _append(c):
            remainder.append(c)
            continue

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
        _append(c)

    if similarity_threshold is not None and len(selected) < n:
        _log.info(
            "Diversity filter (threshold=%.2f) limited panel to %d/%d slots. "
            "Consider lowering --similarity-threshold or increasing pool diversity.",
            similarity_threshold,
            len(selected),
            n,
        )

    # Final sort: highest priority first
    selected.sort(key=lambda x: x["pilot_priority"], reverse=True)
    for rank, c in enumerate(selected, start=1):
        c["pilot_rank"] = rank

    return selected
