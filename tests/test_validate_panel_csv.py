"""Tests for panel CSV validator."""
import csv
import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.validate_panel_csv import validate_panel_csv


def _make_csv(tmp, rows):
    p = Path(tmp) / "panel.csv"
    with p.open("w", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    return str(p)


def test_valid_panel(tmp_path):
    p = _make_csv(tmp_path, [{"candidate_id": "C1", "sequence": "ACDEFGHIKL"}])
    r = validate_panel_csv(p)
    assert r["all_valid"] is True


def test_missing_required_column(tmp_path):
    p = _make_csv(tmp_path, [{"candidate_id": "C1"}])
    r = validate_panel_csv(p)
    assert "error" in r or r["row_errors"] > 0


def test_missing_candidate_id(tmp_path):
    p = _make_csv(tmp_path, [{"candidate_id": "", "sequence": "AAAA"}])
    r = validate_panel_csv(p)
    assert r["row_errors"] > 0


def test_invalid_amino_acid(tmp_path):
    p = _make_csv(tmp_path, [{"candidate_id": "C1", "sequence": "ACB"}] )
    r = validate_panel_csv(p)
    assert r["row_errors"] > 0


def test_missing_file():
    r = validate_panel_csv("/nonexistent.csv")
    assert "error" in r


def test_empty_csv(tmp_path):
    p = Path(tmp_path) / "empty.csv"
    p.write_text("candidate_id,sequence\n")
    r = validate_panel_csv(str(p))
    assert r["total_rows"] == 0


def test_cli_valid(tmp_path):
    p = _make_csv(tmp_path, [{"candidate_id": "C1", "sequence": "ACDEFGHIKL"}])
    res = subprocess.run([sys.executable, "scripts/validate_panel_csv.py", "--csv", p],
                         capture_output=True, text=True)
    assert res.returncode == 0


def test_cli_invalid(tmp_path):
    p = _make_csv(tmp_path, [{"candidate_id": "", "sequence": ""}])
    res = subprocess.run([sys.executable, "scripts/validate_panel_csv.py", "--csv", p],
                         capture_output=True, text=True)
    assert res.returncode == 3
