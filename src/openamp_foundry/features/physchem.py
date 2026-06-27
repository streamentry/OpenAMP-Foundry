from __future__ import annotations

from collections import Counter

HYDROPHOBIC = set("AILMFWVY")
POSITIVE = set("KRH")
NEGATIVE = set("DE")
AROMATIC = set("FWY")
CYS = "C"


def net_charge_proxy(sequence: str) -> int:
    return sum(1 for aa in sequence if aa in POSITIVE) - sum(1 for aa in sequence if aa in NEGATIVE)


def fraction(sequence: str, alphabet: set[str]) -> float:
    if not sequence:
        return 0.0
    return sum(1 for aa in sequence if aa in alphabet) / len(sequence)


def longest_repeat_run(sequence: str) -> int:
    if not sequence:
        return 0
    best = 1
    current = 1
    for prev, aa in zip(sequence, sequence[1:]):
        if aa == prev:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def compute_features(sequence: str) -> dict[str, float | int | dict[str, int]]:
    counts = Counter(sequence)
    length = len(sequence)
    charge = net_charge_proxy(sequence)
    hydrophobic_fraction = fraction(sequence, HYDROPHOBIC)
    aromatic_fraction = fraction(sequence, AROMATIC)
    cys_fraction = counts.get(CYS, 0) / length if length else 0.0
    gly_fraction = counts.get("G", 0) / length if length else 0.0
    pro_fraction = counts.get("P", 0) / length if length else 0.0
    repeat_run = longest_repeat_run(sequence)
    return {
        "length": length,
        "net_charge_proxy": charge,
        "charge_density": charge / length if length else 0.0,
        "hydrophobic_fraction": round(hydrophobic_fraction, 4),
        "aromatic_fraction": round(aromatic_fraction, 4),
        "cysteine_fraction": round(cys_fraction, 4),
        "glycine_fraction": round(gly_fraction, 4),
        "proline_fraction": round(pro_fraction, 4),
        "longest_repeat_run": repeat_run,
        "residue_counts": dict(sorted(counts.items())),
    }
