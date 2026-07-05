"""Dipeptide frequency features for sequence-order awareness.

The pipeline's existing features are predominantly composition-based (charge,
hydrophobicity, aromatic fraction, etc.) and don't capture SEQUENCE ORDER.
Dipeptide frequencies (the 400 possible AA×AA pairs) capture local sequence
order information that survives sequence scrambling.

Usage:
    freqs = dipeptide_frequencies("ACDEF")
    score = dipeptide_order_score("ACDEF", log_odds)

The log-odds reference is pre-computed from the expanded 500-AMP benchmark
(real AMPs vs scrambled versions) and stored as a module-level constant.
"""

from __future__ import annotations

import json
from pathlib import Path

AMINO_ACIDS = list("ACDEFGHIKLMNPQRSTVWY")
ALL_DIPEPTIDES = [a + b for a in AMINO_ACIDS for b in AMINO_ACIDS]  # 400

# Reference log-odds: ln(mean_real / mean_scrambled) for each dipeptide,
# computed from 500 AMPs vs scrambled versions (seed=20260705).
# Pre-computed to avoid data leakage and ensure reproducibility.
_LOG_ODDS_PATH = Path(__file__).parent / "dipeptide_log_odds.json"


def dipeptide_frequencies(sequence: str) -> dict[str, float]:
    """Compute normalized dipeptide frequencies.

    Returns a dict of 400 entries, each the fraction of adjacent pairs
    in the sequence that match that dipeptide. Sequences < 2 AA return
    all zeros.
    """
    freqs = {d: 0.0 for d in ALL_DIPEPTIDES}
    n = len(sequence)
    if n < 2:
        return freqs
    for i in range(n - 1):
        d = sequence[i : i + 2]
        if d in freqs:
            freqs[d] += 1.0
    n_pairs = n - 1
    return {d: round(c / n_pairs, 6) for d, c in freqs.items()}


def _load_log_odds() -> dict[str, float]:
    if _LOG_ODDS_PATH.exists():
        with open(_LOG_ODDS_PATH) as f:
            return json.load(f)
    return {}


# Module-level cache
_REFERENCE_LOG_ODDS: dict[str, float] | None = None


def get_reference_log_odds() -> dict[str, float]:
    global _REFERENCE_LOG_ODDS
    if _REFERENCE_LOG_ODDS is None:
        _REFERENCE_LOG_ODDS = _load_log_odds()
    return _REFERENCE_LOG_ODDS


def dipeptide_order_score(
    sequence: str,
    log_odds: dict[str, float] | None = None,
) -> float:
    """Score a sequence by how AMP-like its dipeptide composition is.

    Higher score = more AMP-like dipeptide patterns.
    Score is a weighted sum of dipeptide frequencies × log-odds,
    normalized to [0, 1].

    If log_odds is None, uses the pre-computed reference.
    """
    if log_odds is None:
        log_odds = get_reference_log_odds()
    if not log_odds:
        return 0.5  # No reference — neutral score

    freqs = dipeptide_frequencies(sequence)
    raw = sum(freqs.get(d, 0.0) * log_odds.get(d, 0.0) for d in ALL_DIPEPTIDES)

    # Normalise: clamp to a reasonable range then map to [0, 1]
    # The raw score range on reference data is approx [-0.3, 0.3]
    normalised = max(0.0, min(1.0, (raw + 0.5) / 1.0))
    return round(normalised, 4)
