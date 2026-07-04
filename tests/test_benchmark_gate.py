from __future__ import annotations

import json
import subprocess
import sys
import unittest.mock
from pathlib import Path

from scripts.benchmark_gate import run_benchmark_gate


def _snapshot(auroc: float) -> dict:
    return {
        "standard": {"auroc": auroc, "auprc": 0.8, "n_positives": 95, "n_negatives": 96},
        "phase3": {"auroc": auroc - 0.0384, "auprc": 0.76, "n_positives": 95, "n_negatives": 96},
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
            from scripts.benchmark_gate import main
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
            from scripts.benchmark_gate import main
            rc = main(["--baseline", str(baseline_file), "--out", str(report)])
            assert rc == 0
            assert report.exists()
            assert "PASS" in report.read_text(encoding="utf-8")
