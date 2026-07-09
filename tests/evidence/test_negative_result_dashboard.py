"""Tests for the negative-result dashboard generator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.negative_result_dashboard import (
    build_dashboard,
    generate_markdown,
    load_entries,
)

_EXAMPLE_PATH = (
    Path(__file__).resolve().parents[2] / "examples" / "negative_result_dashboard_example.json"
)


def _sample_entries() -> list[dict]:
    return [
        {
            "entry_id": 1,
            "candidate_id": "TEST-001",
            "sequence": "RRIRIIRRIRIIRRI",
            "reason_category": "lab_inactive",
            "reason_detail": "MIC > 128 ug/mL.",
            "pipeline_version": "v0.5.70",
            "source_batch": "test",
            "score_activity": 0.80,
            "score_safety": 0.85,
            "score_novelty": 0.50,
            "score_ensemble": 0.75,
            "recalibration_used": "no",
        },
        {
            "entry_id": 2,
            "candidate_id": "TEST-002",
            "sequence": "KLAKLAKKLAKLAK",
            "reason_category": "lab_toxic",
            "reason_detail": "HC50 = 8 ug/mL.",
            "pipeline_version": "v0.5.71",
            "source_batch": "test",
            "score_activity": 0.90,
            "score_safety": 0.30,
            "score_novelty": 0.60,
            "score_ensemble": 0.78,
            "recalibration_used": "yes",
        },
        {
            "entry_id": 3,
            "candidate_id": "TEST-003",
            "sequence": "GIGKFLHSAKKWGKAFVGEIMNS",
            "reason_category": "lab_inactive",
            "reason_detail": "MIC > 256 ug/mL.",
            "pipeline_version": "v0.5.70",
            "source_batch": "test",
            "score_activity": 0.75,
            "score_safety": 0.90,
            "score_novelty": 0.40,
            "score_ensemble": 0.70,
            "recalibration_used": "no",
        },
        {
            "entry_id": 4,
            "candidate_id": "TEST-004",
            "sequence": "AAAAKAAAAKAAAA",
            "reason_category": "control_failure",
            "reason_detail": "Positive control outside range.",
            "pipeline_version": "v0.5.72",
            "source_batch": "test",
            "score_activity": 0.45,
            "score_safety": 0.95,
            "score_novelty": 0.30,
            "score_ensemble": 0.50,
            "recalibration_used": "no",
        },
        {
            "entry_id": 5,
            "candidate_id": "TEST-005",
            "sequence": "RRWQWRMKKLG",
            "reason_category": "synthesis_failure",
            "reason_detail": "Yield < 5%.",
            "pipeline_version": "v0.5.73",
            "source_batch": "test",
            "score_activity": 0.70,
            "score_safety": 0.80,
            "score_novelty": 0.55,
            "score_ensemble": 0.68,
            "recalibration_used": "no",
        },
    ]


class TestBuildDashboard:
    def test_returns_required_structure(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        assert "dashboard_metadata" in dashboard
        assert "summary" in dashboard
        assert "scores_distribution" in dashboard
        assert "category_score_summary" in dashboard
        assert "insights" in dashboard
        assert "_caveat" in dashboard

    def test_summary_counts(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        assert dashboard["summary"]["total_entries"] == 5

    def test_by_category_breakdown(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        by_cat = dashboard["summary"]["by_category"]
        assert by_cat["lab_inactive"] == 2
        assert by_cat["lab_toxic"] == 1
        assert by_cat["control_failure"] == 1
        assert by_cat["synthesis_failure"] == 1

    def test_by_pipeline_version(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        by_pv = dashboard["summary"]["by_pipeline_version"]
        assert by_pv["v0.5.70"] == 2
        assert by_pv["v0.5.71"] == 1
        assert by_pv["v0.5.72"] == 1
        assert by_pv["v0.5.73"] == 1

    def test_scores_distribution_stats(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        sd = dashboard["scores_distribution"]
        assert "activity" in sd
        assert "safety" in sd
        assert "novelty" in sd
        assert "ensemble" in sd
        assert sd["activity"]["count"] == 5
        assert sd["activity"]["min"] == 0.45
        assert sd["activity"]["max"] == 0.90
        assert round(sd["activity"]["mean"], 2) == 0.72

    def test_insights_identifies_most_common_category(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        assert dashboard["insights"]["most_common_failure_category"] == "lab_inactive"
        assert dashboard["insights"]["most_common_failure_count"] == 2

    def test_insights_identifies_highest_activity_category(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        assert dashboard["insights"]["category_with_highest_avg_activity"] == "lab_toxic"

    def test_insights_identifies_lowest_safety_category(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        assert dashboard["insights"]["category_with_lowest_avg_safety"] == "lab_toxic"

    def test_insights_recalibration_opportunities(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        assert dashboard["insights"]["recalibration_opportunities"] == 1

    def test_empty_entries_produces_zero_summary(self):
        dashboard = build_dashboard([])
        assert dashboard["summary"]["total_entries"] == 0
        assert dashboard["summary"]["by_category"] == {}
        assert dashboard["insights"]["total_failures_analyzed"] == 0

    def test_entries_without_scores_handled_gracefully(self):
        entries = [
            {
                "entry_id": 99,
                "candidate_id": "NO-SCORE-001",
                "reason_category": "pre_selection_reject",
                "reason_detail": "No scores available.",
                "pipeline_version": "v0.5.70",
                "source_batch": "test",
            }
        ]
        dashboard = build_dashboard(entries)
        assert dashboard["summary"]["total_entries"] == 1
        assert dashboard["scores_distribution"]["activity"]["count"] == 0

    def test_category_score_summary_shape(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        css = dashboard["category_score_summary"]
        assert "lab_inactive" in css
        assert "lab_toxic" in css
        assert "activity" in css["lab_inactive"]
        assert "safety" in css["lab_inactive"]
        assert css["lab_inactive"]["activity"]["count"] == 2

    def test_metadata_contains_generation_timestamp(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        assert "generated_at" in dashboard["dashboard_metadata"]
        assert dashboard["dashboard_metadata"]["total_entries"] == 5


class TestGenerateMarkdown:
    def test_contains_title(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        md = generate_markdown(dashboard)
        assert "# Negative-Result Dashboard" in md

    def test_contains_summary_section(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        md = generate_markdown(dashboard)
        assert "## Summary" in md

    def test_contains_category_table(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        md = generate_markdown(dashboard)
        assert "### By Failure Category" in md
        assert "lab_inactive" in md
        assert "lab_toxic" in md

    def test_contains_score_distribution(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        md = generate_markdown(dashboard)
        assert "## Score Distribution" in md
        assert "activity" in md
        assert "safety" in md

    def test_contains_insights(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        md = generate_markdown(dashboard)
        assert "## Insights" in md
        assert "Most common failure category" in md

    def test_contains_caveat(self):
        entries = _sample_entries()
        dashboard = build_dashboard(entries)
        md = generate_markdown(dashboard)
        assert "## Caveat" in md

    def test_empty_entries_handled(self):
        dashboard = build_dashboard([])
        md = generate_markdown(dashboard)
        assert "# Negative-Result Dashboard" in md


class TestLoadEntries:
    def test_loads_from_example_file(self):
        entries = load_entries(_EXAMPLE_PATH)
        assert len(entries) == 15
        assert entries[0]["entry_id"] == 101
        assert entries[0]["reason_category"] == "pre_selection_reject"

    def test_loads_list_format(self, tmp_path):
        data = [
            {"entry_id": 1, "candidate_id": "T1", "reason_category": "lab_inactive"},
            {"entry_id": 2, "candidate_id": "T2", "reason_category": "lab_toxic"},
        ]
        inp = tmp_path / "entries.json"
        inp.write_text(json.dumps(data))
        entries = load_entries(inp)
        assert len(entries) == 2

    def test_loads_dict_with_entries_key(self, tmp_path):
        data = {"entries": [
            {"entry_id": 1, "candidate_id": "T1", "reason_category": "lab_inactive"},
        ]}
        inp = tmp_path / "entries.json"
        inp.write_text(json.dumps(data))
        entries = load_entries(inp)
        assert len(entries) == 1

    def test_exits_on_missing_file(self, tmp_path):
        with pytest.raises(SystemExit) as exc:
            load_entries(tmp_path / "nonexistent.json")
        assert exc.value.code == 2

    def test_exits_on_empty_list(self, tmp_path):
        inp = tmp_path / "empty.json"
        inp.write_text("[]")
        with pytest.raises(SystemExit) as exc:
            load_entries(inp)
        assert exc.value.code == 2

    def test_exits_on_missing_required_fields(self, tmp_path):
        data = [{"entry_id": 1}]  # missing candidate_id and reason_category
        inp = tmp_path / "bad.json"
        inp.write_text(json.dumps(data))
        with pytest.raises(SystemExit) as exc:
            load_entries(inp)
        assert exc.value.code == 2


class TestCLI:
    def test_exit_zero_on_success(self, tmp_path):
        entries = _sample_entries()
        inp = tmp_path / "entries.json"
        inp.write_text(json.dumps(entries))
        r = subprocess.run(
            [sys.executable, "scripts/negative_result_dashboard.py",
             "--input", str(inp)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0

    def test_exit_two_on_missing_input(self, tmp_path):
        r = subprocess.run(
            [sys.executable, "scripts/negative_result_dashboard.py",
             "--input", str(tmp_path / "nonexistent.json")],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_exit_two_on_empty_list(self, tmp_path):
        inp = tmp_path / "empty.json"
        inp.write_text("[]")
        r = subprocess.run(
            [sys.executable, "scripts/negative_result_dashboard.py",
             "--input", str(inp)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_exit_two_on_invalid_json(self, tmp_path):
        inp = tmp_path / "bad.json"
        inp.write_text("not json")
        r = subprocess.run(
            [sys.executable, "scripts/negative_result_dashboard.py",
             "--input", str(inp)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_writes_json_output(self, tmp_path):
        entries = _sample_entries()
        inp = tmp_path / "entries.json"
        inp.write_text(json.dumps(entries))
        out = tmp_path / "dashboard.json"
        subprocess.run(
            [sys.executable, "scripts/negative_result_dashboard.py",
             "--input", str(inp), "--out-json", str(out)],
            capture_output=True,
            env={"PYTHONPATH": "src"},
        )
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["summary"]["total_entries"] == 5

    def test_writes_markdown_output(self, tmp_path):
        entries = _sample_entries()
        inp = tmp_path / "entries.json"
        inp.write_text(json.dumps(entries))
        out = tmp_path / "dashboard.md"
        subprocess.run(
            [sys.executable, "scripts/negative_result_dashboard.py",
             "--input", str(inp), "--out-md", str(out)],
            capture_output=True,
            env={"PYTHONPATH": "src"},
        )
        assert out.exists()
        assert "# Negative-Result Dashboard" in out.read_text()

    def test_runs_on_example_file(self, tmp_path):
        r = subprocess.run(
            [sys.executable, "scripts/negative_result_dashboard.py",
             "--input", str(_EXAMPLE_PATH)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        assert "dashboard_metadata" in r.stdout
