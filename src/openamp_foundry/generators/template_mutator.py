"""Systematic template-based candidate generator.

This is a deliberately simple, bounded mutation explorer — not a learned model.
It generates AMP candidate variants by applying conservative substitutions to
known AMP-like template sequences.

Conservative substitution groups (physicochemically similar):
  Cationic: K, R, H (positive charge, preserve charge character)
  Hydrophobic: L, I, V, A, F, M (preserve hydrophobic character)
  Polar/neutral: S, T, N, Q (no charge)
  Aromatic: W, Y, F (aromatic, hydrophobic)

Design rules:
  - Preserve backbone length (no insertions/deletions in this generator)
  - Never target charged residues for hydrophobic substitution (or vice versa)
  - Use deterministic seeding so output is reproducible
  - Aggregation-safe double substitutions avoid creating hydrophobic runs ≥4
    (matching the QC HYDROPHOBIC_RUN_RE threshold used in presynth_check.py)

This generator does NOT claim to produce biologically active peptides.
All generated sequences must pass through the full pipeline safety filters
before any nomination. The lab is the judge.
"""
from __future__ import annotations

import random

from openamp_foundry.features.physchem import AGG_HYDROPHOBIC as _AGG_HYDROPHOBIC

CANONICAL_AA = "ACDEFGHIKLMNPQRSTVWY"

# Conservative substitution groups: within-group swaps preserve physicochemical character
CONSERVATIVE_GROUPS: list[frozenset[str]] = [
    frozenset("KRH"),        # cationic
    frozenset("LIVAFM"),     # aliphatic/hydrophobic
    frozenset("FWY"),        # aromatic
    frozenset("STNQ"),       # polar/neutral
    frozenset("DE"),         # anionic
    frozenset("GP"),         # conformational (glycine, proline — treat conservatively)
    frozenset("C"),          # cysteine — singleton; substitutions restricted
]

# _AGG_HYDROPHOBIC is imported from physchem.py (single source of truth for the VILMFW residue set).


def _conservative_substitutes(aa: str) -> list[str]:
    """Return amino acids that can conservatively substitute for `aa`."""
    for group in CONSERVATIVE_GROUPS:
        if aa in group:
            return [a for a in sorted(group) if a != aa]
    return []


def _max_hydrophobic_run(sequence: str) -> int:
    """Return the length of the longest consecutive _AGG_HYDROPHOBIC run in sequence."""
    max_run = 0
    current = 0
    for aa in sequence:
        if aa in _AGG_HYDROPHOBIC:
            current += 1
            max_run = max(max_run, current)
        else:
            current = 0
    return max_run


def generate_single_substitution_variants(sequence: str) -> list[str]:
    """Generate all single-substitution conservative variants of a template.

    For each position, substitutes with each member of the same physicochemical group.
    Returns up to len(sequence) × (group_size - 1) variants.
    """
    variants = []
    for i, aa in enumerate(sequence):
        subs = _conservative_substitutes(aa)
        for sub in subs:
            new_seq = sequence[:i] + sub + sequence[i + 1:]
            variants.append(new_seq)
    return variants


def generate_double_substitution_variants(
    sequence: str,
    n_samples: int = 20,
    seed: int = 42,
) -> list[str]:
    """Sample random pairs of conservative positions and substitute both.

    Returns up to n_samples unique variants.
    """
    rng = random.Random(seed)
    substitutable = [
        (i, _conservative_substitutes(aa))
        for i, aa in enumerate(sequence)
        if _conservative_substitutes(aa)
    ]
    if len(substitutable) < 2:
        return []

    seen: set[str] = set()
    variants = []
    attempts = 0
    while len(variants) < n_samples and attempts < n_samples * 10:
        attempts += 1
        pos_a, subs_a = rng.choice(substitutable)
        pos_b, subs_b = rng.choice(substitutable)
        if pos_a == pos_b:
            continue
        sub_a = rng.choice(subs_a)
        sub_b = rng.choice(subs_b)
        seq = list(sequence)
        seq[pos_a] = sub_a
        seq[pos_b] = sub_b
        new_seq = "".join(seq)
        if new_seq not in seen:
            seen.add(new_seq)
            variants.append(new_seq)
    return variants


def generate_aggregation_safe_double_variants(
    sequence: str,
    n_samples: int = 20,
    seed: int = 42,
    max_run: int = 4,
) -> list[str]:
    """Like generate_double_substitution_variants but rejects variants with a
    consecutive _AGG_HYDROPHOBIC run >= max_run.

    Default max_run=4 matches the QC HYDROPHOBIC_RUN_RE threshold ([VILMFW]{4,})
    and the aggregation_propensity() run component in physchem.py. This prevents
    the generator from producing sequences that the synthesis scoring pipeline
    would penalise for on-resin aggregation.

    Returns up to n_samples unique aggregation-safe variants.
    """
    rng = random.Random(seed)
    substitutable = [
        (i, _conservative_substitutes(aa))
        for i, aa in enumerate(sequence)
        if _conservative_substitutes(aa)
    ]
    if len(substitutable) < 2:
        return []

    seen: set[str] = set()
    variants = []
    attempts = 0
    # Larger attempt budget: some hydrophobic seeds need many tries to find safe pairs.
    while len(variants) < n_samples and attempts < n_samples * 50:
        attempts += 1
        pos_a, subs_a = rng.choice(substitutable)
        pos_b, subs_b = rng.choice(substitutable)
        if pos_a == pos_b:
            continue
        sub_a = rng.choice(subs_a)
        sub_b = rng.choice(subs_b)
        seq_list = list(sequence)
        seq_list[pos_a] = sub_a
        seq_list[pos_b] = sub_b
        new_seq = "".join(seq_list)
        if _max_hydrophobic_run(new_seq) >= max_run:
            continue
        if new_seq not in seen:
            seen.add(new_seq)
            variants.append(new_seq)
    return variants


