"""Physicochemical feature extraction for OpenAMP Foundry.

Single entry point: `compute_features(sequence)` returns a flat dict
of length, charge, hydrophobicity, helix/fold propensities, and other
descriptors consumed by every scorer.
"""

from openamp_foundry.features.dipeptide import (
    ALL_DIPEPTIDES,
    dipeptide_frequencies,
    dipeptide_order_score,
    get_reference_log_odds,
)
from openamp_foundry.features.physchem import (
    compute_features,
    fraction,
    helix_propensity_score,
    helix_wheel_faces,
    hydrophobic_moment,
    longest_repeat_run,
    max_windowed_hydrophobic_moment,
    net_charge_at_ph74,
    net_charge_proxy,
)

__all__ = [
    "ALL_DIPEPTIDES",
    "compute_features",
    "dipeptide_frequencies",
    "dipeptide_order_score",
    "fraction",
    "get_reference_log_odds",
    "helix_propensity_score",
    "helix_wheel_faces",
    "hydrophobic_moment",
    "longest_repeat_run",
    "max_windowed_hydrophobic_moment",
    "net_charge_at_ph74",
    "net_charge_proxy",
]
