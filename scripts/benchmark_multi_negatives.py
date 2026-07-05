#!/usr/bin/env python3
"""Multi-negative-set benchmark — run AUROC against multiple decoy distributions.

Usage:
  python scripts/benchmark_multi_negatives.py [--out report.json]
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from openamp_foundry.benchmark.retrospective import run_retrospective_benchmark  # noqa: E402

KNOWN_AMPS = "examples/validation/known_amps.csv"
CONFIG = "configs/pipeline.yaml"


def load_amp_sequences(path: str | Path) -> list[dict]:
    amps = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            amps.append(row)
    return amps


def write_decoy_csv(rows: list[dict], path: str | Path) -> Path:
    p = Path(path)
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "sequence", "family", "reference", "label"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


UNIPROT_FREQ = {
    "A": 0.0826, "R": 0.0553, "N": 0.0406, "D": 0.0546, "C": 0.0138,
    "Q": 0.0393, "E": 0.0675, "G": 0.0708, "H": 0.0227, "I": 0.0594,
    "L": 0.0965, "K": 0.0581, "M": 0.0242, "F": 0.0386, "P": 0.0474,
    "S": 0.0656, "T": 0.0534, "W": 0.0109, "Y": 0.0292, "V": 0.0687,
}
UNIFORM_FREQ = {aa: 1.0 / 20 for aa in UNIPROT_FREQ}
AA_TYPES = list(UNIPROT_FREQ.keys())

RNG_SEED = 1729


def generate_uniform_decoys(amps: list[dict], rng: random.Random) -> list[dict]:
    decoys = []
    for i, amp in enumerate(amps):
        seq_len = len(amp["sequence"])
        seq = "".join(rng.choices(AA_TYPES, k=seq_len))
        decoys.append({
            "id": f"UNIFORM-DECOY-{i+1:04d}",
            "sequence": seq,
            "family": "uniform",
            "reference": "synthetic_uniform",
            "label": "0",
        })
    return decoys


def generate_reverse_decoys(amps: list[dict]) -> list[dict]:
    decoys = []
    for i, amp in enumerate(amps):
        seq = amp["sequence"][::-1]
        decoys.append({
            "id": f"REVERSE-DECOY-{i+1:04d}",
            "sequence": seq,
            "family": "reverse",
            "reference": amp.get("id", "UNKNOWN"),
            "label": "0",
        })
    return decoys


def generate_shuffled_decoys(amps: list[dict], rng: random.Random) -> list[dict]:
    decoys = []
    for i, amp in enumerate(amps):
        chars = list(amp["sequence"])
        rng.shuffle(chars)
        seq = "".join(chars)
        decoys.append({
            "id": f"SHUFFLED-DECOY-{i+1:04d}",
            "sequence": seq,
            "family": "shuffled",
            "reference": amp.get("id", "UNKNOWN"),
            "label": "0",
        })
    return decoys


def run_benchmark(amp_csv: str | Path, decoy_csv: str | Path, label: str) -> dict:
    result = run_retrospective_benchmark(
        amp_csv=amp_csv,
        decoy_csv=decoy_csv,
        config_path=CONFIG,
        n_bootstrap=200,
    )
    return {
        "negative_set": label,
        "auroc": result["auroc"],
        "auroc_ci95_lo": result["auroc_ci95_lo"],
        "auroc_ci95_hi": result["auroc_ci95_hi"],
        "auprc": result["auprc"],
        "n_positives": result["n_positives"],
        "n_negatives": result["n_negatives"],
        "interpretation": result["interpretation"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Multi-negative-set benchmark — run AUROC against multiple decoy distributions."
    )
    parser.add_argument(
        "--out", default=None, help="Path to write JSON report"
    )
    parser.add_argument(
        "--amp-csv", default=KNOWN_AMPS, help="Path to known AMPs CSV"
    )
    args = parser.parse_args(argv)

    amps = load_amp_sequences(args.amp_csv)
    rng = random.Random(RNG_SEED)

    results = []

    # 1. Swiss-Prot background (existing file)
    results.append(run_benchmark(
        args.amp_csv, "examples/validation/random_background.csv",
        "swissprot_background",
    ))

    # 2. Uniform random composition
    decoys = generate_uniform_decoys(amps, rng)
    tmp = write_decoy_csv(decoys, "/tmp/uniform_decoys.csv")
    results.append(run_benchmark(args.amp_csv, tmp, "uniform_random"))

    # 3. Reverse sequences
    decoys = generate_reverse_decoys(amps)
    tmp = write_decoy_csv(decoys, "/tmp/reverse_decoys.csv")
    results.append(run_benchmark(args.amp_csv, tmp, "reverse"))

    # 4. Shuffled sequences
    decoys = generate_shuffled_decoys(amps, rng)
    tmp = write_decoy_csv(decoys, "/tmp/shuffled_decoys.csv")
    results.append(run_benchmark(args.amp_csv, tmp, "shuffled"))

    # Report
    aurocs = [r["auroc"] for r in results]
    min_auroc = min(aurocs)
    max_auroc = max(aurocs)
    spread = max_auroc - min_auroc

    # Gate: independent-composition sets (swissprot, uniform) must stay > 0.70
    indep_aurocs = [r["auroc"] for r in results if r["negative_set"] in ("swissprot_background", "uniform_random")]
    composition_aurocs = [r["auroc"] for r in results if r["negative_set"] in ("reverse", "shuffled")]

    all_indep_above_70 = all(a >= 0.70 for a in indep_aurocs)
    min_indep = min(indep_aurocs)
    min_comp = min(composition_aurocs)

    interpretation_note = (
        f"Composition-independent sets (swissprot, uniform): AUROC range "
        f"{min(indep_aurocs):.4f}–{max(indep_aurocs):.4f}. "
        f"Composition-preserving sets (reverse, shuffled): AUROC range "
        f"{min(composition_aurocs):.4f}–{max(composition_aurocs):.4f}. "
        f"The near-random performance on reverse/shuffled decoys is expected: "
        f"the pipeline's discriminative power is largely composition-driven."
    )

    report = {
        "benchmark": "multi_negative_set",
        "n_amps": len(amps),
        "n_sets": len(results),
        "min_auroc": round(min_auroc, 4),
        "max_auroc": round(max_auroc, 4),
        "spread": round(spread, 4),
        "min_independent_composition_auroc": round(min_indep, 4),
        "min_matched_composition_auroc": round(min_comp, 4),
        "all_independent_sets_above_0_70": all_indep_above_70,
        "results": results,
        "interpretation": interpretation_note,
    }

    print(json.dumps(report, indent=2))

    if args.out:
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Gate: independent-composition sets must stay above 0.70
    # (The reverse/shuffled sets are expected to be near-random — that is an
    #  honest finding we document, not a gate failure mode.)
    if not all_indep_above_70:
        print(f"\nFAIL: Independent-composition set AUROC {min_indep:.4f} below 0.70")
        return 1
    print(f"\nPASS: All independent-composition sets > 0.70 (min={min_indep:.4f})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
