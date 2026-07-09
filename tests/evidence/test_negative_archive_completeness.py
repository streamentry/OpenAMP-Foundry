"""Tests for the negative-result archive completeness checker."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check_negative_archive_completeness import (
    check_archive,
    generate_markdown,
    load_entries,
)

_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "negative_result_archive_example.json"
)


def _valid_entry(overrides: dict | None = None) -> dict:
    entry = {
        "entry_id": 1,
        "date": "2026-06-01",
        "candidate_id": "TEST-001",
        "sequence": "RRIRIIRRIRIIRRI",
        "reason_category": "lab_inactive",
        "reason_detail": "MIC > 128 ug/mL.",
        "pipeline_version": "v0.5.70",
        "source_batch": "test",
        "assay_result": ">128",
        "score_safety": 0.35,
    }
    if overrides:
        entry.update(overrides)
    return entry


def _valid_entries() -> list[dict]:
    return [
        _valid_entry({"entry_id": 1, "candidate_id": "TEST-001"}),
        _valid_entry({
            "entry_id": 2,
            "candidate_id": "TEST-002",
            "assay_result": ">256",
            "score_safety": 0.88,
            "reviewer_notes": "Confirmed inactive.",
        }),
    ]


class TestCheckArchive:
    def test_all_valid_entries_pass(self):
        entries = _valid_entries()
        report = check_archive(entries)
        assert report["summary"]["total_entries"] == 2
        assert report["summary"]["fail_count"] == 0
        assert report["summary"]["pass_count"] == 2
        for check in report["checks"].values():
            assert check["pass"] is True

    def test_missing_required_field_detected(self):
        entries = [_valid_entry({"candidate_id": None})]
        report = check_archive(entries)
        assert report["summary"]["fail_count"] == 1
        assert report["checks"]["required_fields"]["pass"] is False
        detail = report["checks"]["required_fields"]["details"][0]
        assert "required field" in detail
        assert "candidate_id" in detail

    def test_duplicate_candidate_id_detected(self):
        entries = [
            _valid_entry({"entry_id": 1, "candidate_id": "DUP-001"}),
            _valid_entry({"entry_id": 2, "candidate_id": "DUP-001"}),
        ]
        report = check_archive(entries)
        assert report["checks"]["duplicate_candidate_ids"]["pass"] is False
        detail = report["checks"]["duplicate_candidate_ids"]["details"][0]
        assert "Duplicate" in detail
        assert "DUP-001" in detail

    def test_no_content_fields_detected(self):
        entries = [_valid_entry({
            "assay_result": None,
            "score_safety": None,
            "reviewer_notes": None,
            "reason_detail": "",
        })]
        report = check_archive(entries)
        assert report["summary"]["fail_count"] == 1
        assert report["checks"]["has_content_fields"]["pass"] is False
        detail = report["checks"]["has_content_fields"]["details"][0]
        assert "content field" in detail

    def test_invalid_date_format_detected(self):
        entries = [_valid_entry({"date": "01-06-2026"})]
        report = check_archive(entries)
        assert report["checks"]["date_format"]["pass"] is False
        detail = report["checks"]["date_format"]["details"][0]
        assert "date format" in detail

    def test_invalid_calendar_date_detected(self):
        entries = [_valid_entry({"date": "2026-13-01"})]
        report = check_archive(entries)
        assert report["checks"]["date_format"]["pass"] is False
        detail = report["checks"]["date_format"]["details"][0]
        assert "calendar date" in detail or "date format" in detail

    def test_invalid_intake_report_id_detected(self):
        entries = [_valid_entry({"intake_report_id": "INVALID-REF"})]
        report = check_archive(entries)
        assert report["checks"]["intake_report_id_references"]["pass"] is False
        detail = report["checks"]["intake_report_id_references"]["details"][0]
        assert "intake_report_id" in detail

    def test_valid_intake_report_id_passes(self):
        entries = [_valid_entry({"intake_report_id": "INT-2026-001"})]
        report = check_archive(entries)
        assert report["checks"]["intake_report_id_references"]["pass"] is True

    def test_mixed_good_and_bad_entries(self):
        entries = [
            _valid_entry({"entry_id": 1, "candidate_id": "GOOD-001"}),
            _valid_entry({"entry_id": 2, "candidate_id": "BAD-001", "date": "bad-date"}),
        ]
        report = check_archive(entries)
        assert report["summary"]["pass_count"] == 1
        assert report["summary"]["fail_count"] == 1
        assert report["per_entry_results"][0]["pass"] is True
        assert report["per_entry_results"][1]["pass"] is False

    def test_empty_string_required_field_detected(self):
        entries = [_valid_entry({"sequence": ""})]
        report = check_archive(entries)
        assert report["summary"]["fail_count"] == 1
        assert report["checks"]["required_fields"]["pass"] is False

    def test_single_reason_detail_is_enough_content(self):
        entries = [_valid_entry({
            "assay_result": None,
            "score_safety": None,
            "reviewer_notes": None,
        })]
        entries[0]["reason_detail"] = "MIC > 128 ug/mL."
        report = check_archive(entries)
        assert report["checks"]["has_content_fields"]["pass"] is True


class TestCheckArchiveStructure:
    def test_report_has_required_keys(self):
        report = check_archive(_valid_entries())
        assert "report_metadata" in report
        assert "summary" in report
        assert "checks" in report
        assert "per_entry_results" in report
        assert "_caveat" in report

    def test_checks_has_five_keys(self):
        report = check_archive(_valid_entries())
        assert set(report["checks"].keys()) == {
            "required_fields",
            "duplicate_candidate_ids",
            "has_content_fields",
            "date_format",
            "intake_report_id_references",
        }

    def test_summary_has_pass_rate(self):
        report = check_archive(_valid_entries())
        assert "pass_rate" in report["summary"]
        assert "%" in report["summary"]["pass_rate"]

    def test_per_entry_results_match_entry_count(self):
        entries = _valid_entries()
        report = check_archive(entries)
        assert len(report["per_entry_results"]) == len(entries)

    def test_empty_entries_raises_system_exit(self):
        with pytest.raises(SystemExit) as exc:
            load_entries("[]")
        assert exc.value.code == 2

    def test_missing_file_raises_system_exit(self):
        with pytest.raises(SystemExit) as exc:
            load_entries("/nonexistent/path.json")
        assert exc.value.code == 2


class TestGenerateMarkdown:
    def test_markdown_has_title(self):
        report = check_archive(_valid_entries())
        md = generate_markdown(report)
        assert "# Negative-Result Archive Completeness Report" in md

    def test_markdown_has_summary_table(self):
        report = check_archive(_valid_entries())
        md = generate_markdown(report)
        assert "## Summary" in md
        assert "Total entries" in md
        assert "Pass rate" in md

    def test_markdown_has_check_results_table(self):
        report = check_archive(_valid_entries())
        md = generate_markdown(report)
        assert "## Check Results" in md
        assert "required_fields" in md
        assert "duplicate_candidate_ids" in md

    def test_markdown_has_caveat(self):
        report = check_archive(_valid_entries())
        md = generate_markdown(report)
        assert "## Caveat" in md
        assert report["_caveat"] in md

    def test_markdown_includes_errors_for_failed_checks(self):
        entries = [_valid_entry({"date": "bad-date"})]
        report = check_archive(entries)
        md = generate_markdown(report)
        assert "## Detailed Errors" in md
        assert "bad-date" in md


class TestExampleFile:
    def test_example_file_loads(self):
        entries = load_entries(str(_EXAMPLE_PATH))
        assert len(entries) > 0

    def test_example_file_all_passes(self):
        entries = load_entries(str(_EXAMPLE_PATH))
        report = check_archive(entries)
        assert report["summary"]["fail_count"] == 0

    def test_example_file_report_structure(self):
        entries = load_entries(str(_EXAMPLE_PATH))
        report = check_archive(entries)
        assert report["summary"]["total_entries"] == 4
        for check in report["checks"].values():
            assert check["pass"] is True


class TestLoadEntries:
    def test_load_from_list(self, tmp_path):
        path = tmp_path / "entries.json"
        entries_data = [_valid_entry()]
        path.write_text(json.dumps(entries_data))
        result = load_entries(str(path))
        assert len(result) == 1

    def test_load_from_dict_with_entries_key(self, tmp_path):
        path = tmp_path / "entries.json"
        path.write_text(json.dumps({"entries": [_valid_entry()]}))
        result = load_entries(str(path))
        assert len(result) == 1

    def test_load_empty_list_raises(self, tmp_path):
        path = tmp_path / "entries.json"
        path.write_text("[]")
        with pytest.raises(SystemExit) as exc:
            load_entries(str(path))
        assert exc.value.code == 2

    def test_load_missing_file_raises(self):
        with pytest.raises(SystemExit) as exc:
            load_entries("/tmp/nonexistent_test_file.json")
        assert exc.value.code == 2

    def test_load_invalid_json_raises(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json")
        with pytest.raises(SystemExit) as exc:
            load_entries(str(path))
        assert exc.value.code == 2

    def test_load_dict_without_entries_raises(self, tmp_path):
        path = tmp_path / "entries.json"
        path.write_text(json.dumps({"not_entries": []}))
        with pytest.raises(SystemExit) as exc:
            load_entries(str(path))
        assert exc.value.code == 2


class TestCLI:
    def test_cli_exit_0_all_valid(self):
        r = subprocess.run(
            [
                sys.executable, str(_EXAMPLE_PATH.parents[1] / "scripts" / "check_negative_archive_completeness.py"),
                "--input", str(_EXAMPLE_PATH),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0

    def test_cli_exit_2_missing_file(self):
        r = subprocess.run(
            [
                sys.executable, str(_EXAMPLE_PATH.parents[1] / "scripts" / "check_negative_archive_completeness.py"),
                "--input", "/tmp/nonexistent_test.json",
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_cli_writes_json_output(self, tmp_path):
        out_json = tmp_path / "report.json"
        r = subprocess.run(
            [
                sys.executable, str(_EXAMPLE_PATH.parents[1] / "scripts" / "check_negative_archive_completeness.py"),
                "--input", str(_EXAMPLE_PATH),
                "--out-json", str(out_json),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_json.exists()
        data = json.loads(out_json.read_text())
        assert "summary" in data

    def test_cli_writes_markdown_output(self, tmp_path):
        out_md = tmp_path / "report.md"
        r = subprocess.run(
            [
                sys.executable, str(_EXAMPLE_PATH.parents[1] / "scripts" / "check_negative_archive_completeness.py"),
                "--input", str(_EXAMPLE_PATH),
                "--out-md", str(out_md),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_md.exists()
        content = out_md.read_text()
        assert "Negative-Result Archive Completeness Report" in content
