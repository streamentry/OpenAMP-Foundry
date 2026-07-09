"""Tests for the failed-candidate report generator (F4)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from scripts.generate_failed_candidate_report import (
    _get_taxonomy_codes,
    build_markdown_report,
    build_report,
    load_input,
    load_taxonomy,
    validate_rejection_codes,
)

PYTHON = sys.executable

_REPO_DIR = Path(__file__).parents[2]
_TAXONOMY_EXAMPLE = _REPO_DIR / "examples" / "rejection_taxonomy_example.json"
_SCHEMA_DIR = _REPO_DIR / "schemas"


def _sample_candidates() -> list[dict]:
    return [
        {
            "candidate_id": "CAND-001",
            "sequence": "ACDEFGHIKLMNPQRSTVWY",
            "rejections": [
                {"code": "PIPE_ACTIVITY_LOW", "detail": "Score 0.42 below 0.50"},
                {"code": "PIPE_SAFETY_LOW", "detail": "Score 0.31 below 0.50"},
            ],
        },
        {
            "candidate_id": "CAND-002",
            "sequence": "KLAKLAKKLAKLAK",
            "rejections": [
                {"code": "PIPE_ENSEMBLE_LOW", "detail": "Score 0.55 below 0.65"},
            ],
        },
        {
            "candidate_id": "CAND-003",
            "sequence": "RRWQWRMKKLG",
            "rejections": [
                {"code": "DIV_TOO_SIMILAR", "detail": "Similarity 0.82 above 0.70"},
            ],
        },
    ]


def _sample_input() -> dict:
    return {
        "source_batch": "test-batch",
        "pipeline_version": "v0.5.74-test",
        "date": "2026-07-09",
        "candidates": _sample_candidates(),
    }


def _taxonomy() -> list[dict]:
    return load_taxonomy(_TAXONOMY_EXAMPLE)


class TestFailedCandidateReport:
    def test_taxonomy_loads_valid(self):
        tax = _taxonomy()
        assert len(tax) >= 21
        codes = _get_taxonomy_codes(tax)
        assert "PIPE_ACTIVITY_LOW" in codes
        assert "PRE_SEQ_INVALID" in codes

    def test_validate_rejection_codes_valid(self):
        tax = _taxonomy()
        codes = _get_taxonomy_codes(tax)
        candidates = [
            {
                "candidate_id": "T-001",
                "rejections": [{"code": "PIPE_ACTIVITY_LOW"}],
            }
        ]
        errors = validate_rejection_codes(candidates, codes)
        assert errors == []

    def test_validate_rejection_codes_unknown(self):
        tax = _taxonomy()
        codes = _get_taxonomy_codes(tax)
        candidates = [
            {
                "candidate_id": "T-001",
                "rejections": [{"code": "NOT_A_REAL_CODE"}],
            }
        ]
        errors = validate_rejection_codes(candidates, codes)
        assert len(errors) == 1
        assert errors[0]["code"] == "NOT_A_REAL_CODE"
        assert "Unknown rejection code" in errors[0]["error"]

    def test_build_report_summary_counts(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test-batch",
            pipeline_version="v0.5.74-test",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        s = report["summary"]
        assert s["total_candidates"] == 3
        assert s["total_rejection_instances"] == 4
        assert s["total_unique_rejection_codes"] == 4

    def test_build_report_by_category(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        cat = report["summary"]["by_category"]
        assert "pipeline" in cat
        assert cat["pipeline"]["count"] >= 3
        assert "diversity" in cat
        assert cat["diversity"]["count"] >= 1

    def test_build_report_by_severity(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        sev = report["summary"]["by_severity"]
        assert "soft" in sev
        assert sev["soft"] >= 4

    def test_build_report_rejection_code_frequencies(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        freq = report["summary"]["rejection_code_frequencies"]
        assert freq["PIPE_ACTIVITY_LOW"] == 1
        assert freq["PIPE_SAFETY_LOW"] == 1
        assert freq["PIPE_ENSEMBLE_LOW"] == 1
        assert freq["DIV_TOO_SIMILAR"] == 1

    def test_build_report_metadata(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="wave0.5",
            pipeline_version="v0.5.74",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        meta = report["report_metadata"]
        assert meta["report_type"] == "failed_candidate_report"
        assert meta["source_batch"] == "wave0.5"
        assert meta["pipeline_version"] == "v0.5.74"
        assert meta["report_date"] == "2026-07-09"
        assert "generated_at" in meta

    def test_build_report_caveats(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        assert len(report["caveats"]) >= 5
        assert any("not biological proof" in c for c in report["caveats"])
        assert report["dry_lab_only"] is True

    def test_build_report_candidate_entries(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        candidates_out = report["candidates"]
        assert len(candidates_out) == 3
        c1 = candidates_out[0]
        assert c1["candidate_id"] == "CAND-001"
        assert c1["rejection_count"] == 2
        assert len(c1["rejections"]) == 2

    def test_build_report_rejection_enriches_with_taxonomy(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        r = report["candidates"][0]["rejections"][0]
        assert r["category"] == "pipeline"
        assert r["severity"] == "soft"
        assert r["evidence_impact"] == "downgrade_by_1"

    def test_build_markdown_contains_sections(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        md = build_markdown_report(report)
        assert "# Failed Candidate Report" in md
        assert "## Report Metadata" in md
        assert "## Summary" in md
        assert "## Per-Candidate Breakdown" in md
        assert "## Caveats" in md
        assert "CAND-001" in md
        assert "CAND-002" in md
        assert "CAND-003" in md

    def test_build_markdown_contains_caveats(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=_taxonomy(),
        )
        md = build_markdown_report(report)
        assert "not biological proof" in md
        assert "informational only" in md
        assert "dry-lab only" in md.lower()

    def test_load_input_valid(self):
        report = load_input(str(_TAXONOMY_EXAMPLE))
        assert isinstance(report, list)
        assert len(report) >= 1

    def test_load_input_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_input("/nonexistent/path.json")

    def test_cli_writes_json(self, tmp_path):
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_sample_input(), indent=2))
        out_json = tmp_path / "report.json"
        r = subprocess.run(
            [PYTHON,
                "scripts/generate_failed_candidate_report.py",
                "--input", str(input_file),
                "--out-json", str(out_json),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_json.exists()
        data = json.loads(out_json.read_text())
        assert data["report_metadata"]["report_type"] == "failed_candidate_report"
        assert data["summary"]["total_candidates"] == 3
        assert data["dry_lab_only"] is True

    def test_cli_writes_markdown(self, tmp_path):
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_sample_input(), indent=2))
        out_md = tmp_path / "report.md"
        r = subprocess.run(
            [PYTHON,
                "scripts/generate_failed_candidate_report.py",
                "--input", str(input_file),
                "--out-md", str(out_md),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_md.exists()
        content = out_md.read_text()
        assert "# Failed Candidate Report" in content
        assert "CAND-001" in content

    def test_cli_validate_rejection_codes_success(self, tmp_path):
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_sample_input(), indent=2))
        out_json = tmp_path / "report.json"
        r = subprocess.run(
            [PYTHON,
                "scripts/generate_failed_candidate_report.py",
                "--input", str(input_file),
                "--out-json", str(out_json),
                "--validate-rejection-codes",
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_json.exists()

    def test_cli_validate_rejection_codes_fails(self, tmp_path):
        bad_candidates = {
            "source_batch": "test",
            "pipeline_version": "v1",
            "date": "2026-07-09",
            "candidates": [
                {
                    "candidate_id": "BAD-001",
                    "rejections": [{"code": "NOT_REAL"}],
                }
            ],
        }
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(bad_candidates, indent=2))
        r = subprocess.run(
            [PYTHON,
                "scripts/generate_failed_candidate_report.py",
                "--input", str(input_file),
                "--out-json", str(tmp_path / "report.json"),
                "--validate-rejection-codes",
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 3

    def test_cli_missing_input_fails(self, tmp_path):
        r = subprocess.run(
            [PYTHON,
                "scripts/generate_failed_candidate_report.py",
                "--input", str(tmp_path / "nonexistent.json"),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_cli_empty_candidates_fails(self, tmp_path):
        empty = {
            "source_batch": "test",
            "pipeline_version": "v1",
            "date": "2026-07-09",
            "candidates": [],
        }
        input_file = tmp_path / "empty.json"
        input_file.write_text(json.dumps(empty, indent=2))
        r = subprocess.run(
            [
                sys.executable,
                "scripts/generate_failed_candidate_report.py",
                "--input", str(input_file),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_build_report_empty_taxonomy(self):
        report = build_report(
            candidates=_sample_candidates(),
            source_batch="test",
            pipeline_version="v1",
            report_date="2026-07-09",
            taxonomy=[],
        )
        assert report["summary"]["total_candidates"] == 3
        # Without taxonomy, category/severity defaults to "unknown"
        rejections = report["candidates"][0]["rejections"]
        for r in rejections:
            assert r.get("category") in ("", None, "unknown")

    def test_cli_produces_both_json_and_md(self, tmp_path):
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(_sample_input(), indent=2))
        out_json = tmp_path / "report.json"
        out_md = tmp_path / "report.md"
        r = subprocess.run(
            [PYTHON,
                "scripts/generate_failed_candidate_report.py",
                "--input", str(input_file),
                "--out-json", str(out_json),
                "--out-md", str(out_md),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_json.exists()
        assert out_md.exists()

    def test_example_input_validates(self):
        """The example input file should load without error."""
        example_path = _REPO_DIR / "examples" / "failed_candidates_example.json"
        assert example_path.exists()
        data = load_input(example_path)
        assert "candidates" in data
        assert len(data["candidates"]) == 5
        assert "WAVE0.5_EXAMPLE-001" in {c["candidate_id"] for c in data["candidates"]}

    def test_example_input_generates_valid_report(self):
        """Running the generator on the example input should produce a valid report."""
        example_path = _REPO_DIR / "examples" / "failed_candidates_example.json"
        data = load_input(example_path)
        candidates = data["candidates"]
        taxonomy = _taxonomy()
        report = build_report(
            candidates=candidates,
            source_batch=data.get("source_batch", "unknown"),
            pipeline_version=data.get("pipeline_version", "unknown"),
            report_date=data.get("date", "2026-07-09"),
            taxonomy=taxonomy,
        )
        assert report["summary"]["total_candidates"] == 5
        assert report["summary"]["total_rejection_instances"] == 8
        codes = set(report["summary"]["rejection_code_frequencies"].keys())
        assert "PIPE_ACTIVITY_LOW" in codes
        assert "PRE_SEQ_INVALID" in codes
        assert "DIV_BUDGET" in codes
        assert report["dry_lab_only"] is True
