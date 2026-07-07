"""Tests for missing-file error behavior across CLI commands.

Verifies that commands fail with clear, actionable messages
when required input files are missing.
"""

import subprocess
import sys

import pytest

ROOT = "."


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", *args],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
        cwd=ROOT,
    )


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, script, *args],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
        cwd=ROOT,
    )


class TestRank:
    def test_missing_candidates(self):
        r = _run("rank", "--candidates", "/nonexistent.csv", "--out", "/tmp/out.jsonl")
        assert r.returncode != 0

    def test_missing_config(self):
        r = _run("rank", "--candidates", "examples/sequences/demo_candidates.csv",
                 "--config", "/nonexistent.yaml", "--out", "/tmp/out.jsonl")
        assert r.returncode != 0


class TestValidate:
    def test_missing_certificate(self):
        r = _run("validate", "--certificate", "/nonexistent.json",
                 "--schema", "schemas/candidate.schema.json")
        assert r.returncode != 0
        assert "nonexistent" in r.stdout.lower() or "nonexistent" in r.stderr.lower()

    def test_missing_schema(self):
        r = _run("validate", "--certificate", "schemas/candidate.schema.json",
                 "--schema", "/nonexistent.json")
        assert r.returncode != 0


class TestBench:
    def test_leakage_missing_candidates(self):
        r = _run("bench", "leakage", "--candidates", "/nonexistent.csv",
                 "--references", "examples/known_reference/demo_known_amps.csv")
        assert r.returncode != 0


class TestPilotPanel:
    def test_missing_ranked(self):
        r = _run("pilot-panel", "--ranked", "/nonexistent.jsonl", "--out", "/tmp/p.csv")
        assert r.returncode != 0


class TestCalibrationIntake:
    def test_missing_predictions(self):
        r = _run("calibration-intake", "--predictions", "/nonexistent.csv",
                 "--results-dir", "examples/lab_results", "--panel-name", "test")
        assert r.returncode != 0


class TestRankMissingRefs:
    def test_missing_references(self):
        r = _run("rank", "--candidates", "/nonexistent.csv",
                 "--references", "/nonexistent.csv", "--out", "/tmp/out.jsonl")
        assert r.returncode != 0


class TestPassFailCheck:
    def test_missing_results_dir(self):
        r = _run_script("scripts/check_wave1_pass_fail.py", "--results-dir", "/nonexistent")
        assert r.returncode == 2

    def test_missing_criteria(self):
        r = _run_script("scripts/check_wave1_pass_fail.py",
                        "--results-dir", "examples/lab_results",
                        "--criteria", "/nonexistent.yaml")
        assert r.returncode == 2


class TestValidateLabData:
    def test_missing_dir(self):
        r = _run_script("scripts/validate_lab_data_return.py", "--results-dir", "/nonexistent")
        assert r.returncode == 2


class TestNegativeArchive:
    def test_missing_archive(self):
        r = _run_script("scripts/validate_negative_archive.py", "--archive", "/nonexistent.csv")
        assert "error" in r.stdout.lower() or r.returncode != 0
