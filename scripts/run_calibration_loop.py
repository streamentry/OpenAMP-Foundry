#!/usr/bin/env python3
"""Full calibration loop: synthetic data → intake → gate → engine → batch-2 manifest.

Runs the entire calibration pipeline on synthetic data to produce a batch-2
manifest. This is a code-path integrity check — all data is synthetic, no
biological claims are made.

Usage::

    python scripts/run_calibration_loop.py

    python scripts/run_calibration_loop.py \\
        --panel examples/lab_results_panel.csv \\
        --policy configs/recalibration_policy.yaml \\
        --out-dir outputs/calibration_loop \\
        --seed 42
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def run_calibration_loop(
    *,
    panel_csv: str | Path,
    policy_yaml: str | Path,
    out_dir: str | Path,
    rng_seed: int = 42,
    n_batch_2: int = 10,
) -> dict[str, Any]:
    """Execute the full calibration loop on synthetic data.

    Steps:
        1. Generate synthetic lab results for the panel.
        2. Build calibration intake report.
        3. Evaluate recalibration gate.
        4. Compute weight update proposal (dry-run).
        5. Select batch-2 candidates.
        6. Write batch-2 manifest.

    Returns a summary dict with paths and key results.
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    repo_root = Path(__file__).resolve().parent.parent
    results: dict[str, Any] = {}
    notes: list[str] = []

    # ── Step 1: Generate synthetic lab results ────────────────────────
    print("=" * 60)
    print("Step 1/5: Generating synthetic lab results...")
    print("=" * 60)
    results_dir = out_path / "synthetic_lab_results"
    results_dir.mkdir(parents=True, exist_ok=True)

    import subprocess

    gen_cmd = [
        sys.executable, str(repo_root / "examples" / "lab_results_generator.py"),
        "--panel-csv", str(Path(panel_csv).resolve()),
        "--out-dir", str(results_dir.resolve()),
        "--effect-size", "0.40",
        "--noise-level", "0.05",
        "--assay-types", "MIC", "hemolysis_RBC",
        "--seed", str(rng_seed),
        "--no-validate",
    ]
    gen_result = subprocess.run(gen_cmd, capture_output=True, text=True, timeout=120)
    if gen_result.returncode != 0:
        print(f"  ⚠ Generator stderr: {gen_result.stderr[:500]}")
        print(f"  ⚠ Generator stdout: {gen_result.stdout[:500]}")
    # Count generated files
    gen_paths = sorted(results_dir.glob("*.json"))
    n_results = len(gen_paths)
    n_active = 0
    for p in gen_paths:
        try:
            d = json.loads(p.read_text())
            if d.get("result_qualitative") == "active":
                n_active += 1
        except Exception:
            pass
    print(f"  Generated {n_results} lab results ({n_active} active, "
          f"{n_results - n_active} inactive)")
    results["n_synthetic_results"] = n_results
    results["n_active_results"] = n_active

    # ── Step 2: Build intake report ───────────────────────────────────
    print()
    print("=" * 60)
    print("Step 2/5: Building calibration intake report...")
    print("=" * 60)
    from openamp_foundry.calibration.intake import (
        build_calibration_intake_report,
        write_calibration_intake_json,
    )

    intake = build_calibration_intake_report(
        panel_csv=Path(panel_csv),
        results_dir=results_dir,
    )
    intake_json = out_path / "intake_report.json"
    write_calibration_intake_json(intake, intake_json)
    print(f"  Intake report written to {intake_json}")
    print(f"  Matched candidates: {intake.get('n_matched_candidates', '?')}")
    n_cohort = len(intake.get("cohort_metrics", {}))
    print(f"  Cohort metrics: {n_cohort}")
    results["intake_report"] = str(intake_json)
    results["n_matched_candidates"] = intake.get("n_matched_candidates", 0)
    results["n_cohort_metrics"] = n_cohort

    # ── Step 3: Evaluate gate ─────────────────────────────────────────
    print()
    print("=" * 60)
    print("Step 3/5: Evaluating recalibration gate...")
    print("=" * 60)
    from openamp_foundry.calibration.policy import load_recalibration_policy
    from openamp_foundry.calibration.recalibration_gate import (
        evaluate_recalibration_gate,
        write_gate_verdict_json,
    )

    policy = load_recalibration_policy(Path(policy_yaml))
    gate_verdict = evaluate_recalibration_gate(
        intake_report=intake,
        policy=policy,
        project_root=repo_root,
    )
    gate_json = out_path / "gate_verdict.json"
    write_gate_verdict_json(gate_verdict, gate_json)
    print(f"  Gate verdict written to {gate_json}")
    print(f"  may_recalibrate: {gate_verdict.may_recalibrate}")
    n_blockers = len(gate_verdict.reasons)
    print(f"  Blockers: {n_blockers}")
    results["gate_verdict"] = str(gate_json)
    results["may_recalibrate"] = gate_verdict.may_recalibrate
    results["n_blockers"] = n_blockers

    if not gate_verdict.may_recalibrate:
        notes.append(
            "Gate returned may_recalibrate=False. The synthetic cohort may be "
            "too small or have control failures. Continuing with dry-run engine "
            "but weight proposal will raise PolicyViolationError."
        )

    # ── Step 4: Compute weight updates (dry-run) ──────────────────────
    print()
    print("=" * 60)
    print("Step 4/5: Computing weight update proposal (dry-run)...")
    print("=" * 60)

    # Get current weights from policy or use defaults
    current_weights = {"activity": 0.40, "safety": 0.25, "synthesis": 0.20, "novelty": 0.15}
    l1_budget = next(
        (rl.threshold for rl in policy.rate_limits if rl.id == "WEIGHT_CHANGE_L1_BUDGET"),
        0.10,
    )

    engine_success = False
    proposal = None
    from openamp_foundry.calibration.engine import (
        BudgetExceededError,
        PolicyViolationError,
        compute_weight_update,
        write_weight_update_proposal_json,
    )

    try:
        proposal = compute_weight_update(
            intake_report=intake,
            gate_verdict=gate_verdict,
            current_weights=current_weights,
            policy_l1_budget=l1_budget,
        )
        engine_success = True
        proposal_json = out_path / "weight_proposal.json"
        write_weight_update_proposal_json(proposal, proposal_json)
        print(f"  Weight proposal written to {proposal_json}")
        print(f"  Deltas: {len(proposal.deltas)}")
        print(f"  L1 total: {proposal.l1_total:.4f} / budget {l1_budget:.4f}")
        results["weight_proposal"] = str(proposal_json)
        results["n_deltas"] = len(proposal.deltas)
        results["l1_total"] = proposal.l1_total
    except PolicyViolationError as e:
        notes.append(f"Engine PolicyViolationError: {e}")
        print(f"  ⚠ Policy violation: {e}")
        results["engine_error"] = str(e)
    except BudgetExceededError as e:
        notes.append(f"Engine BudgetExceededError: {e}")
        print(f"  ⚠ Budget exceeded: {e}")
        results["engine_error"] = str(e)

    # ── Step 5: Select batch 2 ────────────────────────────────────────
    print()
    print("=" * 60)
    print("Step 5/5: Selecting batch-2 candidates...")
    print("=" * 60)

    from openamp_foundry.active_learning.selector import select_batch_2

    # Extract unique candidate IDs from synthetic lab results (batch-1 test subjects)
    # For the integration test, use empty batch-1 IDs since all panel candidates
    # are tested candidates. In a real run, batch-1 IDs would be the tested subset
    # of a larger pool.
    batch_1_ids: list[str] = []

    selection = select_batch_2(
        candidates_csv=Path(panel_csv),
        batch_1_ids=batch_1_ids,
        n=n_batch_2,
        safety_threshold=0.0,
        selectivity_threshold=0.0,
    )

    manifest = out_path / "batch_2_manifest.json"
    manifest.write_text(
        json.dumps(selection.to_dict(), indent=2, sort_keys=False) + "\n"
    )
    print(f"  Batch-2 manifest written to {manifest}")
    print(f"  Selected: {len(selection.selected)} candidates")
    selected_ids = [str(c.get("candidate_id", "?")) for c in selection.selected]
    print(f"  IDs: {', '.join(selected_ids)}")
    print(f"  Probes in top-N: {selection.probes_in_top_n}")
    results["batch_2_manifest"] = str(manifest)
    results["n_batch_2_selected"] = len(selection.selected)
    results["batch_2_ids"] = selected_ids
    results["probes_in_top_n"] = selection.probes_in_top_n

    # ── Summary ───────────────────────────────────────────────────────
    results["notes"] = notes
    if notes:
        print()
        print("Notes:")
        for n in notes:
            print(f"  - {n}")

    print()
    print("=" * 60)
    print("Calibration loop complete.")
    print(f"Output directory: {out_path.resolve()}")
    print("=" * 60)

    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the full calibration loop on synthetic data.",
    )
    parser.add_argument(
        "--panel",
        default="examples/lab_results_panel.csv",
        help="Path to the pilot panel CSV (default: examples/lab_results_panel.csv).",
    )
    parser.add_argument(
        "--policy",
        default="configs/recalibration_policy.yaml",
        help="Path to the recalibration policy YAML (default: configs/recalibration_policy.yaml).",
    )
    parser.add_argument(
        "--out-dir",
        default="outputs/calibration_loop",
        help="Output directory (default: outputs/calibration_loop).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--n-batch-2",
        type=int,
        default=10,
        help="Desired batch-2 size (default: 10).",
    )
    args = parser.parse_args(argv)

    results = run_calibration_loop(
        panel_csv=args.panel,
        policy_yaml=args.policy,
        out_dir=args.out_dir,
        rng_seed=args.seed,
        n_batch_2=args.n_batch_2,
    )

    summary = {k: v for k, v in results.items() if k != "notes"}
    summary["n_notes"] = len(results.get("notes", []))
    print()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
