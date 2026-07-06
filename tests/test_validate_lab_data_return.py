"""Tests for the data-return validation tool."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.validate_lab_data_return import validate_lab_results_dir


def _make_valid_result(tmp: Path, cid: str = "C1", at: str = "MIC") -> Path:
    d = tmp / "results"
    d.mkdir(exist_ok=True)
    data = {
        "result_id": f"{cid}_{at}_001",
        "candidate_id": cid,
        "assay_type": at,
        "organism_or_cell_line": "Escherichia coli ATCC 25922",
        "result_value": 8.0,
        "result_unit": "ug/mL",
        "positive_control_passed": True,
        "negative_control_passed": True,
        "assay_date": "2026-08-15",
        "replicate_count": 3,
        "performed_by_lab": "Test Lab",
        "computational_candidate_certificate_hash": "abc123",
        "disclaimer": "SYNTHETIC TEST DATA",
    }
    fp = d / f"{cid}_{at}.json"
    fp.write_text(json.dumps(data))
    return d


def test_validates_pass():
    with tempfile.TemporaryDirectory() as tmp:
        d = _make_valid_result(Path(tmp), "C1")
        result = validate_lab_results_dir(str(d))
        assert "error" not in result
        assert result["passed"] == 1
        assert result["all_pass"] is True


def test_validates_multiple():
    with tempfile.TemporaryDirectory() as tmp:
        d = _make_valid_result(Path(tmp), "C1")
        _make_valid_result(Path(tmp), "C2")
        result = validate_lab_results_dir(str(d))
        assert result["passed"] == 2
        assert result["failed"] == 0


def test_detects_missing_required_field():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "results"
        d.mkdir()
        (d / "bad.json").write_text(json.dumps({"candidate_id": "C1"}))
        result = validate_lab_results_dir(str(d))
        assert result["failed"] == 1


def test_detects_invalid_json():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "results"
        d.mkdir()
        (d / "bad.json").write_text("not valid json")
        result = validate_lab_results_dir(str(d))
        assert result["failed"] == 1
        assert "Invalid JSON" in result["per_file"]["failed"][0]["errors"]


def test_error_missing_dir():
    result = validate_lab_results_dir("/nonexistent")
    assert "error" in result


def test_error_no_json_files():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "results"
        d.mkdir()
        (d / "readme.txt").write_text("hello")
        result = validate_lab_results_dir(str(d))
        assert "error" in result


def test_cli_pass():
    with tempfile.TemporaryDirectory() as tmp:
        d = _make_valid_result(Path(tmp), "C1")
        r = subprocess.run(
            [sys.executable, "scripts/validate_lab_data_return.py",
             "--results-dir", str(d)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert "Passed: 1" in r.stdout


def test_cli_fail():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "results"
        d.mkdir()
        (d / "bad.json").write_text("invalid")
        r = subprocess.run(
            [sys.executable, "scripts/validate_lab_data_return.py",
             "--results-dir", str(d)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 3
