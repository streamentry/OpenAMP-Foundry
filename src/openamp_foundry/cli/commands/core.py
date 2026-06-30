"""Core pipeline commands."""
from __future__ import annotations
import argparse
import json
import csv
from pathlib import Path

def _run_generate_batch(args: argparse.Namespace) -> int:

    from openamp_foundry.generators.template_mutator import generate_candidate_pool

    seeds_path = Path(args.seeds)
    if not seeds_path.exists():
        print(json.dumps({"status": "error", "message": f"Seeds file not found: {args.seeds}"}))
        return 1

    seed_ids: list[str] = []
    seed_seqs: list[str] = []
    with open(seeds_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            seed_ids.append(row["id"])
            seed_seqs.append(row["sequence"].strip().upper())

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

    print(json.dumps({
        "status": "ok",
        "n_seeds": len(seed_ids),
        "n_candidates_generated": len(pool),
        "out": str(out_path),
        "disclaimer": (
            "Generated candidates are toy conservative-substitution variants. "
            "They have no demonstrated biological activity. "
            "Run 'rank' to score and filter them."
        ),
    }, indent=2))
    return 0


