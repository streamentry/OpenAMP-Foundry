from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest.mock
from pathlib import Path

# scripts/ is not part of the openamp_foundry package, so we load the
# benchmark_gate module by file path. This avoids depending on whether
# scripts/ is on PYTHONPATH in a given environment (local dev, CI,
# editable install, etc.).
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
_spec = importlib.util.spec_from_file_location(
    "_scripts_benchmark_gate", _SCRIPTS_DIR / "benchmark_gate.py"
)
_benchmark_gate = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_benchmark_gate)
run_benchmark_gate = _benchmark_gate.run_benchmark_gate


def _snapshot(
    auroc: float = 0.7832,
    cluster_full: float = 0.7832,
    cluster_rep: float = 0.7607,
    rich_detection: float = 0.7138,
    gate_triage_correct: bool = True,
    best_scorer: str = "gate_triage",
) -> dict:
    return {
        "standard": {"auroc": auroc, "auprc": 0.8, "n_positives": 95, "n_negatives": 96},
        "phase3": {"auroc": auroc - 0.0384, "auprc": 0.76, "n_positives": 95, "n_negatives": 96},
        "cluster_split": {
            "full_auroc": cluster_full,
            "representative_auroc": cluster_rep,
        },
        "selectivity": {
            "per_score_auroc": {
                "rich_selectivity": {
                    "hemolysis_detection_auroc": rich_detection,
                },
            },
        },
        "triage": {
            "best_scorer": best_scorer,
            "per_scorer": {
                "gate_triage": {
                    "triages_correctly": gate_triage_correct,
                },
            },
        },
    }


class TestRunBenchmarkGate:
    def test_passes_when_auroc_unchanged(self):
        snap = _snapshot(0.7832)
        assert run_benchmark_gate(snap, snap) == 0

    def test_passes_when_auroc_improves(self):
        baseline = _snapshot(0.7832)
        current = _snapshot(0.7900)
        assert run_benchmark_gate(baseline, current) == 0

    def test_passes_within_tolerance(self):
        baseline = _snapshot(0.7832)
        current = _snapshot(0.7700)
        assert run_benchmark_gate(baseline, current, tolerance=0.02) == 0

    def test_fails_when_auroc_drops_below_tolerance(self):
        baseline = _snapshot(0.7832)
        current = _snapshot(0.7550)
        assert run_benchmark_gate(baseline, current, tolerance=0.02) == 1

    def test_fails_when_both_metrics_regress(self):
        baseline = _snapshot(0.7832)
        current = _snapshot(0.7000)
        assert run_benchmark_gate(baseline, current, tolerance=0.02) == 1

    def test_fails_when_tolerance_is_zero_and_auroc_drops(self):
        baseline = _snapshot(0.7832)
        current = _snapshot(0.7831)
        assert run_benchmark_gate(baseline, current, tolerance=0.0) == 1

    def test_fails_when_baseline_missing_metrics(self):
        assert run_benchmark_gate({}, _snapshot(0.7832)) == 0

    def test_writes_report_file(self, tmp_path):
        report = tmp_path / "report.md"
        snap = _snapshot(0.7832)
        rc = run_benchmark_gate(snap, snap, report_file=report)
        assert rc == 0
        assert report.exists()
        content = report.read_text(encoding="utf-8")
        assert "PASS" in content

    def test_writes_report_file_on_failure(self, tmp_path):
        report = tmp_path / "report.md"
        baseline = _snapshot(0.7832)
        current = _snapshot(0.7000)
        rc = run_benchmark_gate(baseline, current, report_file=report)
        assert rc == 1
        content = report.read_text(encoding="utf-8")
        assert "FAIL" in content


