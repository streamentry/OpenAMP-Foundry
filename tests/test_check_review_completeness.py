"""Tests for review request completeness checker."""
import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.check_review_completeness import check_completeness


def _make_request(tmp_path, data: dict) -> str:
    p = Path(tmp_path) / "request.json"
    p.write_text(json.dumps(data))
    return str(p)


def _valid_request():
    return {
        "request_id": "REV-001",
        "reviewer_role": "domain_expert",
        "artifact_refs": ["docs/review/EXPERT_REVIEW_PACK.md"],
        "claim_boundary": "Evaluate whether the candidate panel is credible",
        "decision_needed": "approve",
        "requested_by": "PI Name",
        "deadline": "2026-08-01",
        "context_notes": "First pilot panel review",
    }


def test_complete_request(tmp_path):
    r = check_completeness(_make_request(tmp_path, _valid_request()))
    assert r["is_complete"] is True


def test_missing_required_field(tmp_path):
    d = _valid_request()
    del d["decision_needed"]
    r = check_completeness(_make_request(tmp_path, d))
    assert r["is_complete"] is False


def test_empty_required_field(tmp_path):
    d = _valid_request()
    d["reviewer_role"] = ""
    r = check_completeness(_make_request(tmp_path, d))
    assert r["is_complete"] is False


def test_missing_multiple_fields(tmp_path):
    d = _valid_request()
    del d["artifact_refs"]
    del d["claim_boundary"]
    r = check_completeness(_make_request(tmp_path, d))
    assert len(r["missing_fields"]) >= 2


def test_missing_file():
    r = check_completeness("/nonexistent.json")
    assert "error" in r


def test_invalid_json(tmp_path):
    p = Path(tmp_path) / "bad.json"
    p.write_text("not json")
    r = check_completeness(str(p))
    assert "error" in r


def test_cli_valid(tmp_path):
    p = _make_request(tmp_path, _valid_request())
    res = subprocess.run([sys.executable, "scripts/check_review_completeness.py", "--request", p],
                         capture_output=True, text=True)
    assert res.returncode == 0


def test_cli_invalid(tmp_path):
    p = _make_request(tmp_path, {"id": "incomplete"})
    res = subprocess.run([sys.executable, "scripts/check_review_completeness.py", "--request", p],
                         capture_output=True, text=True)
    assert res.returncode == 3
