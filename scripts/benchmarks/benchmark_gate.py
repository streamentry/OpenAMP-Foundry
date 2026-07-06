#!/usr/bin/env python3
"""Benchmark regression gate for CI — fail CI if key metrics regress."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def _deep_get(d: dict, path: str) -> object:
    """Resolve a dotted path like 'a.b.c' in a nested dict."""
    parts = path.split(".")
    for p in parts:
        if not isinstance(d, dict):
            return None
        d = d.get(p, {})
    return d if d != {} else None


def run_benchmark_gate(
    baseline: dict,
    current: dict,
    tolerance: float = 0.02,
    *,
    report_file: str | Path | None = None,
    cluster_tolerance: float = 0.03,
    selectivity_tolerance: float = 0.05,
) -> int:
    """Compare baseline vs current metrics and return 0 (pass) or 1 (fail).

    Checks:
      - standard.auroc, phase3.auroc  (tolerance)
      - cluster_split.full_auroc, cluster_split.representative_auroc (cluster_tolerance)
      - selectivity.per_score_auroc.rich_selectivity.hemolysis_detection_auroc (selectivity_tolerance)
      - triage.per_scorer.gate_triage.triages_correctly  (must remain True)
      - triage.best_scorer  (must remain "gate_triage")
    """
    # Define checks: (label, dotted_path, tolerance_or_bool_target, is_boolean)
    numeric_checks = [
        ("standard.auroc", "standard.auroc", tolerance),
        ("phase3.auroc", "phase3.auroc", tolerance),
        ("cluster_split.full_auroc", "cluster_split.full_auroc", cluster_tolerance),
        ("cluster_split.representative_auroc", "cluster_split.representative_auroc", cluster_tolerance),
        ("rich_selectivity.detection.auroc",
         "selectivity.per_score_auroc.rich_selectivity.hemolysis_detection_auroc",
         selectivity_tolerance),
    ]

    bool_checks = [
        ("gate_triage.triages_correctly",
         "triage.per_scorer.gate_triage.triages_correctly",
         True),
        ("triage.best_scorer",
         "triage.best_scorer",
         "gate_triage"),
    ]

    lines: list[str] = []
    lines.append("=== Benchmark Regression Gate ===")
    lines.append(f"AUROC tolerance: {tolerance}; cluster: {cluster_tolerance}; selectivity: {selectivity_tolerance}")
    lines.append("")

    worst_delta = 0.0
    any_fail = False

    for label, path, tol in numeric_checks:
        b = _deep_get(baseline, path)
        c = _deep_get(current, path)
        if b is None:
            lines.append(f"  [SKIP] {label:30s} baseline metric not found")
            continue
        if c is None:
            lines.append(f"  [SKIP] {label:30s} current metric not found")
            continue
        if not isinstance(b, (int, float)) or not isinstance(c, (int, float)):
            lines.append(f"  [SKIP] {label:30s} non-numeric values")
            continue
        bf, cf = float(b), float(c)
        d = bf - cf
        flag = "FAIL" if d > tol else "PASS"
        if d > tol:
            any_fail = True
        lines.append(
            f"  [{flag:4s}] {label:30s} {bf:.4f} → {cf:.4f}  (Δ={d:+.4f})"
        )
        if d > worst_delta:
            worst_delta = d

    for label, path, expected in bool_checks:
        b = _deep_get(baseline, path)
        c = _deep_get(current, path)
        if b is None:
            lines.append(f"  [SKIP] {label:30s} baseline metric not found")
            continue
        if c is None:
            lines.append(f"  [SKIP] {label:30s} current metric not found")
            continue
        if c != expected:
            any_fail = True
            lines.append(f"  [FAIL] {label:30s} {b} → {c}  (expected {expected})")
        else:
            lines.append(f"  [PASS] {label:30s} {b} → {c}")

    lines.append("")
    if any_fail:
        lines.append(f"FAIL: Benchmark regression detected — {worst_delta=:.4f}")
        lines.append("Investigate scoring changes before merging.")
        report = "\n".join(lines)
        print(report)
        if report_file:
            Path(report_file).write_text(report, encoding="utf-8")
        return 1

    lines.append(
        f"PASS: All benchmark metrics within tolerances "
        f"(max Δ={worst_delta:.4f})"
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
