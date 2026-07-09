"""End-to-end test for recalibration gate with synthetic data."""
import json
import subprocess
import sys
from pathlib import Path


def test_recalibration_gate_example_runs_and_fails_closed():
    r = subprocess.run(
        ["make", "lab-result-intake-example"],
        capture_output=True, text=True,
        cwd=Path(__file__).parents[1],
    )
    assert r.returncode == 0, f"make lab-result-intake-example failed: {r.stderr[:200]}"

    repo = Path(__file__).parents[1]
    r = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "recalibration-gate",
         "--intake-report", "outputs/calibration_intake_example.json",
         "--intake-report-date", "2026-07-04",
         "--out-json", "outputs/recalibration_gate_example.json",
         "--out-md", "outputs/recalibration_gate_example.md"],
        capture_output=True, text=True,
        cwd=repo,
        env={**__import__("os").environ, "PYTHONPATH": "src"},
    )
    # Gate correctly fails-closed (exit 3) because cohort size 4 < minimum 5
    assert r.returncode == 3, (
        f"Expected exit 3 (fail-closed), got {r.returncode}. "
        f"Gate should reject cohort < 5 candidates.\nstdout: {r.stdout[:300]}\nstderr: {r.stderr[:300]}"
    )


def test_recalibration_gate_output_exists():
    out = Path("outputs/recalibration_gate_example.json")
    assert out.exists(), "Expected gate verdict JSON"


def test_recalibration_gate_output_shows_blocked():
    out = Path("outputs/recalibration_gate_example.json")
    data = json.loads(out.read_text())
    assert "may_recalibrate" in str(data) or "FAIL" in str(data)
    assert "recalibration forbidden" in str(data).lower()