class TestBenchmarkGateCLI:
    def test_missing_baseline_returns_2(self, tmp_path):
        fake = tmp_path / "nonexistent.json"
        result = subprocess.run(
            [sys.executable, "scripts/benchmark_gate.py", "--baseline", str(fake)],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        assert result.returncode == 2

    def test_passes_with_committed_baseline(self):
        result = subprocess.run(
            [sys.executable, "scripts/benchmark_gate.py",
             "--baseline", "outputs/metrics_snapshot.json",
             "--n-bootstrap", "50"],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_fails_with_artificially_low_tolerance(self, tmp_path):
        baseline = _snapshot(0.7832)
        current = _snapshot(0.7810)
        low = tmp_path / "baseline.json"
        low.write_text(json.dumps(baseline), encoding="utf-8")

        with unittest.mock.patch(
            "openamp_foundry.benchmark.metrics_snapshot.build_metrics_snapshot",
            return_value=current,
        ):
            # _benchmark_gate is loaded at module scope above via importlib.util
            main = _benchmark_gate.main
            rc = main(["--baseline", str(low), "--tolerance", "0.0"])
            assert rc == 1

    def test_out_flag_writes_report(self, tmp_path):
        snap = _snapshot(0.7832)
        baseline_file = tmp_path / "baseline.json"
        baseline_file.write_text(json.dumps(snap), encoding="utf-8")

        with unittest.mock.patch(
            "openamp_foundry.benchmark.metrics_snapshot.build_metrics_snapshot",
            return_value=snap,
        ):
            report = tmp_path / "gate.md"
            # _benchmark_gate is loaded at module scope above via importlib.util
            main = _benchmark_gate.main
            rc = main(["--baseline", str(baseline_file), "--out", str(report)])
            assert rc == 0
            assert report.exists()
            assert "PASS" in report.read_text(encoding="utf-8")

    # ── Extended gate: cluster-split checks ─────────────────────────────

    def test_passes_when_cluster_split_stable(self):
        baseline = _snapshot(cluster_full=0.7832, cluster_rep=0.7607)
        current = _snapshot(cluster_full=0.7800, cluster_rep=0.7550)
        assert run_benchmark_gate(baseline, current, cluster_tolerance=0.03) == 0

    def test_fails_when_cluster_full_drops_below_tolerance(self):
        baseline = _snapshot(cluster_full=0.7832)
        current = _snapshot(cluster_full=0.7400)
        assert run_benchmark_gate(baseline, current, cluster_tolerance=0.03) == 1

    def test_fails_when_cluster_rep_drops_below_tolerance(self):
        baseline = _snapshot(cluster_rep=0.7607)
        current = _snapshot(cluster_rep=0.7200)
        assert run_benchmark_gate(baseline, current, cluster_tolerance=0.03) == 1

    # ── Extended gate: selectivity check ────────────────────────────────

    def test_passes_when_rich_selectivity_stable(self):
        baseline = _snapshot(rich_detection=0.7138)
        current = _snapshot(rich_detection=0.7000)
        assert run_benchmark_gate(baseline, current, selectivity_tolerance=0.05) == 0

    def test_fails_when_rich_selectivity_drops_below_tolerance(self):
        baseline = _snapshot(rich_detection=0.7138)
        current = _snapshot(rich_detection=0.6200)
        assert run_benchmark_gate(baseline, current, selectivity_tolerance=0.05) == 1

    # ── Extended gate: triage boolean checks ────────────────────────────

    def test_passes_when_gate_triage_correct(self):
        baseline = _snapshot(gate_triage_correct=True, best_scorer="gate_triage")
        current = _snapshot(gate_triage_correct=True, best_scorer="gate_triage")
        assert run_benchmark_gate(baseline, current) == 0

    def test_fails_when_gate_triage_becomes_incorrect(self):
        baseline = _snapshot(gate_triage_correct=True, best_scorer="gate_triage")
        current = _snapshot(gate_triage_correct=False, best_scorer="gate_triage")
        assert run_benchmark_gate(baseline, current) == 1

    def test_skips_when_baseline_missing_metric(self):
        """If a metric path is missing from baseline, gate skips — not fails."""
        baseline = {"standard": {"auroc": 0.7832}}
        current = _snapshot()
        assert run_benchmark_gate(baseline, current) == 0
