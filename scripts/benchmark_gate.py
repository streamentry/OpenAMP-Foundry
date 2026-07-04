#!/usr/bin/env python3
"""Benchmark regression gate for CI — fail CI if AUROC drops significantly."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def run_benchmark_gate(
    baseline: dict,
    current: dict,
    tolerance: float = 0.02,
    *,
    report_file: str | Path | None = None,
) -> int:
    keys = ["standard", "phase3"]
    lines: list[str] = []
    lines.append("=== Benchmark Regression Gate ===")
    lines.append(f"Tolerance: AUROC drop <= {tolerance}")
    lines.append("")

    worst_delta = 0.0
    for key in keys:
        b = baseline.get(key, {}).get("auroc", 0.0)
        c = current.get(key, {}).get("auroc", 0.0)
        d = b - c
        flag = "FAIL" if d > tolerance else "PASS"
        lines.append(
            f"  [{flag:4s}] {key + '.auroc':30s} {b:.4f} → {c:.4f}  (Δ={d:+.4f})"
        )
        if d > worst_delta:
            worst_delta = d

    lines.append("")
    if worst_delta > tolerance:
        lines.append(
            f"FAIL: AUROC regression detected — max Δ={worst_delta:.4f}"
            f" exceeds tolerance {tolerance}"
        )
        lines.append("Investigate scoring changes before merging.")
        report = "\n".join(lines)
        print(report)
        if report_file:
            Path(report_file).write_text(report, encoding="utf-8")
        return 1

    lines.append(
        f"PASS: All AUROC metrics within tolerance "
        f"(max Δ={worst_delta:.4f}, limit={tolerance})"
    )
    report = "\n".join(lines)
    print(report)
    if report_file:
        Path(report_file).write_text(report, encoding="utf-8")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark regression gate — checks AUROC hasn't dropped significantly."
    )
    parser.add_argument(
        "--baseline",
        default="outputs/metrics_snapshot.json",
        help="Path to baseline metrics_snapshot.json",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.02,
        help="Maximum allowed AUROC drop (default: 0.02)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional path to write report file",
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=200,
        help="Bootstrap iterations for benchmarks (default: 200, CI-friendly)",
    )
    args = parser.parse_args(argv)

    baseline_path = Path(args.baseline)
    if not baseline_path.exists():
        print(f"ERROR: Baseline not found at {baseline_path}", file=sys.stderr)
        print("Run 'make metrics-snapshot' first to generate baseline.", file=sys.stderr)
        return 2

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    from openamp_foundry.benchmark.metrics_snapshot import build_metrics_snapshot

    print("Running benchmarks (all 6)...")
    current = build_metrics_snapshot(n_bootstrap=args.n_bootstrap)
    print("Done.\n")

    return run_benchmark_gate(
        baseline, current, tolerance=args.tolerance, report_file=args.out
    )


if __name__ == "__main__":
    sys.exit(main())
