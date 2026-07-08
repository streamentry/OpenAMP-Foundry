"""Structure ensemble proxy for virtual assay layer.

Computes 3-state secondary structure propensities (helix/sheet/coil)
using Chou-Fasman parameters. Generates normalized ensemble weights
and flags non-helical candidates where the helic-centric activity
scorer is unreliable.

Reference: Chou PY & Fasman GD (1974) Biochemistry 13:222-245.
"""

from .interfaces import EmulatorBaseline, SimulationResult, VirtualAssayProxy

# Chou-Fasman alpha-helix propensity parameters (Palpha).
# Source: Chou & Fasman (1974) Biochemistry 13:222-245, Table IV.
# Values > 1.0 are helix-forming; < 0.75 helix-breaking.
_HELIX: dict[str, float] = {
    "A": 1.42, "R": 0.98, "N": 0.67, "D": 1.01, "C": 0.70,
    "Q": 1.11, "E": 1.51, "G": 0.57, "H": 1.00, "I": 1.08,
    "L": 1.21, "K": 1.16, "M": 1.45, "F": 1.13, "P": 0.57,
    "S": 0.77, "T": 0.83, "W": 1.08, "Y": 0.69, "V": 1.06,
}

# Chou-Fasman beta-sheet propensity parameters (Pbeta).
_SHEET: dict[str, float] = {
    "A": 0.83, "R": 0.93, "N": 0.89, "D": 0.54, "C": 1.19,
    "Q": 1.10, "E": 0.37, "G": 0.75, "H": 0.87, "I": 1.60,
    "L": 1.30, "K": 0.74, "M": 1.05, "F": 1.38, "P": 0.55,
    "S": 0.75, "T": 1.19, "W": 1.37, "Y": 1.47, "V": 1.70,
}

# Chou-Fasman coil / turn propensity parameters (Pt / Pc).
_COIL: dict[str, float] = {
    "A": 0.66, "R": 0.95, "N": 1.56, "D": 1.46, "C": 0.70,
    "Q": 0.98, "E": 0.74, "G": 1.56, "H": 0.95, "I": 0.47,
    "L": 0.59, "K": 1.01, "M": 0.60, "F": 0.60, "P": 1.52,
    "S": 1.43, "T": 0.96, "W": 0.96, "Y": 1.14, "V": 0.50,
}


def _mean_propensity(sequence: str, scale: dict[str, float]) -> float:
    if not sequence:
        return 1.0
    total = 0.0
    count = 0
    for aa in sequence.upper():
        if aa in scale:
            total += scale[aa]
            count += 1
    return total / count if count else 1.0


def _normalize_weights(h: float, e: float, c: float) -> tuple[float, float, float]:
    """Normalize three propensity scores to sum to 1.0.

    Converts Chou-Fasman propensities (centered at 1.0) to fractional
    ensemble weights by taking their relative magnitudes.
    """
    total = h + e + c
    if total <= 0.0:
        return (0.0, 0.0, 0.0)
    return (h / total, e / total, c / total)


def _dominant_state(helix: float, sheet: float, coil: float) -> str:
    """Return 'helix', 'sheet', or 'coil' as the predicted dominant state."""
    if helix >= sheet and helix >= coil:
        return "helix"
    if sheet >= coil:
        return "sheet"
    return "coil"


def _is_non_helical(dominant: str, helix_weight: float) -> bool:
    """Return True if the candidate is likely non-helical.

    Non-helical means the dominant state is NOT helix, or helix
    weight is below 0.33 (indifferent / ambiguous).
    """
    return dominant != "helix" or helix_weight < 0.33


def _uncertainty(sequence: str) -> float:
    """Uncertainty estimate for structure predictions.

    Higher uncertainty when:
    - Sequence is short (< 12 AA): insufficient residues for pattern
    - Sequence is very long (> 40 AA): Chou-Fasman less reliable for multi-domain
    """
    length = len(sequence) if sequence else 0
    if length == 0:
        return 1.0
    if length < 12:
        return round(1.0 - length / 12.0, 4)
    if length > 40:
        return round(min((length - 40) / 40.0, 1.0), 4)
    return 0.15  # baseline uncertainty for well-behaved sequences


class HelicityBaseline(EmulatorBaseline):
    """Mean Chou-Fasman helix propensity as a cheap baseline."""

    def evaluate(self, sequence: str) -> float:
        return _mean_propensity(sequence, _HELIX)


class StructureProxy(VirtualAssayProxy):
    """Secondary structure ensemble proxy.

    Predicts helix/sheet/coil propensities from sequence using
    Chou-Fasman parameters. Flags non-helical candidates where
    the helic-centric activity scorer is unreliable.
    """

    def __init__(self, version: str = "0.1.0") -> None:
        self._version = version

    def simulate(self, sequence: str) -> SimulationResult:
        h = _mean_propensity(sequence, _HELIX)
        e = _mean_propensity(sequence, _SHEET)
        c = _mean_propensity(sequence, _COIL)

        w_h, w_e, w_c = _normalize_weights(h, e, c)
        dominant = _dominant_state(w_h, w_e, w_c)
        non_helical = _is_non_helical(dominant, w_h)
        uncertainty = _uncertainty(sequence)

        return SimulationResult(
            module="structure_proxy",
            version=self._version,
            scope=[
                "secondary_structure_prediction",
                "non_helical_flag",
            ],
            scores={
                "helix_weight": round(w_h, 4),
                "sheet_weight": round(w_e, 4),
                "coil_weight": round(w_c, 4),
                "helix_propensity_raw": round(h, 4),
                "sheet_propensity_raw": round(e, 4),
                "coil_propensity_raw": round(c, 4),
                "non_helical": 1.0 if non_helical else 0.0,
            },
            uncertainty=uncertainty,
            calibration_set=None,
            validated_against=[],
            notes=[
                "3-state Chou-Fasman secondary structure prediction.",
                f"Dominant predicted state: {dominant}.",
                "Non-helical flag: True if dominant != helix or helix_weight < 0.33.",
                "Not validated against any experimental structure data.",
                "Uncertainty > 0.5 = experimental, must not affect selection.",
            ],
        )

    def get_baseline(self) -> EmulatorBaseline:
        return HelicityBaseline()

    @property
    def cheapest_baseline_description(self) -> str:
        return "sequence length alone (longer sequences have higher helix probability by chance)"
