"""Tests for the A3 first-run report generator (tests/cli/test_first_run_report.py)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from openamp_foundry.cli.commands.first_run_report import (
    _CLAIM_BOUNDARY_NOTICE,
    _DEFAULT_OUTPUTS_DIR,
    _count_certs,
    _count_jsonl_lines,
    _read_manifest,
    _report_exists,
    build_first_run_report,
    format_first_run_report,
    _run_first_run_report,
)


class TestCountJsonlLines:
    def test_missing_file_returns_zero(self, tmp_path):
        result = _count_jsonl_lines(tmp_path / "missing.jsonl")
        assert result == 0

    def test_empty_file_returns_zero(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("")
        assert _count_jsonl_lines(p) == 0

    def test_single_line_returns_one(self, tmp_path):
        p = tmp_path / "single.jsonl"
        p.write_text('{"a": 1}\n')
        assert _count_jsonl_lines(p) == 1

    def test_multiple_lines_counted(self, tmp_path):
        p = tmp_path / "multi.jsonl"
        p.write_text('{"a": 1}\n{"b": 2}\n{"c": 3}\n')
        assert _count_jsonl_lines(p) == 3

    def test_blank_lines_not_counted(self, tmp_path):
        p = tmp_path / "blanks.jsonl"
        p.write_text('{"a": 1}\n\n{"b": 2}\n')
        assert _count_jsonl_lines(p) == 2

    def test_returns_int(self, tmp_path):
        p = tmp_path / "test.jsonl"
        p.write_text('{"x": 0}\n')
        assert isinstance(_count_jsonl_lines(p), int)


class TestReadManifest:
    def test_missing_file_returns_empty_dict(self, tmp_path):
        result = _read_manifest(tmp_path / "missing.json")
        assert result == {}

    def test_valid_json_returned(self, tmp_path):
        p = tmp_path / "manifest.json"
        p.write_text('{"run_id": "abc", "ts": "2026-01-01"}')
        result = _read_manifest(p)
        assert result["run_id"] == "abc"

    def test_invalid_json_returns_empty(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("not valid json {{")
        result = _read_manifest(p)
        assert result == {}

    def test_empty_file_returns_empty(self, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text("")
        result = _read_manifest(p)
        assert result == {}

    def test_returns_dict(self, tmp_path):
        p = tmp_path / "m.json"
        p.write_text('{}')
        assert isinstance(_read_manifest(p), dict)

    def test_nested_keys_preserved(self, tmp_path):
        p = tmp_path / "nest.json"
        data = {"a": {"b": 1}}
        p.write_text(json.dumps(data))
        result = _read_manifest(p)
        assert result["a"]["b"] == 1


class TestCountCerts:
    def test_missing_dir_returns_zero(self, tmp_path):
        result = _count_certs(tmp_path / "no_such_dir")
        assert result == 0

    def test_empty_dir_returns_zero(self, tmp_path):
        d = tmp_path / "certs"
        d.mkdir()
        assert _count_certs(d) == 0

    def test_one_file_returns_one(self, tmp_path):
        d = tmp_path / "certs"
        d.mkdir()
        (d / "cert1.json").write_text("{}")
        assert _count_certs(d) == 1

    def test_multiple_files_counted(self, tmp_path):
        d = tmp_path / "certs"
        d.mkdir()
        for i in range(5):
            (d / f"cert{i}.json").write_text("{}")
        assert _count_certs(d) == 5

    def test_subdirs_not_counted(self, tmp_path):
        d = tmp_path / "certs"
        d.mkdir()
        (d / "subdir").mkdir()
        (d / "cert1.json").write_text("{}")
        assert _count_certs(d) == 1

    def test_returns_int(self, tmp_path):
        d = tmp_path / "certs"
        d.mkdir()
        assert isinstance(_count_certs(d), int)


class TestReportExists:
    def test_missing_file_returns_false(self, tmp_path):
        assert _report_exists(tmp_path / "missing.md") is False

    def test_empty_file_returns_false(self, tmp_path):
        p = tmp_path / "empty.md"
        p.write_text("")
        assert _report_exists(p) is False

    def test_nonempty_file_returns_true(self, tmp_path):
        p = tmp_path / "report.md"
        p.write_text("# Report\n")
        assert _report_exists(p) is True

    def test_returns_bool(self, tmp_path):
        p = tmp_path / "r.md"
        p.write_text("x")
        assert isinstance(_report_exists(p), bool)


class TestBuildFirstRunReport:
    def test_returns_dict(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert isinstance(result, dict)

    def test_has_required_keys(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        for key in ["outputs_dir", "demo_run_found", "candidate_count",
                    "cert_count", "report_exists", "manifest_keys",
                    "claim_boundary_notice", "sections"]:
            assert key in result

    def test_empty_dir_demo_not_found(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["demo_run_found"] is False

    def test_empty_dir_candidate_count_zero(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["candidate_count"] == 0

    def test_empty_dir_cert_count_zero(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["cert_count"] == 0

    def test_empty_dir_report_exists_false(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["report_exists"] is False

    def test_with_ranked_file_demo_found(self, tmp_path):
        (tmp_path / "demo_ranked.jsonl").write_text('{"score": 0.9}\n')
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["demo_run_found"] is True

    def test_with_ranked_file_count_correct(self, tmp_path):
        (tmp_path / "demo_ranked.jsonl").write_text(
            '{"a": 1}\n{"b": 2}\n{"c": 3}\n'
        )
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["candidate_count"] == 3

    def test_with_cert_dir_cert_count(self, tmp_path):
        cert_dir = tmp_path / "evidence"
        cert_dir.mkdir()
        (cert_dir / "c1.json").write_text("{}")
        (cert_dir / "c2.json").write_text("{}")
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["cert_count"] == 2

    def test_with_report_file_report_exists_true(self, tmp_path):
        (tmp_path / "demo_report.md").write_text("# Report\n")
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["report_exists"] is True

    def test_with_manifest_keys_listed(self, tmp_path):
        (tmp_path / "run_manifest.json").write_text(
            '{"run_id": "abc", "ts": "2026"}'
        )
        result = build_first_run_report(outputs_dir=tmp_path)
        assert "run_id" in result["manifest_keys"]

    def test_claim_boundary_in_report(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["claim_boundary_notice"] == _CLAIM_BOUNDARY_NOTICE

    def test_claim_boundary_in_sections(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert any(_CLAIM_BOUNDARY_NOTICE in s for s in result["sections"])

    def test_sections_is_list(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert isinstance(result["sections"], list)

    def test_no_outputs_section_mentions_make_demo(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert any("make demo" in s for s in result["sections"])

    def test_outputs_dir_in_result(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert str(tmp_path) in result["outputs_dir"]

    def test_default_outputs_dir_used_when_none(self):
        result = build_first_run_report(outputs_dir=None)
        assert "outputs" in result["outputs_dir"]

    def test_manifest_keys_empty_when_no_manifest(self, tmp_path):
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["manifest_keys"] == []

    def test_full_demo_output_found(self, tmp_path):
        (tmp_path / "demo_ranked.jsonl").write_text('{"s": 0.9}\n')
        cert_dir = tmp_path / "evidence"
        cert_dir.mkdir()
        (cert_dir / "c1.json").write_text("{}")
        (tmp_path / "demo_report.md").write_text("# Demo\n")
        (tmp_path / "run_manifest.json").write_text('{"run_id": "xyz"}')
        result = build_first_run_report(outputs_dir=tmp_path)
        assert result["demo_run_found"] is True
        assert result["candidate_count"] == 1
        assert result["cert_count"] == 1
        assert result["report_exists"] is True
        assert "run_id" in result["manifest_keys"]


class TestFormatFirstRunReport:
    def test_returns_string(self, tmp_path):
        report = build_first_run_report(outputs_dir=tmp_path)
        result = format_first_run_report(report)
        assert isinstance(result, str)

    def test_header_present(self, tmp_path):
        report = build_first_run_report(outputs_dir=tmp_path)
        result = format_first_run_report(report)
        assert "OpenAMP Foundry" in result

    def test_first_run_report_in_header(self, tmp_path):
        report = build_first_run_report(outputs_dir=tmp_path)
        result = format_first_run_report(report)
        assert "First-Run Report" in result

    def test_walkthrough_link_present(self, tmp_path):
        report = build_first_run_report(outputs_dir=tmp_path)
        result = format_first_run_report(report)
        assert "FIRST_RUN_WALKTHROUGH" in result

    def test_claim_boundary_in_output(self, tmp_path):
        report = build_first_run_report(outputs_dir=tmp_path)
        result = format_first_run_report(report)
        assert "dry-lab only" in result

    def test_sections_present_in_output(self, tmp_path):
        report = build_first_run_report(outputs_dir=tmp_path)
        result = format_first_run_report(report)
        for section in report["sections"]:
            assert section in result


class TestRunFirstRunReportCLI:
    def test_returns_zero(self, tmp_path):
        import types
        args = types.SimpleNamespace(outputs_dir=str(tmp_path))
        result = _run_first_run_report(args)
        assert result == 0

    def test_prints_output(self, tmp_path, capsys):
        import types
        args = types.SimpleNamespace(outputs_dir=str(tmp_path))
        _run_first_run_report(args)
        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_output_contains_header(self, tmp_path, capsys):
        import types
        args = types.SimpleNamespace(outputs_dir=str(tmp_path))
        _run_first_run_report(args)
        captured = capsys.readouterr()
        assert "OpenAMP Foundry" in captured.out

    def test_no_outputs_dir_attribute_uses_default(self, capsys):
        import types
        args = types.SimpleNamespace()
        result = _run_first_run_report(args)
        assert result == 0

    def test_output_contains_claim_notice(self, tmp_path, capsys):
        import types
        args = types.SimpleNamespace(outputs_dir=str(tmp_path))
        _run_first_run_report(args)
        captured = capsys.readouterr()
        assert "dry-lab only" in captured.out


class TestConstants:
    def test_claim_boundary_notice_is_str(self):
        assert isinstance(_CLAIM_BOUNDARY_NOTICE, str)

    def test_claim_boundary_mentions_dry_lab(self):
        assert "dry-lab only" in _CLAIM_BOUNDARY_NOTICE

    def test_claim_boundary_mentions_not_biological(self):
        assert "NOT biological" in _CLAIM_BOUNDARY_NOTICE

    def test_default_outputs_dir_is_path(self):
        assert isinstance(_DEFAULT_OUTPUTS_DIR, Path)

    def test_default_outputs_dir_name(self):
        assert _DEFAULT_OUTPUTS_DIR.name == "outputs"

    def test_claim_boundary_mentions_computational(self):
        assert "computational" in _CLAIM_BOUNDARY_NOTICE
