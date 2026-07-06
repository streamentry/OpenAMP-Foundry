"""Phase 3 candidate generation script.

Reads seed sequences from examples/sequences/amp_seeds.csv, applies conservative
substitution mutations, and writes the candidate pool to
examples/sequences/phase3_pool.csv.

Usage:
    python scripts/generate_phase3_batch.py [--seeds PATH] [--out PATH] [--seed INT]

This is a toy mutation explorer. Generated candidates must pass through the full
pipeline before any selection. The lab is the judge of activity.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from openamp_foundry.generators.template_mutator import generate_candidate_pool


def load_seeds(path: Path) -> tuple[list[str], list[str]]:
    seed_ids: list[str] = []
    seed_seqs: list[str] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            seed_ids.append(row["id"])
            seed_seqs.append(row["sequence"].strip().upper())
    return seed_ids, seed_seqs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Phase 3 candidate pool")
    parser.add_argument(
        "--seeds",
        default="examples/sequences/amp_seeds.csv",
        help="Seed sequences CSV (columns: id, sequence, source)",
    )
    parser.add_argument(
        "--out",
        default="examples/sequences/phase3_pool.csv",
        help="Output pool CSV path",
    )
    parser.add_argument(
        "--n-double",
        type=int,
        default=25,
        help="Number of double substitution variants per seed (default: 25)",
    )
    parser.add_argument(
        "--n-charge",
        type=int,
        default=12,
        help="Number of charge-enhanced variants per seed (default: 12)",
    )
    parser.add_argument(
        "--rng-seed",
        type=int,
        default=2024,
        help="RNG seed for reproducibility (default: 2024)",
    )
    args = parser.parse_args(argv)

    seeds_path = Path(args.seeds)
    if not seeds_path.exists():
        print(f"ERROR: seeds file not found: {seeds_path}", file=sys.stderr)
        return 1

    seed_ids, seed_seqs = load_seeds(seeds_path)
    print(f"Loaded {len(seed_ids)} seed sequences from {seeds_path}")

    pool = generate_candidate_pool(
        seed_sequences=seed_seqs,
        seed_ids=seed_ids,
        n_double=args.n_double,
        n_charge_enhance=args.n_charge,
        rng_seed=args.rng_seed,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "sequence", "source"])
        writer.writeheader()
        writer.writerows(pool)

    print(f"Generated {len(pool)} candidate variants → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
