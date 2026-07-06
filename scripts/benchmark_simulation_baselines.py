"""Simulation cheap-baseline benchmark: does each simulation signal beat its cheapest heuristic?

Compares each simulation module output against its cheapest meaningful
baseline on the within-AMP hemolysis detection task.

Simulation signal → cheap baseline:
- bacterial_binding → mean Eisenberg hydrophobicity
- selectivity_ratio → selectivity_proxy (charge + GRAVY)
- helix_weight → helix_propensity_score (mean Chou-Fasman Pα)
- non_helical → proline_fraction

Any module with delta ≤ 0 against its baseline is flagged as NO_IMPROVEMENT
and must remain permanently experimental.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from openamp_foundry.features.physchem import (
    _HYDROPHOBICITY,
    compute_features,
    fraction,
    helix_propensity_score,
    selectivity_proxy,
)
from openamp_foundry.simulation.membrane import MembraneProxy
from openamp_foundry.simulation.structure import StructureProxy

HYDROPHOBIC = set("AILMFWVY")


def _auroc(scores_pos: list[float], scores_neg: list[float]) -> float:
    n_p = len(scores_pos)
    n_n = len(scores_neg)
    if n_p == 0 or n_n == 0:
        return 0.5
    better = 0
    ties = 0
    for sp in scores_pos:
        for sn in scores_neg:
            if sp > sn:
                better += 1
            elif sp == sn:
                ties += 1
    total = n_p * n_n
    return (better + 0.5 * ties) / total if total else 0.5


def _mean_eisenberg(sequence: str) -> float:
    if not sequence:
        return 0.0
    total = 0.0
    count = 0
    for aa in sequence.upper():
        if aa in _HYDROPHOBICITY:
            total += _HYDROPHOBICITY[aa]
            count += 1
    return total / count if count else 0.0


def _detection_auroc(hemo_vals: list[float], sel_vals: list[float], invert: bool = False) -> float:
    raw = _auroc(hemo_vals, sel_vals)
    return 1.0 - raw if invert else raw


def run_simulation_baselines(
    hemolysis_csv: str = "examples/validation/hemolysis_reference.csv",
) -> dict:
    """Compare each simulation signal against its cheap heuristic baseline.

    Returns per-signal deltas and verdict.
    """
    csv_p = Path(hemolysis_csv)
    if not csv_p.exists():
        return {"error": f"Hemolysis CSV not found: {hemolysis_csv}"}

    hemolytic: list[tuple[str, str]] = []
    selective: list[tuple[str, str]] = []
    with csv_p.open("r", newline="") as f:
        for row in csv.DictReader(f):
            cls = row.get("hemolysis_class", "").strip().upper()
            seq = row.get("sequence", "").strip()
            cid = row.get("id", "unknown")
            if not seq:
                continue
            if cls == "HEMOLYTIC":
                hemolytic.append((cid, seq))
            elif cls == "SELECTIVE":
                selective.append((cid, seq))

    if len(hemolytic) < 3 or len(selective) < 3:
        return {"error": f"Not enough sequences: {len(hemolytic)} hemolytic, {len(selective)} selective"}

    membrane = MembraneProxy()
    structure = StructureProxy()

    hemo_scores: dict[str, list[float]] = {
        "bacterial_binding": [],
        "selectivity_ratio": [],
        "helix_weight": [],
        "non_helical": [],
        "mean_eisenberg": [],
        "selectivity_proxy": [],
        "helix_propensity": [],
        "proline_fraction": [],
    }
    sel_scores: dict[str, list[float]] = {k: [] for k in hemo_scores}

    def _score_and_record(seqs: list[tuple[str, str]], target: dict[str, list[float]]) -> None:
        for cid, seq in seqs:
            feats = compute_features(seq)
            mem_result = membrane.simulate(seq)
            struct_result = structure.simulate(seq)
            target["bacterial_binding"].append(mem_result.scores.get("bacterial_binding", 0.0))
            target["selectivity_ratio"].append(mem_result.scores.get("selectivity_ratio", 1.0))
            target["helix_weight"].append(struct_result.scores.get("helix_weight", 0.33))
            target["non_helical"].append(struct_result.scores.get("non_helical", 0.0))
            target["mean_eisenberg"].append(_mean_eisenberg(seq))
            net_charge = feats.get("net_charge_ph74", 0.0)
            gravy = feats.get("gravy", 0.0)
            target["selectivity_proxy"].append(selectivity_proxy(net_charge, gravy))
            target["helix_propensity"].append(helix_propensity_score(seq))
            target["proline_fraction"].append(fraction(seq, {"P"}))

    _score_and_record(hemolytic, hemo_scores)
    _score_and_record(selective, sel_scores)

    # Compute raw AUROCs (no direction inversion).
    # For each score we report: auroc_raw = P(hemolytic_score > selective_score).
    # If auroc_raw > 0.5: hemolytic tends to score HIGHER.
    # If auroc_raw < 0.5: hemolytic tends to score LOWER.
    # The comparison is symmetric: both signal and baseline use the same metric.
    hemo_raw = lambda k: round(_auroc(hemo_scores[k], sel_scores[k]), 4)

    pairs = [
        ("bacterial_binding", "mean_eisenberg"),
        ("selectivity_ratio", "selectivity_proxy"),
        ("helix_weight", "helix_propensity"),
        ("non_helical", "proline_fraction"),
    ]

    per_signal = {}
    for signal, baseline in pairs:
        sig_auroc = hemo_raw(signal)
        base_auroc = hemo_raw(baseline)
        delta = round(sig_auroc - base_auroc, 4)
        verdict = "NO_IMPROVEMENT" if delta <= 0 else "IMPROVEMENT"
        per_signal[signal] = {
            "signal_auroc": sig_auroc,
            "baseline_auroc": base_auroc,
            "baseline_name": baseline,
            "delta": delta,
            "verdict": verdict,
            "note": (
                f"auroc > 0.5 = hemolytic AMPs score higher. "
                f"Signal={sig_auroc:.4f}, baseline={base_auroc:.4f}, delta={delta:+.4f}"
            ),
        }

    n_improved = sum(1 for v in per_signal.values() if v["verdict"] == "IMPROVEMENT")
    n_total = len(per_signal)

    return {
        "benchmark": "simulation_baselines",
        "n_hemolytic": len(hemolytic),
        "n_selective": len(selective),
        "results": per_signal,
        "summary": {
            "n_improved": n_improved,
            "n_total": n_total,
            "all_blocked": n_improved == 0,
        },
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Simulation cheap-baseline benchmark")
    parser.add_argument("--hemolysis-csv", default="examples/validation/hemolysis_reference.csv")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    result = run_simulation_baselines(hemolysis_csv=args.hemolysis_csv)
    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2) + "\n")

    summary = result["summary"]
    print(f"\nResults: {summary['n_improved']}/{summary['n_total']} signals improve over baseline")
    for name, data in result["results"].items():
        print(f"  {name}: signal={data['signal_auroc']:.4f} baseline={data['baseline_auroc']:.4f} "
              f"delta={data['delta']:+.4f} → {data['verdict']}")

    if summary["all_blocked"]:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
