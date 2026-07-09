"""Tests for the bulk rejection-event validator."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.validate_rejection_events import (
    build_report,
    generate_markdown,
    load_taxonomy_codes,
    validate_events,
)

_TAXONOMY_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "rejection_taxonomy_example.json"
)


def _taxonomy_codes() -> set[str]:
    return load_taxonomy_codes(_TAXONOMY_PATH)


_VALID_EVENT: dict = {
    "candidate_id": "WAVE0.5-001",
    "rejection_code": "PIPE_ACTIVITY_LOW",
    "date": "2026-07-09",
    "pipeline_version": "v0.5.78",
    "notes": "Activity score 0.42 below minimum threshold 0.50.",
}


class TestLoadTaxonomyCodes:
    def test_returns_set_of_codes(self):
        codes = _taxonomy_codes()
        assert isinstance(codes, set)
        assert len(codes) > 0
        assert "PIPE_ACTIVITY_LOW" in codes

    def test_includes_all_example_codes(self):
        codes = _taxonomy_codes()
        expected = {
            "PRE_SEQ_INVALID", "PIPE_ACTIVITY_LOW", "PIPE_SAFETY_LOW",
            "DIV_TOO_SIMILAR", "REV_EXPERT_REJECT", "LAB_INACTIVE",
            "LAB_TOXIC", "LIFECYCLE_WITHDRAWN",
        }
        assert expected.issubset(codes), f"Missing: {expected - codes}"


class TestValidateEvents:
    def test_valid_event_passes(self):
        result = validate_events([_VALID_EVENT], _taxonomy_codes())
        assert result["summary"]["all_valid"] is True
        assert result["summary"]["valid"] == 1
        assert result["summary"]["invalid"] == 0

    def test_multiple_valid_events(self):
        events = [
            dict(_VALID_EVENT),
            dict(_VALID_EVENT, candidate_id="WAVE0.5-002", rejection_code="LAB_INACTIVE"),
        ]
        result = validate_events(events, _taxonomy_codes())
        assert result["summary"]["valid"] == 2
        assert result["summary"]["all_valid"] is True

    def test_missing_candidate_id_fails(self):
        event = dict(_VALID_EVENT)
        del event["candidate_id"]
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False
        assert len(result["errors"]) == 1
        assert any(
            "Missing required field" in e
            and "candidate_id" in e
            for err in result["errors"]
            for e in err["errors"]
        )

    def test_missing_rejection_code_fails(self):
        event = dict(_VALID_EVENT)
        del event["rejection_code"]
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False

    def test_missing_date_fails(self):
        event = dict(_VALID_EVENT)
        del event["date"]
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False

    def test_missing_pipeline_version_fails(self):
        event = dict(_VALID_EVENT)
        del event["pipeline_version"]
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False

    def test_unknown_rejection_code_fails(self):
        event = dict(_VALID_EVENT, rejection_code="NOT_A_REAL_CODE")
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False
        assert any(
            "Unknown rejection_code" in e
            for err in result["errors"]
            for e in err["errors"]
        )

    def test_invalid_date_format_fails(self):
        event = dict(_VALID_EVENT, date="07-09-2026")
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False
        assert any(
            "Invalid date format" in e
            for err in result["errors"]
            for e in err["errors"]
        )

    def test_empty_string_fields_fail(self):
        event = dict(
            _VALID_EVENT,
            candidate_id="",
            rejection_code="",
            date="",
            pipeline_version="",
        )
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False
        assert result["summary"]["invalid"] == 1

    def test_empty_events_list(self):
        result = validate_events([], _taxonomy_codes())
        assert result["summary"]["valid"] == 0
        assert result["summary"]["all_valid"] is True

    def test_multiple_errors_per_event(self):
        event = dict(_VALID_EVENT, candidate_id="", rejection_code="BAD_CODE", date="bad-date")
        result = validate_events([event], _taxonomy_codes())
        assert result["summary"]["all_valid"] is False
        assert len(result["errors"]) == 1
        assert len(result["errors"][0]["errors"]) >= 2


class TestBuildReport:
    def test_returns_full_report_structure(self):
        result = build_report([_VALID_EVENT], _taxonomy_codes())
        assert "input" in result
        assert "summary" in result
        assert "errors" in result
        assert "rejection_code_summary" in result
        assert "_caveat" in result

    def test_rejection_code_summary_counts(self):
        events = [
            dict(_VALID_EVENT),
            dict(_VALID_EVENT, candidate_id="WAVE0.5-002", rejection_code="PIPE_ACTIVITY_LOW"),
            dict(_VALID_EVENT, candidate_id="WAVE0.5-003", rejection_code="LAB_INACTIVE"),
        ]
        result = build_report(events, _taxonomy_codes())
        assert result["rejection_code_summary"]["PIPE_ACTIVITY_LOW"] == 2
        assert result["rejection_code_summary"]["LAB_INACTIVE"] == 1


class TestGenerateMarkdown:
    def test_contains_title(self):
        result = build_report([_VALID_EVENT], _taxonomy_codes())
        md = generate_markdown(result)
        assert "# Rejection Event Validation Report" in md

    def test_includes_summary_counts(self):
        result = build_report([_VALID_EVENT], _taxonomy_codes())
        md = generate_markdown(result)
        assert "Total events" in md
        assert "Valid:" in md
        assert "Invalid:" in md

    def test_includes_errors_section_when_present(self):
        event = dict(_VALID_EVENT, candidate_id="")
        result = build_report([event], _taxonomy_codes())
        md = generate_markdown(result)
        assert "Errors" in md

    def test_includes_caveat(self):
        result = build_report([_VALID_EVENT], _taxonomy_codes())
        md = generate_markdown(result)
        assert "Caveat" in md


class TestCLI:
    def test_exit_zero_on_valid(self, tmp_path):
        events = [_VALID_EVENT]
        inp = tmp_path / "events.json"
        inp.write_text(json.dumps(events))
        r = subprocess.run(
            [sys.executable, "scripts/validate_rejection_events.py",
             "--input", str(inp)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0

    def test_exit_three_on_invalid(self, tmp_path):
        events = [dict(_VALID_EVENT, rejection_code="NOT_A_REAL_CODE")]
        inp = tmp_path / "events.json"
        inp.write_text(json.dumps(events))
        r = subprocess.run(
            [sys.executable, "scripts/validate_rejection_events.py",
             "--input", str(inp)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 3

    def test_exit_two_on_missing_input(self, tmp_path):
        r = subprocess.run(
            [sys.executable, "scripts/validate_rejection_events.py",
             "--input", str(tmp_path / "nonexistent.json")],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_exit_two_on_empty_list(self, tmp_path):
        inp = tmp_path / "empty.json"
        inp.write_text("[]")
        r = subprocess.run(
            [sys.executable, "scripts/validate_rejection_events.py",
             "--input", str(inp)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_exit_two_on_non_array(self, tmp_path):
        inp = tmp_path / "not_array.json"
        inp.write_text('{"not": "an array"}')
        r = subprocess.run(
            [sys.executable, "scripts/validate_rejection_events.py",
             "--input", str(inp)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_writes_json_output(self, tmp_path):
        events = [_VALID_EVENT]
        inp = tmp_path / "events.json"
        inp.write_text(json.dumps(events))
        out = tmp_path / "report.json"
        subprocess.run(
            [sys.executable, "scripts/validate_rejection_events.py",
             "--input", str(inp), "--out-json", str(out)],
            capture_output=True,
            env={"PYTHONPATH": "src"},
        )
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["summary"]["all_valid"] is True

    def test_writes_markdown_output(self, tmp_path):
        events = [_VALID_EVENT]
        inp = tmp_path / "events.json"
        inp.write_text(json.dumps(events))
        out = tmp_path / "report.md"
        subprocess.run(
            [sys.executable, "scripts/validate_rejection_events.py",
             "--input", str(inp), "--out-md", str(out)],
            capture_output=True,
            env={"PYTHONPATH": "src"},
        )
        assert out.exists()
        assert "# Rejection Event Validation Report" in out.read_text()
