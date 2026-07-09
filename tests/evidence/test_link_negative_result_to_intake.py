"""Tests for the negative-result to intake link report (F7)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.link_negative_result_to_intake import (
    build_link_report,
    build_markdown_report,
    load_json,
)

PYTHON = sys.executable

_REPO_DIR = Path(__file__).parents[2]


def _sample_entries() -> list[dict]:
    return [
        {
            "entry_id": 1,
            "candidate_id": "CAND-001",
            "sequence": "ACDEFGHIKLMNPQRSTVWY",
            "reason_category": "lab_inactive",
            "reason_detail": "MIC 64 > 32 ug/mL cutoff",
            "date": "2026-07-09",
            "intake_report_id": "pilot_panel.csv",
        },
        {
            "entry_id": 2,
            "candidate_id": "CAND-002",
            "sequence": "KLAKLAKKLAKLAK",
            "reason_category": "lab_toxic",
            "reason_detail": "Hemolysis 15% above 10% cutoff",
            "date": "2026-07-09",
            "intake_report_id": "pilot_panel.csv",
        },
        {
            "entry_id": 3,
            "candidate_id": "CAND-003",
            "sequence": "RRWQWRMKKLG",
            "reason_category": "synthesis_failure",
            "reason_detail": "Purity 72% below 90% threshold",
            "date": "2026-07-09",
        },
    ]


def _sample_intake_report() -> dict:
    return {
        "panel_csv": "pilot_panel.csv",
        "results_dir": "/tmp/lab_results",
        "n_panel_candidates": 5,
        "n_lab_results": 6,
        "n_matched_candidates": 3,
        "n_orphan_lab_results": 0,
        "orphan_candidate_ids": [],
        "per_candidate_joined": [
            {
                "candidate_id": "CAND-001",
                "coverage_note": "matched",
                "predictions": {
                    "ensemble": 0.45,
                    "activity": 0.42,
                    "safety": 0.31,
                    "synthesis": 0.88,
                    "novelty": 0.65,
                    "selectivity_proxy": 0.50,
                    "rich_selectivity": 0.35,
                    "pilot_priority": 0.40,
                },
                "has_lab": {
                    "n_results": 2,
                    "n_mic": 2,
                    "n_hemolysis": 0,
                    "active_mic": False,
                    "high_hemolysis": None,
                    "all_controls_passed": True,
                },
            },
            {
                "candidate_id": "CAND-002",
                "coverage_note": "matched",
                "predictions": {
                    "ensemble": 0.62,
                    "activity": 0.71,
                    "safety": 0.28,
                    "synthesis": 0.90,
                    "novelty": 0.55,
                },
                "has_lab": {
                    "n_results": 1,
                    "n_hemolysis": 1,
                    "n_mic": 0,
                    "active_mic": None,
                    "high_hemolysis": True,
                    "all_controls_passed": True,
                },
            },
            {
                "candidate_id": "CAND-004",
                "coverage_note": "matched",
                "predictions": {
                    "ensemble": 0.78,
                    "activity": 0.82,
                    "safety": 0.65,
                    "synthesis": 0.85,
                    "novelty": 0.30,
                },
                "has_lab": {
                    "n_results": 1,
                    "n_mic": 1,
                    "active_mic": True,
                    "all_controls_passed": True,
                },
            },
        ],
        "cohort_metrics": {
            "activity_vs_active_mic": {
                "assay_type": "MIC",
                "n": 2,
                "insufficient_data": True,
            },
        },
        "control_failures": [],
        "report_disclaimer": "Test disclaimer",
    }


class TestLinkNegativeResultToIntake:
    def test_basic_linkage_counts(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        s = report["summary"]
        assert s["total_negative_entries"] == 3
        assert s["total_matched_to_intake"] == 2
        assert s["total_unmatched_negative_entries"] == 1

    def test_linkage_rate(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        assert report["summary"]["linkage_rate"] == round(2 / 3, 4)

    def test_linked_entries_have_predictions(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        for m in report["linked_entries"]:
            if m["matched"]:
                assert "predictions" in m
                assert "had_lab_result" in m
                assert m["had_lab_result"] is True

    def test_unmatched_entry_has_no_predictions(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        c3 = [m for m in report["linked_entries"] if m["candidate_id"] == "CAND-003"]
        assert len(c3) == 1
        assert c3[0]["matched"] is False
        assert "predictions" not in c3[0] or c3[0]["predictions"] == {}

    def test_orphan_intake_candidates_detected(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        orphans = report["summary"]["orphan_intake_candidate_ids"]
        assert "CAND-004" in orphans

    def test_intake_report_id_validated(self):
        bad_entries = _sample_entries()
        bad_entries[0]["intake_report_id"] = "wrong_intake.json"
        report = build_link_report(
            entries=bad_entries,
            intake_report=_sample_intake_report(),
        )
        inv = report["summary"]["invalid_intake_report_ids"]
        assert len(inv) == 1
        assert inv[0]["candidate_id"] == "CAND-001"

    def test_valid_intake_report_id_passes(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        inv = report["summary"]["invalid_intake_report_ids"]
        assert len(inv) == 0

    def test_by_reason_category_matched(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        cats = report["summary"]["by_reason_category_matched"]
        assert cats.get("lab_inactive", 0) == 1
        assert cats.get("lab_toxic", 0) == 1

    def test_report_metadata(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
            archive_source="test_archive.json",
        )
        meta = report["report_metadata"]
        assert meta["report_type"] == "negative_result_intake_link_report"
        assert meta["schema_version"] == "1.0.0"
        assert meta["archive_source"] == "test_archive.json"
        assert "generated_at" in meta

    def test_report_caveats(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        assert len(report["caveats"]) >= 4
        assert any("not biological proof" in c for c in report["caveats"])
        assert report["dry_lab_only"] is True

    def test_lab_summary_in_linked_entries(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        c1 = [m for m in report["linked_entries"] if m["candidate_id"] == "CAND-001"][0]
        assert c1["lab_summary"]["n_results"] == 2
        assert c1["lab_summary"]["active_mic"] is False
        assert c1["lab_summary"]["all_controls_passed"] is True

    def test_markdown_contains_sections(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        md = build_markdown_report(report)
        assert "# Negative-Result to Intake Link Report" in md
        assert "## Report Metadata" in md
        assert "## Linkage Summary" in md
        assert "## Linked Entries" in md
        assert "## Caveats" in md

    def test_markdown_contains_caveats(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        md = build_markdown_report(report)
        assert "not biological proof" in md
        assert "informational only" in md

    def test_empty_entries_returns_zero_rate(self):
        report = build_link_report(
            entries=[],
            intake_report=_sample_intake_report(),
        )
        assert report["summary"]["total_negative_entries"] == 0
        assert report["summary"]["linkage_rate"] == 0.0

    def test_all_unmatched(self):
        report = build_link_report(
            entries=[
                {
                    "entry_id": 99,
                    "candidate_id": "NOBODY",
                    "reason_category": "pre_selection_reject",
                    "reason_detail": "No match in intake",
                    "date": "2026-07-09",
                }
            ],
            intake_report=_sample_intake_report(),
        )
        assert report["summary"]["total_matched_to_intake"] == 0
        assert report["summary"]["total_unmatched_negative_entries"] == 1
        assert report["summary"]["linkage_rate"] == 0.0

    def test_load_input_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_json("/nonexistent/path.json")

    def test_cli_writes_json(self, tmp_path):
        archive_file = tmp_path / "archive.json"
        archive_file.write_text(
            json.dumps({"entries": _sample_entries(), "archive_source": "test"}, indent=2)
        )
        intake_file = tmp_path / "intake.json"
        intake_file.write_text(json.dumps(_sample_intake_report(), indent=2))
        out_json = tmp_path / "link.json"
        r = subprocess.run(
            [PYTHON,
                "scripts/link_negative_result_to_intake.py",
                "--negative-result-archive", str(archive_file),
                "--intake-report", str(intake_file),
                "--out-json", str(out_json),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_json.exists()
        data = json.loads(out_json.read_text())
        assert data["report_metadata"]["report_type"] == "negative_result_intake_link_report"
        assert data["summary"]["total_negative_entries"] == 3
        assert data["dry_lab_only"] is True

    def test_cli_writes_markdown(self, tmp_path):
        archive_file = tmp_path / "archive.json"
        archive_file.write_text(
            json.dumps({"entries": _sample_entries()}, indent=2)
        )
        intake_file = tmp_path / "intake.json"
        intake_file.write_text(json.dumps(_sample_intake_report(), indent=2))
        out_md = tmp_path / "link.md"
        r = subprocess.run(
            [PYTHON,
                "scripts/link_negative_result_to_intake.py",
                "--negative-result-archive", str(archive_file),
                "--intake-report", str(intake_file),
                "--out-md", str(out_md),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_md.exists()
        content = out_md.read_text()
        assert "# Negative-Result to Intake Link Report" in content
        assert "CAND-001" in content

    def test_cli_writes_both_json_and_md(self, tmp_path):
        archive_file = tmp_path / "archive.json"
        archive_file.write_text(
            json.dumps({"entries": _sample_entries()}, indent=2)
        )
        intake_file = tmp_path / "intake.json"
        intake_file.write_text(json.dumps(_sample_intake_report(), indent=2))
        out_json = tmp_path / "link.json"
        out_md = tmp_path / "link.md"
        r = subprocess.run(
            [PYTHON,
                "scripts/link_negative_result_to_intake.py",
                "--negative-result-archive", str(archive_file),
                "--intake-report", str(intake_file),
                "--out-json", str(out_json),
                "--out-md", str(out_md),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert out_json.exists()
        assert out_md.exists()

    def test_cli_missing_input_fails(self, tmp_path):
        r = subprocess.run(
            [PYTHON,
                "scripts/link_negative_result_to_intake.py",
                "--negative-result-archive", str(tmp_path / "nonexistent.json"),
                "--intake-report", str(tmp_path / "nonexistent2.json"),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_cli_empty_entries_fails(self, tmp_path):
        archive_file = tmp_path / "empty.json"
        archive_file.write_text(json.dumps({"entries": []}, indent=2))
        intake_file = tmp_path / "intake.json"
        intake_file.write_text(json.dumps(_sample_intake_report(), indent=2))
        r = subprocess.run(
            [PYTHON,
                "scripts/link_negative_result_to_intake.py",
                "--negative-result-archive", str(archive_file),
                "--intake-report", str(intake_file),
            ],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_control_failures_from_intake_included(self):
        intake = _sample_intake_report()
        intake["control_failures"] = [
            {
                "result_id": "R-001",
                "candidate_id": "CAND-002",
                "assay_type": "MIC",
                "positive_control_passed": False,
                "negative_control_passed": True,
            }
        ]
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=intake,
        )
        assert len(report["control_failures_in_intake"]) == 1
        assert report["control_failures_in_intake"][0]["result_id"] == "R-001"

    def test_cohort_metrics_from_intake_included(self):
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        metrics = report["cohort_metrics_from_intake"]
        assert "activity_vs_active_mic" in metrics
        assert metrics["activity_vs_active_mic"]["insufficient_data"] is True

    def test_list_input_format_supported(self):
        """Archive data can be a raw list instead of dict with entries key."""
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=_sample_intake_report(),
        )
        assert report["summary"]["total_negative_entries"] == 3

    def test_lab_summary_absent_when_no_lab(self):
        intake = _sample_intake_report()
        intake["per_candidate_joined"][0]["has_lab"] = None
        report = build_link_report(
            entries=_sample_entries(),
            intake_report=intake,
        )
        c1 = [m for m in report["linked_entries"] if m["candidate_id"] == "CAND-001"][0]
        assert c1["had_lab_result"] is False
