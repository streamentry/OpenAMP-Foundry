"""Tests for the full reproducibility report."""

import subprocess
import sys
from pathlib import Path

from scripts.full_reproducibility_report import build_report


def test_report_builds():
    report = build_report()
    assert report["report_type"] == "full_reproducibility"
    assert report["loops_completed"] == 49
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
        [sys.executable, "scripts/full_reproducibility_report.py"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
        cwd=str(tmp_path),
    )
    if result.returncode != 0:
        # Run from repo root instead
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "scripts/full_reproducibility_report.py"],
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
