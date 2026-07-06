#!/usr/bin/env python3
"""Regenerate all derived outputs and verify determinism.

Usage:
  python scripts/regenerate_all.py            # run + check
  python scripts/regenerate_all.py --update    # run + update baseline
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


TRACKED: list[str] = [
    "outputs/metrics_snapshot.json",
]

TARGETS: list[str] = [
    "demo",
    "validate-scoring",
    "validate-scoring-phase3",
    "validate-scoring-strict",
    "bench-leakage",
    "bench-cluster-split",
    "bench-expert-ablation",
    "bench-selectivity",
    "bench-triage",
    "bench-feature-decomp",
    "metrics-snapshot",
]


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_make(target: str) -> int:
    env = {**subprocess.os.environ, "PYTHONPATH": "src"}
    result = subprocess.run(
        ["make", target],
        capture_output=True, text=True,
        env=env,
    )
    if result.returncode != 0:
        print(f"  FAIL: make {target} (exit {result.returncode})")
        short = (result.stderr or "")[:600]
        if short:
            for line in short.splitlines():
                print(f"    {line}")
    else:
        print(f"  OK:   make {target}")
    return result.returncode


def run_targets(targets: list[str] | None = None) -> int:
    failures = 0
    for t in targets or TARGETS:
        rc = run_make(t)
        if rc != 0:
            failures += 1
            print(f"  -> stopping early after make {t} failed")
            return 1
    return 0


def check_determinism(
    tracked: list[str] | None = None,
) -> int:
    result = subprocess.run(
        ["git", "diff", "--exit-code", "--stat"] + (tracked or TRACKED),
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        print("\nPASS: All tracked outputs unchanged — pipeline is deterministic")
        return 0
    print("\nFAIL: Tracked outputs changed:")
    print(result.stdout[:1000])
    print("Run without --update, commit the new baseline, and re-run.")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate all derived outputs and verify determinism."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update baseline (git add tracked outputs) after regeneration",
    )
    parser.add_argument(
        "--skip-targets",
        action="store_true",
        help="Skip running targets (only check determinism)",
    )
    args = parser.parse_args(argv)

    if not args.skip_targets:
        print("=== Regenerating all derived outputs ===")
        rc = run_targets()
        if rc != 0:
            return rc

    rc = check_determinism()
    if rc == 0:
        return 0

    if args.update:
        print("\nUpdating baseline...")
        subprocess.run(["git", "add"] + TRACKED, check=True)
        print("Done. Run `git commit` to save the updated baseline.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
