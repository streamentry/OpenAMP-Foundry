from __future__ import annotations


def classify_structural_class(sequence: str, features: dict) -> str:
    """Classify a peptide into the mutually exclusive benchmark structural class.

    This mirrors the v0.5.37 per-family benchmark classes so selection code can
    compensate for measured charge/helical bias without re-defining categories.
    """
    seq = sequence.upper()
    pro_fraction = features.get("proline_fraction", 0.0) or 0.0
    length = features.get("length", len(seq)) or len(seq)
    net_charge = features.get("net_charge_ph74", 0.0) or 0.0

    if seq.count("C") >= 2:
        return "cysteine_rich"
    if length <= 12:
        return "short"
    if pro_fraction >= 0.15:
        return "proline_rich"
    if net_charge >= 4.0:
        return "highly_cationic"
    if net_charge >= 2.0:
        return "moderately_cationic"
    return "low_charge"


STRUCTURAL_CLASS_ORDER = (
    "cysteine_rich",
    "proline_rich",
    "short",
    "highly_cationic",
    "moderately_cationic",
    "low_charge",
)
