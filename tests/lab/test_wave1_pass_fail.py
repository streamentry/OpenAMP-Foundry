"""Tests for the Wave 1 pass/fail criteria checker."""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "lab" / "check_wave1_pass_fail.py"
_spec = importlib.util.spec_from_file_location("_scripts_lab_wave1_pass_fail", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
_check_criteria = _mod._check_criteria
_load_lab_results = _mod._load_lab_results


def _make_result(
    candidate_id: str,
    assay_type: str,
    value: float,
    organism: str = "Escherichia coli ATCC 25922",
    positive_control_passed: bool = True,
) -> dict:
    return {
        "result_id": f"{candidate_id}_{assay_type}",
        "candidate_id": candidate_id,
        "assay_type": assay_type,
        "organism_or_cell_line": organism,
        "result_value": value,
        "result_unit": "ug/mL",
        "positive_control_passed": positive_control_passed,
        "negative_control_passed": True,
        "assay_date": "2026-08-15",
        "replicate_count": 3,
        "performed_by_lab": "Test Lab",
        "computational_candidate_certificate_hash": "abc123",
        "disclaimer": "SYNTHETIC TEST DATA",
    }


_MINIMAL_CRITERIA = {
    "primary_endpoint": {
        "organism": "Escherichia coli ATCC 25922",
        "assay_type": "MIC",
        "max_mic_ugml": 32,
        "min_passing_candidates": 3,
    },
    "secondary_endpoint": {
        "max_mic_ugml": 32,
        "min_therapeutic_index": 10,
        "min_passing_candidates": 1,
    },
    "positive_controls": [
        {
            "candidate_id": "CTRL-001",
            "expected_mic_min_ugml": 4,
            "expected_mic_max_ugml": 32,
        }
    ],
    "hemolysis": {
        "assay_type": "hemolysis_RBC",
        "ti_toxic_threshold": 2,
        "ti_selective_threshold": 10,
        "max_toxic_candidates": 0,
    },
    "batch_level": {
        "positive_control_passed": True,
        "negative_control_passed": True,
        "min_total_candidates_tested": 3,
        "require_all_results_reported": True,
    },
}


def test_load_results_empty_dir():
    with tempfile.TemporaryDirectory() as tmp:
        results = _load_lab_results(tmp)
        assert len(results) == 0


def test_load_results_finds_jsons():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        data = {"candidate_id": "T1", "assay_type": "MIC", "result_value": 8}
        (d / "r1.json").write_text(json.dumps(data))
        (d / "r2.txt").write_text("not json")
        results = _load_lab_results(tmp)
        assert len(results) == 1


def test_check_all_pass():
    results = [
        _make_result("C1", "MIC", 8),
        _make_result("C2", "MIC", 16),
        _make_result("C3", "MIC", 4),
        _make_result("C1", "hemolysis_RBC", 320),
        _make_result("C2", "hemolysis_RBC", 640),
        _make_result("C3", "hemolysis_RBC", 160),
        _make_result("CTRL-001", "MIC", 16),
    ]
    verdict = _check_criteria(results, _MINIMAL_CRITERIA)
    assert verdict["all_pass"] is True


def test_check_mic_fails_when_too_few_pass():
    results = [
        _make_result("C1", "MIC", 64),
        _make_result("C2", "MIC", 128),
        _make_result("CTRL-001", "MIC", 16),
    ]
    verdict = _check_criteria(results, _MINIMAL_CRITERIA)
    assert verdict["all_pass"] is False
    assert verdict["checks"]["primary_endpoint_mic"]["pass"] is False


def test_check_positive_control_fails():
    results = [
        _make_result("C1", "MIC", 8),
        _make_result("C2", "MIC", 16),
        _make_result("C3", "MIC", 4),
    ]
    verdict = _check_criteria(results, _MINIMAL_CRITERIA)
    assert verdict["all_pass"] is False
    assert verdict["checks"]["positive_controls"]["pass"] is False


def test_check_hemolysis_toxic():
    results = [
        _make_result("C1", "MIC", 4),
        _make_result("C1", "hemolysis_RBC", 2),
        _make_result("CTRL-001", "MIC", 16),
    ]
    verdict = _check_criteria(results, _MINIMAL_CRITERIA)
    assert verdict["all_pass"] is False
    assert verdict["checks"]["hemolysis_safety"]["pass"] is False


def test_check_secondary_endpoint():
    results = [
        _make_result("C1", "MIC", 8),
        _make_result("C1", "hemolysis_RBC", 320),
        _make_result("C2", "MIC", 64),
        _make_result("CTRL-001", "MIC", 16),
    ]
    verdict = _check_criteria(results, _MINIMAL_CRITERIA)
    # C1: MIC=8, HC50=320, TI=40 > 10 → secondary passes
    assert verdict["checks"]["secondary_endpoint"]["detail"] is not None


def test_cli_no_results_dir():
    result = subprocess.run(
        [sys.executable, "scripts/lab/check_wave1_pass_fail.py",
         "--results-dir", "/nonexistent"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert result.returncode == 2


def test_cli_all_pass(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    # Use the real positive control ID from the YAML config
    (results_dir / "c1_mic.json").write_text(json.dumps(_make_result("C1", "MIC", 8)))
    (results_dir / "c2_mic.json").write_text(json.dumps(_make_result("C2", "MIC", 16)))
    (results_dir / "c3_mic.json").write_text(json.dumps(_make_result("C3", "MIC", 4)))
    candidates = ["C1", "C2", "C3"] + [f"C{i}" for i in range(4, 21)]
    for c in candidates:
        (results_dir / f"{c}_mic.json").write_text(
            json.dumps(_make_result(c, "MIC", 16)))
        (results_dir / f"{c}_hemo.json").write_text(
            json.dumps(_make_result(c, "hemolysis_RBC", 320)))
    (results_dir / "ctrl.json").write_text(
        json.dumps(_make_result("SEED-001_VAR_064", "MIC", 16)))
    result = subprocess.run(
        [sys.executable, "scripts/lab/check_wave1_pass_fail.py",
         "--results-dir", str(results_dir)],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0


def test_cli_fails_when_mic_criteria_not_met(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "c1_mic.json").write_text(json.dumps(_make_result("C1", "MIC", 128)))
    (results_dir / "ctrl.json").write_text(json.dumps(_make_result("CTRL-001", "MIC", 16)))
    result = subprocess.run(
        [sys.executable, "scripts/lab/check_wave1_pass_fail.py",
         "--results-dir", str(results_dir)],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert result.returncode == 3


def test_cli_writes_output_json(tmp_path):
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / "c1_mic.json").write_text(json.dumps(_make_result("C1", "MIC", 8)))
    (results_dir / "ctrl.json").write_text(json.dumps(_make_result("CTRL-001", "MIC", 16)))
    out = tmp_path / "verdict.json"
    subprocess.run(
        [sys.executable, "scripts/lab/check_wave1_pass_fail.py",
         "--results-dir", str(results_dir),
         "--out", str(out)],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert out.exists()
    data = json.loads(out.read_text())
    assert "all_pass" in data
    assert "checks" in data
