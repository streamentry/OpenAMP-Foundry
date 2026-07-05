"""Charge-matched decoy benchmark."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from openamp_foundry.benchmark.charge_matched import run_charge_matched_benchmark  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark pipeline against charge-matched decoys.")
    parser.add_argument("--amp-csv", default="examples/validation/known_amps_500.csv")
    parser.add_argument("--decoy-csv", default="examples/validation/random_background_500.csv")
    parser.add_argument("--config", default="configs/pipeline.yaml")
    parser.add_argument("--out", default="outputs/benchmark_charge_matched.json")
    args = parser.parse_args(argv)

    result = run_charge_matched_benchmark(args.amp_csv, args.decoy_csv, args.config)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print("=== Charge-Matched Decoy Benchmark ===")
    print(f"n: {result['n_positives']} positives vs {result['n_matched_decoys']} matched decoys")
    print(f"mean |charge density delta|: {result['mean_abs_charge_density_delta']:.4f}")
    print(f"pipeline AUROC: {result['pipeline_auroc']:.4f}")
    print(f"charge-density AUROC: {result['charge_density_auroc']:.4f}")
    print(f"pipeline - charge-density: {result['pipeline_minus_charge_density']:.4f}")
    print(result["interpretation"])
    print(f"Saved: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