def generate_charge_enhanced_variants(
    sequence: str,
    n_samples: int = 10,
    seed: int = 42,
) -> list[str]:
    """Replace uncharged positions with K or R to boost predicted charge density.

    Targets positions occupied by non-charged hydrophilic residues (S, T, N, Q)
    and replaces with K (higher charge density → better activity likeness).

    Deprecated: generate_all_variants() now calls generate_balanced_charge_variants()
    which generates both K and R for each polar position. This function is retained
    for backward compatibility (used by existing tests and any external callers).
    """
    rng = random.Random(seed)
    targetable = [
        i for i, aa in enumerate(sequence) if aa in "STNQ"
    ]
    if not targetable:
        return []

    seen: set[str] = set()
    variants = []
    for i in targetable[:n_samples]:
        replacement = rng.choice(["K", "R"])
        new_seq = sequence[:i] + replacement + sequence[i + 1:]
        if new_seq not in seen:
            seen.add(new_seq)
            variants.append(new_seq)
    return variants


def generate_balanced_charge_variants(
    sequence: str,
    n_positions: int = 10,
) -> list[str]:
    """Generate both K and R replacements for each polar (S/T/N/Q) position.

    Unlike generate_charge_enhanced_variants(), which randomly picks K or R,
    this function generates one K and one R variant per targetable position.
    The scoring pipeline can then rank both options and select the better one
    based on GRAVY / selectivity_proxy trade-offs:
      - K (KD = -3.9): slightly less hydrophilic than R, slightly lower trypsin rate
      - R (KD = -4.5): more hydrophilic, marginally higher GRAVY improvement

    Args:
        n_positions: maximum number of polar positions to target. Returns up to
            2 × n_positions unique variants (one K variant and one R variant per position).
            Named n_positions (not n_samples) to avoid confusion with other generator
            functions where n_samples bounds the total output count directly.
    """
    targetable = [i for i, aa in enumerate(sequence) if aa in "STNQ"]
    if not targetable:
        return []

    seen: set[str] = set()
    variants = []
    for i in targetable[:n_positions]:
        for replacement in ("K", "R"):
            new_seq = sequence[:i] + replacement + sequence[i + 1:]
            if new_seq not in seen:
                seen.add(new_seq)
                variants.append(new_seq)
    return variants


def generate_all_variants(
    seed_sequence: str,
    n_double: int = 15,
    n_charge_enhance: int = 8,
    seed: int = 42,
) -> list[str]:
    """Generate all candidate variants for a template sequence.

    Combines single substitutions, aggregation-safe double substitutions, and
    balanced (K+R) charge-enhanced variants. Deduplicates and removes the seed.

    Double substitutions use generate_aggregation_safe_double_variants() to avoid
    creating hydrophobic runs ≥4 that would be penalised by synthesis scoring.
    Single substitutions are also filtered for the same threshold — a conservative swap
    of an adjacent residue can extend a near-threshold run into aggregation territory.
    Charge enhancements use generate_balanced_charge_variants() to produce both
    K and R options at each polar position, letting the scoring pipeline rank them.
    """
    variants: set[str] = set()
    # Single subs are filtered: a conservative A→L substitution adjacent to a run-of-3
    # can create run-of-4, which would be flagged by synthesis scoring and QC.
    variants.update(
        v for v in generate_single_substitution_variants(seed_sequence)
        if _max_hydrophobic_run(v) < 4
    )
    variants.update(generate_aggregation_safe_double_variants(seed_sequence, n_double, seed))
    variants.update(generate_balanced_charge_variants(seed_sequence, n_charge_enhance))
    variants.discard(seed_sequence)
    return sorted(variants)


def generate_candidate_pool(
    seed_sequences: list[str],
    seed_ids: list[str],
    n_double: int = 15,
    n_charge_enhance: int = 8,
    rng_seed: int = 42,
) -> list[dict[str, str]]:
    """Generate a candidate pool from multiple seed templates.

    Returns a list of dicts with 'id', 'sequence', 'source' fields.
    IDs are formatted as {seed_id}_VAR_{index:03d}.
    """
    candidates = []
    for seed_id, seed_seq in zip(seed_ids, seed_sequences):
        variants = generate_all_variants(seed_seq, n_double, n_charge_enhance, rng_seed)
        for idx, variant in enumerate(variants, start=1):
            candidates.append({
                "id": f"{seed_id}_VAR_{idx:03d}",
                "sequence": variant,
                "source": f"template_mutation_from_{seed_id}",
            })
    return candidates
