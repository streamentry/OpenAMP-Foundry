"""Tests for the negative-result archive validator."""

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.validate_negative_archive import validate_archive


def _make_archive(tmp: Path, rows: list[dict]) -> str:
    p = tmp / "archive.csv"
    with p.open("w", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    return str(p)


_VALID_ROW = {
    "entry_id": "1",
    "date": "2026-08-01",
    "candidate_id": "WAVE0.5-001",
    "sequence": "ACDEFGHIKLMNPQRSTVWY",
    "reason_category": "lab_inactive",
    "reason_detail": "MIC > 64 ug/mL",
    "pipeline_version": "v0.5.49",
    "source_batch": "wave0.5",
    "assay_type": "MIC",
    "assay_result": "128",
    "assay_unit": "ug/mL",
    "score_activity": "0.85",
    "score_safety": "0.79",
    "score_novelty": "0.88",
    "score_ensemble": "0.83",
    "recalibration_used": "no",
    "superseded_by": "",
    "reviewer_notes": "",
}


def test_valid_entry():
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_archive(_make_archive(Path(tmp), [_VALID_ROW]))
        assert result["all_valid"] is True
        assert result["valid"] == 1


def test_missing_required_field():
    row = dict(_VALID_ROW)
    del row["candidate_id"]
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_archive(_make_archive(Path(tmp), [row]))
        assert result["all_valid"] is False
        assert result["errors"] == 1


def test_invalid_category():
    row = dict(_VALID_ROW, reason_category="invalid_cat")
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_archive(_make_archive(Path(tmp), [row]))
        assert result["all_valid"] is False


def test_invalid_date():
    row = dict(_VALID_ROW, date="not-a-date")
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_archive(_make_archive(Path(tmp), [row]))
        assert result["all_valid"] is False


def test_conditional_fields_warning():
    row = dict(_VALID_ROW, assay_type="", assay_result="", assay_unit="")
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_archive(_make_archive(Path(tmp), [row]))
        assert result["warnings"] >= 1


def test_superseded_refers_to_existing():
    rows = [
        dict(_VALID_ROW, entry_id="1", superseded_by=""),
        dict(_VALID_ROW, entry_id="2", superseded_by="1"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_archive(_make_archive(Path(tmp), rows))
        assert result["all_valid"] is True


def test_superseded_refers_to_nonexistent():
    rows = [
        dict(_VALID_ROW, entry_id="1", superseded_by="999"),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        result = validate_archive(_make_archive(Path(tmp), rows))
        assert result["warnings"] >= 1


def test_empty_archive():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "empty.csv"
        # CSV with only header
        with p.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(list(_VALID_ROW.keys()))
        result = validate_archive(str(p))
        assert "error" in result or result["total_rows"] == 0


def test_missing_file():
    result = validate_archive("/nonexistent.csv")
    assert "error" in result


def test_cli_exit_valid(tmp_path):
    p = _make_archive(tmp_path, [_VALID_ROW])
    r = subprocess.run(
        [sys.executable, "scripts/validate_negative_archive.py",
         "--archive", p],
        capture_output=True, text=True,
    )
    assert r.returncode == 0


def test_cli_exit_invalid(tmp_path):
    row = dict(_VALID_ROW, reason_category="")
    p = _make_archive(tmp_path, [row])
    r = subprocess.run(
        [sys.executable, "scripts/validate_negative_archive.py",
         "--archive", p],
        capture_output=True, text=True,
    )
    assert r.returncode == 3


def test_cli_writes_output(tmp_path):
    p = _make_archive(tmp_path, [_VALID_ROW])
    out = tmp_path / "report.json"
    subprocess.run(
        [sys.executable, "scripts/validate_negative_archive.py",
         "--archive", p, "--out", str(out)],
        capture_output=True,
        env={"PYTHONPATH": "src"},
    )
    assert out.exists()
    data = json.loads(out.read_text())
    assert "valid" in data
