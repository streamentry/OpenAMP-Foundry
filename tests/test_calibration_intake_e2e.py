"""End-to-end test for calibration-intake with synthetic lab data."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_calibration_intake_example_runs():
    """Verify make lab-result-intake-example produces valid output."""
    r = subprocess.run(
        ["make", "lab-result-intake-example"],
        capture_output=True, text=True,
        cwd=Path(__file__).parents[1],
    )
    assert r.returncode == 0, f"Intake failed: {r.stderr[:300]}"


def test_calibration_intake_example_output_exists():
    out_json = Path("outputs/calibration_intake_example.json")
    out_md = Path("outputs/calibration_intake_example.md")
    assert out_json.exists(), "Expected calibration_intake_example.json"
    assert out_md.exists(), "Expected calibration_intake_example.md"


def test_calibration_intake_example_is_valid_json():
    out_json = Path("outputs/calibration_intake_example.json")
    data = json.loads(out_json.read_text())
    assert "status" in data or "candidates" in data or "summary" in data


def test_calibration_intake_with_explicit_args():
    with tempfile.TemporaryDirectory() as tmp:
        out_json = Path(tmp) / "intake.json"
        r = subprocess.run(
            [sys.executable, "-m", "openamp_foundry.cli", "calibration-intake",
             "--panel", "examples/lab_results_panel.csv",
             "--results-dir", "examples/lab_results",
             "--out-json", str(out_json)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0, f"Intake CLI failed: {r.stderr[:200]}"
        data = json.loads(out_json.read_text())
        assert data.get("n_matched_candidates", 0) > 0, "Expected matched candidates"
