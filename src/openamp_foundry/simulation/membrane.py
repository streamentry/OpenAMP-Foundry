"""Membrane interaction proxy for virtual assay layer.

Coarse-grained membrane binding energy using Wimley-White experimental
hydrophobicity scales. Models two membrane types separately:
- Bacterial (anionic): Wimley-White interfacial scale
- Mammalian / RBC (zwitterionic): Wimley-White octanol scale

Reference: Wimley & White (1996) Nat Struct Biol 3:842-848.
"""

from .interfaces import EmulatorBaseline, SimulationResult, VirtualAssayProxy

# Wimley-White interfacial hydrophobicity scale (kcal/mol).
# Water-to-membrane-interface transfer free energy.
# More negative = stronger membrane binding.
# Source: Wimley & White (1996) Nat Struct Biol 3:842-848, Table 1.
_INTERFACIAL: dict[str, float] = {
    "A": -0.04, "C": -0.60, "D": 0.83, "E": 0.64,
    "F": -1.57, "G": -0.10, "H": 0.12, "I": -1.35,
    "K": 0.99, "L": -1.22, "M": -1.02, "N": 0.27,
    "P": -0.22, "Q": 0.11, "R": 1.18, "S": -0.10,
    "T": -0.18, "V": -1.06, "W": -2.74, "Y": -1.30,
}

# Wimley-White octanol scale (kcal/mol).
# Water-to-octanol transfer free energy. Models insertion into
# hydrophobic core (zwitterionic / cholesterol-containing membranes).
# Source: Wimley & White (1996) Nat Struct Biol 3:842-848, Table 1.
_OCTANOL: dict[str, float] = {
    "A": 0.40, "C": -0.13, "D": 3.02, "E": 2.68,
    "F": -1.49, "G": 1.01, "H": 0.87, "I": -1.68,
    "K": 2.71, "L": -1.60, "M": -0.96, "N": 1.76,
    "P": 0.87, "Q": 1.56, "R": 2.89, "S": 0.84,
    "T": 0.52, "V": -1.35, "W": -3.08, "Y": -0.82,
}


def _mean_scale(sequence: str, scale: dict[str, float]) -> float:
    if not sequence:
        return 0.0
    total = 0.0
    count = 0
    for aa in sequence.upper():
        if aa in scale:
            total += scale[aa]
            count += 1
    return total / count if count else 0.0


def _normalize_negative(value: float, lo: float = -2.0, hi: float = 1.0) -> float:
    """Normalize a negative-scale value to [0, 1] where 1 = strongest binding.

    Wimley-White scales are in kcal/mol: negative = favorable (binds),
    positive = unfavorable.  This maps from [lo, hi] interval to [0, 1].
    Values outside the range are clamped.
    """
    if value <= lo:
        return 1.0
    if value >= hi:
        return 0.0
    return (hi - value) / (hi - lo)


def _normalize_positive(value: float, lo: float = 0.0, hi: float = 1.5) -> float:
    """Normalize a positive-scale value to [0, 1] where 1 = strongest binding.

    The octanol scale has positive values for most residues (unfavorable).
    """
    if value <= lo:
        return 1.0
    if value >= hi:
        return 0.0
    return (hi - value) / (hi - lo)


def _selectivity_ratio(bacterial_score: float, mammalian_score: float) -> float:
    """Ratio of bacterial to mammalian membrane binding.

    > 1.0 = selective (prefers bacterial over mammalian).
    < 1.0 = hemolytic risk (prefers mammalian or binds both equally).
    """
    if mammalian_score <= 0.0:
        return 2.0
    return min(bacterial_score / mammalian_score, 2.0)


def _uncertainty(sequence: str, bacterial_score: float, mammalian_score: float) -> float:
    """Uncertainty estimate for membrane proxy scores.

    Higher uncertainty when:
    - Sequence is short (< 12 AA): insufficient residues for amphipathic pattern
    - Binding scores are mid-range (0.3-0.7): signal is weak
    """
    length = len(sequence) if sequence else 0
    length_uncertainty = max(0.0, 1.0 - length / 20.0) if length < 20 else 0.0
    score_mid = abs(bacterial_score - 0.5) + abs(mammalian_score - 0.5)
    score_uncertainty = max(0.0, 0.5 - score_mid / 2.0)
    return min(round((length_uncertainty + score_uncertainty) / 2.0, 4), 1.0)


class BomanBaseline(EmulatorBaseline):
    """Boman index as a cheap baseline heuristic for membrane binding."""

    def evaluate(self, sequence: str) -> float:
        from openamp_foundry.scoring.boman import boman_index
        raw = boman_index(sequence)
        return max(0.0, min(raw / 5.0, 1.0))


class MembraneProxy(VirtualAssayProxy):
    """Coarse-grained membrane binding energy proxy.

    Models bacterial membrane binding (interfacial scale) and mammalian
    membrane binding (octanol scale) separately. Returns a selectivity
    ratio and uncertainty estimate.
    """

    def __init__(self, version: str = "0.1.0") -> None:
        self._version = version

    def simulate(self, sequence: str) -> SimulationResult:
        mean_if = _mean_scale(sequence, _INTERFACIAL)
        mean_oct = _mean_scale(sequence, _OCTANOL)

        bacterial_score = _normalize_negative(mean_if)
        mammalian_score = _normalize_positive(mean_oct)

        from openamp_foundry.features.physchem import hydrophobic_moment
        moment = hydrophobic_moment(sequence)
        amphipathic_bonus = min(moment / 0.8, 1.0)

        bacterial_combined = round((bacterial_score * 0.7 + amphipathic_bonus * 0.3), 4)
        mammalian_combined = round((mammalian_score * 0.7 + amphipathic_bonus * 0.3), 4)
        sel_ratio = round(_selectivity_ratio(bacterial_combined, mammalian_combined), 4)
        uncertainty = _uncertainty(sequence, bacterial_combined, mammalian_combined)

        return SimulationResult(
            module="membrane_proxy",
            version=self._version,
            scope=[
                "bacterial_membrane_binding",
                "mammalian_membrane_binding",
                "selectivity_ratio",
            ],
            scores={
                "bacterial_binding": bacterial_combined,
                "mammalian_binding": mammalian_combined,
                "selectivity_ratio": sel_ratio,
                "raw_interfacial_mean": round(mean_if, 4),
                "raw_octanol_mean": round(mean_oct, 4),
                "hydrophobic_moment": round(moment, 4),
            },
            uncertainty=uncertainty,
            calibration_set=None,
            validated_against=[],
            notes=[
                "Coarse-grained proxy using Wimley-White interfacial and octanol scales.",
                "Bacterial score: 70% interfacial + 30% hydrophobic moment bonus.",
                "Mammalian score: 70% octanol + 30% hydrophobic moment bonus.",
                "Uncertainty > 0.5 = experimental, must not affect selection.",
                "Not validated against any wet-lab membrane binding data.",
            ],
        )

    def get_baseline(self) -> EmulatorBaseline:
        return BomanBaseline()

    @property
    def cheapest_baseline_description(self) -> str:
        return "Boman index (heuristic AMP activity proxy based on amino acid composition)"
