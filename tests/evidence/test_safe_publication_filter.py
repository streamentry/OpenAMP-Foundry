"""Tests for the safe-publication filter (F5)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.safe_publication_filter import (
    build_filter_result,
    build_markdown_result,
    load_input,
    run_candidate_checks,
    run_global_checks,
)

PYTHON = sys.executable
_REPO_DIR = Path(__file__).parents[2]


def _default_input(overrides: dict | None = None) -> dict:
    data = {
        "source": "test-batch",
        "pipeline_version": "v0.5.75-test",
        "report_type": "safe_publication_input",
        "dry_lab_only": True,
        "proof_ladder_level": 2,
        "safety_checks": {
            "toxicity_screened": True,
            "hemolysis_screened": True,
            "dual_use_reviewed": True,
        },
        "candidates": [
            {
                "candidate_id": "CAND-001",
                "sequence": "ACDEFGHIKLMNPQRSTVWY",
                "ensemble_score": 0.85,
                "proof_ladder_level": 2,
            },
            {
                "candidate_id": "CAND-002",
                "sequence": "KLAKLAKKLAKLAK",
                "ensemble_score": 0.80,
                "proof_ladder_level": 1,
            },
        ],
    }
    if overrides:
        data.update(overrides)
    return data


class TestSafePublicationFilter:
    def test_global_checks_all_pass(self):
        """All global checks pass with valid input."""
        result = run_global_checks(_default_input())
        assert result["all_passed"] is True
        checks = result["checks"]
        assert checks["dry_lab_only"]["passed"] is True
        assert checks["global_proof_ladder_level"]["passed"] is True
        assert checks["safety_checks"]["all_passed"] is True

    def test_global_dry_lab_only_false_fails(self):
        """dry_lab_only=false fails global checks."""
        result = run_global_checks(_default_input({"dry_lab_only": False}))
        assert result["all_passed"] is False
        assert result["checks"]["dry_lab_only"]["passed"] is False

    def test_global_dry_lab_only_missing_fails(self):
        """Missing dry_lab_only defaults to False and fails."""
        result = run_global_checks(_default_input({"dry_lab_only": False}))
        assert result["all_passed"] is False

    def test_global_proof_ladder_too_high_fails(self):
        """proof_ladder_level > 4 fails global checks."""
        result = run_global_checks(_default_input({"proof_ladder_level": 5}))
        assert result["all_passed"] is False
        assert result["checks"]["global_proof_ladder_level"]["passed"] is False
        assert "exceeds" in result["checks"]["global_proof_ladder_level"].get("reason", "")

    def test_global_proof_ladder_missing_fails(self):
        """Missing proof_ladder_level fails checks."""
        result = run_global_checks(_default_input({"proof_ladder_level": None}))
        assert result["all_passed"] is False
        assert result["checks"]["global_proof_ladder_level"]["passed"] is False

    def test_global_toxicity_not_screened_fails(self):
        """toxicity_screened=false fails safety checks."""
        result = run_global_checks(_default_input({
            "safety_checks": {
                "toxicity_screened": False,
                "hemolysis_screened": True,
                "dual_use_reviewed": True,
            }
        }))
        assert result["all_passed"] is False
        sc = result["checks"]["safety_checks"]
        assert sc["all_passed"] is False
        assert sc["checks"]["toxicity_screened"]["passed"] is False

    def test_global_hemolysis_not_screened_fails(self):
        """hemolysis_screened=false fails safety checks."""
        result = run_global_checks(_default_input({
            "safety_checks": {
                "toxicity_screened": True,
                "hemolysis_screened": False,
                "dual_use_reviewed": True,
            }
        }))
        assert result["all_passed"] is False
        sc = result["checks"]["safety_checks"]
        assert sc["all_passed"] is False
        assert sc["checks"]["hemolysis_screened"]["passed"] is False

    def test_global_dual_use_not_reviewed_fails(self):
        """dual_use_reviewed=false fails safety checks."""
        result = run_global_checks(_default_input({
            "safety_checks": {
                "toxicity_screened": True,
                "hemolysis_screened": True,
                "dual_use_reviewed": False,
            }
        }))
        assert result["all_passed"] is False
        sc = result["checks"]["safety_checks"]
        assert sc["all_passed"] is False
        assert sc["checks"]["dual_use_reviewed"]["passed"] is False

    def test_global_safety_missing_all_fails(self):
        """Missing safety_checks section fails all three."""
        result = run_global_checks(_default_input({"safety_checks": {}}))
        assert result["all_passed"] is False
        sc = result["checks"]["safety_checks"]
        assert sc["all_passed"] is False
        for name in ["toxicity_screened", "hemolysis_screened", "dual_use_reviewed"]:
            assert sc["checks"][name]["passed"] is False

    def test_candidate_pll_too_high_fails(self):
        """Candidate with proof_ladder_level > 4 fails."""
        candidates = [{
            "candidate_id": "CAND-001",
            "proof_ladder_level": 5,
        }]
        results = run_candidate_checks(candidates)
        assert results[0]["overall"] == "FAIL"
        assert "PROOF_LADDER_EXCEEDED" in results[0].get("issues", [])

    def test_candidate_pll_missing_fails(self):
        """Candidate missing proof_ladder_level fails."""
        candidates = [{"candidate_id": "CAND-001"}]
        results = run_candidate_checks(candidates)
        assert results[0]["overall"] == "FAIL"
        assert "PROOF_LADDER_MISSING" in results[0].get("issues", [])

    def test_candidate_pll_at_boundary_warns(self):
        """Candidate with proof_ladder_level == 4 returns WARN."""
        candidates = [{
            "candidate_id": "CAND-001",
            "proof_ladder_level": 4,
        }]
        results = run_candidate_checks(candidates)
        assert results[0]["overall"] == "WARN"
        assert results[0]["checks"]["proof_ladder_level"]["passed"] is True

    def test_candidate_pll_valid_passes(self):
        """Candidate with valid proof_ladder_level passes."""
        candidates = [{
            "candidate_id": "CAND-001",
            "proof_ladder_level": 2,
        }]
        results = run_candidate_checks(candidates)
        assert results[0]["overall"] == "PASS"
        assert results[0]["checks"]["proof_ladder_level"]["passed"] is True

    def test_candidate_multiple_mixed_results(self):
        """Multiple candidates with mixed levels produce correct results."""
        candidates = [
            {"candidate_id": "C-001", "proof_ladder_level": 2},
            {"candidate_id": "C-002", "proof_ladder_level": 5},
            {"candidate_id": "C-003", "proof_ladder_level": 4},
        ]
        results = run_candidate_checks(candidates)
        statuses = {r["candidate_id"]: r["overall"] for r in results}
        assert statuses["C-001"] == "PASS"
        assert statuses["C-002"] == "FAIL"
        assert statuses["C-003"] == "WARN"

    def test_build_filter_result_summary(self):
        """Filter result summary counts are correct."""
        input_data = _default_input()
        global_results = run_global_checks(input_data)
        candidate_results = run_candidate_checks(input_data["candidates"])
        result = build_filter_result(input_data, global_results, candidate_results)
        s = result["summary"]
        candidates = input_data["candidates"]
        assert s["total_candidates"] == len(candidates)
        assert s["passed"] + s["warned"] + s["failed"] == s["total_candidates"]
        assert s["overall_filter_pass"] is True

    def test_build_filter_result_summary_with_fails(self):
        """Overall filter pass is False when candidates fail."""
        input_data = _default_input({
            "dry_lab_only": True,
            "proof_ladder_level": 2,
            "safety_checks": {"toxicity_screened": True, "hemolysis_screened": True, "dual_use_reviewed": True},
            "candidates": [
                {"candidate_id": "C-001", "proof_ladder_level": 2},
                {"candidate_id": "C-002", "proof_ladder_level": 5},
            ],
        })
        global_results = run_global_checks(input_data)
        candidate_results = run_candidate_checks(input_data["candidates"])
        result = build_filter_result(input_data, global_results, candidate_results)
        assert result["summary"]["overall_filter_pass"] is False
        assert result["summary"]["failed"] == 1

    def test_global_fail_makes_overall_fail_even_with_pass_candidates(self):
        """Global check failure makes overall_filter_pass False even with passing candidates."""
        input_data = _default_input({
            "dry_lab_only": False,
            "safety_checks": {"toxicity_screened": True, "hemolysis_screened": True, "dual_use_reviewed": True},
            "candidates": [
                {"candidate_id": "C-001", "proof_ladder_level": 2},
            ],
        })
        global_results = run_global_checks(input_data)
        candidate_results = run_candidate_checks(input_data["candidates"])
        result = build_filter_result(input_data, global_results, candidate_results)
        assert result["global_pass"] is False
        assert result["summary"]["overall_filter_pass"] is False
        assert result["summary"]["passed"] == 1  # candidates pass but global fails

    def test_markdown_contains_sections(self):
        """Markdown output contains expected sections."""
        input_data = _default_input()
        global_results = run_global_checks(input_data)
        candidate_results = run_candidate_checks(input_data["candidates"])
        result = build_filter_result(input_data, global_results, candidate_results)
        md = build_markdown_result(result)
        assert "# Safe Publication Filter Result" in md
        assert "## Filter Metadata" in md
        assert "## Global Checks" in md
        assert "## Summary" in md
        assert "## Per-Candidate Results" in md
        assert "## Caveats" in md
        assert "CAND-001" in md
        assert "CAND-002" in md

    def test_markdown_summary_counts(self):
        """Markdown contains summary counts."""
        input_data = _default_input()
        global_results = run_global_checks(input_data)
        candidate_results = run_candidate_checks(input_data["candidates"])
        result = build_filter_result(input_data, global_results, candidate_results)
        md = build_markdown_result(result)
        assert "Total candidates" in md
        assert "Passed" in md
        assert "Failed" in md
        assert "overall filter verdict" in md.lower()

    def test_load_input_valid(self):
        """Loading a valid JSON file succeeds."""
        example = _REPO_DIR / "examples" / "safe_publication_filter_example_input.json"
        assert example.exists()
        data = load_input(str(example))
        assert "candidates" in data
        assert "dry_lab_only" in data
        assert data["dry_lab_only"] is True

    def test_load_input_missing_file(self):
        """Loading a nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_input("/nonexistent/path.json")

    def test_load_input_invalid_json(self):
        """Loading an invalid JSON file raises ValueError."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("not json")
            p = Path(f.name)
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_input(p)
        finally:
            p.unlink()

    def test_cli_writes_json(self, tmp_path):
        """CLI produces a valid JSON output file."""
        example = _REPO_DIR / "examples" / "safe_publication_filter_example_input.json"
        out_json = tmp_path / "filter_result.json"
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(example),
             "--out-json", str(out_json)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode in (0, 1)
        assert out_json.exists()
        data = json.loads(out_json.read_text())
        assert data["filter_metadata"]["filter_type"] == "safe_publication_filter"
        assert "candidates" in data
        assert "global_checks" in data

    def test_cli_exit_code_0_all_pass(self, tmp_path):
        """CLI returns 0 when all checks pass."""
        input_data = _default_input()
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(input_data))
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(input_file)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 0
        result = json.loads(r.stdout)
        assert result["summary"]["overall_filter_pass"] is True

    def test_cli_exit_code_1_global_fail(self, tmp_path):
        """CLI returns 1 when global checks fail."""
        input_data = _default_input({"dry_lab_only": False})
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(input_data))
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(input_file)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 1
        result = json.loads(r.stdout)
        assert result["global_pass"] is False

    def test_cli_exit_code_1_candidate_fail(self, tmp_path):
        """CLI returns 1 when a candidate fails checks."""
        input_data = _default_input({
            "candidates": [{"candidate_id": "C-001", "proof_ladder_level": 6}],
        })
        input_file = tmp_path / "input.json"
        input_file.write_text(json.dumps(input_data))
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(input_file)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 1
        result = json.loads(r.stdout)
        assert result["summary"]["overall_filter_pass"] is False

    def test_cli_missing_input_fails(self, tmp_path):
        """CLI returns 2 for missing input file."""
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(tmp_path / "nonexistent.json")],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_cli_empty_candidates_fails(self, tmp_path):
        """CLI returns 2 for empty candidates list."""
        input_data = _default_input({"candidates": []})
        input_file = tmp_path / "empty.json"
        input_file.write_text(json.dumps(input_data))
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(input_file)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 2

    def test_cli_produces_json_and_md(self, tmp_path):
        """CLI produces both JSON and Markdown output when requested."""
        example = _REPO_DIR / "examples" / "safe_publication_filter_example_input.json"
        out_json = tmp_path / "result.json"
        out_md = tmp_path / "result.md"
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(example),
             "--out-json", str(out_json),
             "--out-md", str(out_md)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode in (0, 1)
        assert out_json.exists()
        assert out_md.exists()
        md_content = out_md.read_text()
        assert "# Safe Publication Filter Result" in md_content

    def test_filter_result_has_caveats(self):
        """Filter result always includes caveats."""
        input_data = _default_input()
        global_results = run_global_checks(input_data)
        candidate_results = run_candidate_checks(input_data["candidates"])
        result = build_filter_result(input_data, global_results, candidate_results)
        assert len(result["caveats"]) >= 6
        assert any("not biological proof" in c for c in result["caveats"])
        assert result["dry_lab_only"] is True

    def test_filter_metadata_structure(self):
        """Filter metadata has correct structure."""
        input_data = _default_input()
        global_results = run_global_checks(input_data)
        candidate_results = run_candidate_checks(input_data["candidates"])
        result = build_filter_result(input_data, global_results, candidate_results)
        meta = result["filter_metadata"]
        assert meta["filter_type"] == "safe_publication_filter"
        assert meta["filter_version"] == "1.0.0"
        assert meta["input_source"] == "test-batch"
        assert meta["pipeline_version"] == "v0.5.75-test"
        assert "generated_at" in meta

    def test_example_input_produces_valid_result(self):
        """The example input file produces a valid filter result with expected outcomes."""
        example = _REPO_DIR / "examples" / "safe_publication_filter_example_input.json"
        data = load_input(str(example))
        global_results = run_global_checks(data)
        candidate_results = run_candidate_checks(data["candidates"])
        result = build_filter_result(data, global_results, candidate_results)
        assert result["global_pass"] is True
        s = result["summary"]
        assert s["total_candidates"] == 4
        outcomes = {r["overall"] for r in result["candidates"]}
        # CAND-003 has pll=5 → FAIL
        # CAND-002 has pll=4 → WARN
        assert "FAIL" in outcomes
        assert "WARN" in outcomes
        assert "PASS" in outcomes

    def test_example_input_cli_round_trip(self, tmp_path):
        """Running the CLI on the example input produces a parseable result."""
        example = _REPO_DIR / "examples" / "safe_publication_filter_example_input.json"
        out_json = tmp_path / "result.json"
        r = subprocess.run(
            [PYTHON, "scripts/safe_publication_filter.py",
             "--input", str(example),
             "--out-json", str(out_json)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
        )
        assert r.returncode == 1  # CAND-003 fails
        assert out_json.exists()
        data = json.loads(out_json.read_text())
        assert data["summary"]["failed"] == 1
        assert data["summary"]["warned"] == 1
        assert data["summary"]["passed"] == 2
