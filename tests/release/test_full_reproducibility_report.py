"""Tests for the full reproducibility report."""

import importlib.util
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "release" / "full_reproducibility_report.py"
_spec = importlib.util.spec_from_file_location("_scripts_release_full_repro_report", _SCRIPT_PATH)
_mod = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_mod)
build_report = _mod.build_report


def test_report_builds():
    report = build_report()
    assert report["report_type"] == "full_reproducibility"
    assert report["loops_completed"] == 50
    assert "sections" in report


def test_report_has_git_section():
    report = build_report()
    assert "git" in report["sections"]
    assert len(report["sections"]["git"]["head_sha"]) > 5


def test_report_has_test_count():
    report = build_report()
    assert "tests" in report["sections"]
    assert report["sections"]["tests"]["collection_output"]


def test_report_has_phase4_readiness():
    report = build_report()
    assert "phase_4_readiness" in report["sections"]
    assert "all_met" in report["sections"]["phase_4_readiness"]


def test_report_has_honest_limitations():
    report = build_report()
    assert "limitations" in report["sections"]
    assert "no_wet_lab_data" in report["sections"]["limitations"]


def test_report_has_simulation_status():
    report = build_report()
    assert "simulation_modules" in report["sections"]
    assert "weighted_mode" in report["sections"]["simulation_modules"]


def test_cli_runs_and_writes_output(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/release/full_reproducibility_report.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
        cwd=str(tmp_path),
    )
    if result.returncode != 0:
        # Run from repo root instead
        repo_root = Path(__file__).resolve().parents[2]
        result = subprocess.run(
            [sys.executable, "scripts/release/full_reproducibility_report.py"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
            cwd=str(repo_root),
        )
    assert result.returncode == 0
    assert "full_reproducibility" in result.stdout


def test_report_phases_all_complete():
    report = build_report()
    for phase, done in report["phases_completed"].items():
        assert done, f"{phase} not complete"
