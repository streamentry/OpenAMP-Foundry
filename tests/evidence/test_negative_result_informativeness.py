"""Tests for the negative-result informativeness classifier (F6)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.classify_negative_result_informativeness import (
    build_markdown,
    build_output,
    classify_entry,
    load_entry,
    _identity_score,
    _context_score,
    _specificity_score,
    _actionability_score,
    _verifiability_score,
    _structured_metadata_score,
    _interpretation_score,
)

PYTHON = sys.executable
_REPO_DIR = Path(__file__).parents[2]


def _make_entry(overrides: dict | None = None) -> dict:
    """Build a maximally informative entry, then override for test cases."""
    entry = {
        "entry_id": 1,
        "date": "2026-07-09",
        "candidate_id": "TEST-001",
        "sequence": "ACDEFGHIKLMNPQRSTVWY",
        "reason_category": "pre_selection_reject",
        "reason_detail": "Safety score 0.31 below minimum threshold 0.50. Driving factor: high hemolysis proxy (0.89) from elevated hydrophobicity (GRAVY=1.2). Batch-level pattern: all high-GRAVY candidates in this batch were rejected by the same gate.",
        "pipeline_version": "v0.5.76",
        "source_batch": "test-batch",
        "score_activity": 0.82,
        "score_safety": 0.31,
        "score_novelty": 0.91,
        "score_ensemble": 0.68,
        "reviewer_notes": "Rejected at Gate W0.5-3. High GRAVY is structural for these designed amphipathic sequences. Recommend implementing a two-tier safety flag that distinguishes structural membrane activity from non-specific toxicity risk. This systematic pattern affects 12/40 candidates in the current batch and warrants a policy review.",
    }
    if overrides:
        entry.update(overrides)
    return entry


class TestClassifyEntry:
    def test_informative_entry_classified_informative(self):
        """A fully populated entry should be classified INFORMATIVE."""
        result = classify_entry(_make_entry())
        assert result["classification"] == "INFORMATIVE"
        assert result["total_score"] >= 6.0

    def test_non_informative_minimal_entry(self):
        """A bare-minimum entry should be NON_INFORMATIVE."""
        entry = {
            "entry_id": 2,
            "candidate_id": "TEST-002",
            "sequence": "ACDEFGHIKLMNPQRSTVWY",
            "reason_category": "pre_selection_reject",
            "reason_detail": "Failed.",
            "pipeline_version": "v0.5.76",
            "source_batch": "test",
            "date": "2026-07-09",
        }
        result = classify_entry(entry)
        assert result["classification"] == "NON_INFORMATIVE"
        assert result["total_score"] < 3.5

    def test_neutral_entry_partial_info(self):
        """An entry with basic fields but no analysis should be NEUTRAL."""
        entry = {
            "entry_id": 3,
            "date": "2026-07-09",
            "candidate_id": "TEST-003",
            "sequence": "ACDEFGHIKLMNPQRSTVWY",
            "reason_category": "lab_inactive",
            "reason_detail": "MIC > 64 ug/mL against E. coli.",
            "pipeline_version": "v0.5.76",
            "source_batch": "wave0.5",
            "assay_type": "MIC",
            "assay_result": ">64",
            "assay_unit": "ug/mL",
        }
        result = classify_entry(entry)
        assert result["classification"] == "NEUTRAL"
        assert 3.5 <= result["total_score"] < 6.0

    def test_classification_score_range(self):
        """Total score should always be in 0.0-7.0 range."""
        for entry_data in [
            {},
            {"candidate_id": "X"},
            _make_entry(),
            _make_entry({"reviewer_notes": ""}),
        ]:
            result = classify_entry(entry_data)
            assert 0.0 <= result["total_score"] <= 7.0

    def test_result_contains_required_keys(self):
        """Result dict should have all expected fields."""
        result = classify_entry(_make_entry())
        for key in ("entry_id", "candidate_id", "reason_category", "classification",
                     "total_score", "dimensions", "caveat"):
            assert key in result

    def test_dimensions_has_seven_keys(self):
        """Dimensions dict should have all 7 dimension scores."""
        result = classify_entry(_make_entry())
        for dim in ("identity", "context", "specificity", "actionability",
                     "verifiability", "structured_metadata", "interpretation"):
            assert dim in result["dimensions"]
            assert 0.0 <= result["dimensions"][dim] <= 1.0

    def test_empty_entry_non_informative(self):
        """An empty entry should score 0 and be NON_INFORMATIVE."""
        result = classify_entry({})
        assert result["classification"] == "NON_INFORMATIVE"
        assert result["total_score"] == 0.0
        for dim_val in result["dimensions"].values():
            assert dim_val == 0.0


class TestDimensionScorers:
    def test_identity_present(self):
        assert _identity_score({"candidate_id": "X", "sequence": "ACDEF"}) == 1.0

    def test_identity_missing(self):
        assert _identity_score({}) == 0.0
        assert _identity_score({"candidate_id": "", "sequence": ""}) == 0.0

    def test_context_present(self):
        entry = {"pipeline_version": "v1", "source_batch": "batch", "date": "2026-07-09"}
        assert _context_score(entry) == 1.0

    def test_context_missing(self):
        assert _context_score({}) == 0.0

    def test_specificity_vague_string(self):
        assert _specificity_score({"reason_detail": "Failed."}) < 0.5

    def test_specificity_with_numbers_and_features(self):
        score = _specificity_score({
            "reason_detail": "Safety score 0.31 below threshold 0.50. GRAVY=1.2 driving hemolysis."
        })
        assert score >= 0.75

    def test_actionability_with_notes(self):
        entry = _make_entry({"reviewer_notes": "Recommend tightening the safety gate threshold."})
        assert _actionability_score(entry) > 0.0

    def test_actionability_missing_notes(self):
        assert _actionability_score({"reason_detail": "no"}) == 0.0

    def test_verifiability_with_scores_and_assay(self):
        entry = {
            "score_activity": 0.78, "score_safety": 0.85,
            "score_ensemble": 0.75,
            "assay_result": ">128", "assay_unit": "ug/mL",
        }
        assert _verifiability_score(entry) > 0.0

    def test_verifiability_no_data(self):
        assert _verifiability_score({}) == 0.0

    def test_structured_metadata_lab_entry(self):
        entry = {
            "entry_id": 1,
            "reason_category": "lab_inactive",
            "assay_type": "MIC", "assay_result": ">64", "assay_unit": "ug/mL",
        }
        assert _structured_metadata_score(entry) >= 1.0

    def test_structured_metadata_non_lab(self):
        score = _structured_metadata_score({"reason_category": "pre_selection_reject"})
        assert score == 0.25

    def test_structured_metadata_with_superseded(self):
        entry = {"entry_id": 1, "reason_category": "pre_selection_reject", "superseded_by": 0}
        assert _structured_metadata_score(entry) >= 1.0

    def test_interpretation_long_analytical_notes(self):
        entry = {
            "reason_detail": "Score too low.",
            "reviewer_notes": (
                "This failure suggests a systematic issue with the safety scorer "
                "for high-GRAVY candidates. The current threshold may be too "
                "conservative for designed amphipathic sequences. Consider a "
                "two-tier flag approach that distinguishes structural from "
                "non-specific membrane activity."
            ),
        }
        assert _interpretation_score(entry) >= 0.5

    def test_interpretation_no_notes(self):
        assert _interpretation_score({"reason_detail": "Failed."}) == 0.0


class TestBuildMarkdown:
    def test_markdown_contains_classification(self):
        entry = _make_entry()
        result = classify_entry(entry)
        md = build_markdown(result)
        assert result["classification"] in md
        assert str(result["total_score"]) in md

    def test_markdown_contains_caveat(self):
        entry = _make_entry()
        result = classify_entry(entry)
        md = build_markdown(result)
        assert "Computational classification only" in md


class TestBuildOutput:
    def test_output_contains_entry_and_result(self):
        entry = _make_entry()
        result = classify_entry(entry)
        output = build_output(entry, result)
        assert output["input_entry"] is entry
        assert output["result"] is result
        assert output["classifier_version"] == "v1.0.0"
        assert "framework" in output

    def test_output_json_serializable(self):
        entry = _make_entry()
        result = classify_entry(entry)
        output = build_output(entry, result)
        dumped = json.dumps(output)
        assert len(dumped) > 0
        reloaded = json.loads(dumped)
        assert reloaded["result"]["classification"] == result["classification"]


class TestLoadEntry:
    def test_load_entry_from_dict(self):
        entry = {"candidate_id": "X"}
        assert load_entry(entry) is entry

    def test_load_entry_from_json_string(self):
        entry = load_entry('{"candidate_id": "X"}')
        assert entry["candidate_id"] == "X"

    def test_load_entry_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON string"):
            load_entry("not-json")

    def test_load_entry_file_not_found_raises(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_entry("/nonexistent/path.json")


class TestCLI:
    def test_cli_entry_flag(self):
        r = subprocess.run(
            [PYTHON, "scripts/classify_negative_result_informativeness.py",
             "--entry", json.dumps(_make_entry())],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
            cwd=str(_REPO_DIR),
        )
        assert r.returncode == 0
        assert "INFORMATIVE" in r.stdout

    def test_cli_input_file(self):
        example = _REPO_DIR / "examples/negative_result_entry_example.json"
        r = subprocess.run(
            [PYTHON, "scripts/classify_negative_result_informativeness.py",
             "--input", str(example)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
            cwd=str(_REPO_DIR),
        )
        assert r.returncode == 0
        assert "INFORMATIVE" in r.stdout

    def test_cli_missing_flag(self):
        r = subprocess.run(
            [PYTHON, "scripts/classify_negative_result_informativeness.py"],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
            cwd=str(_REPO_DIR),
        )
        assert r.returncode == 2

    def test_cli_out_json_creates_file(self, tmp_path):
        out = tmp_path / "result.json"
        r = subprocess.run(
            [PYTHON, "scripts/classify_negative_result_informativeness.py",
             "--entry", json.dumps(_make_entry()),
             "--out-json", str(out)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
            cwd=str(_REPO_DIR),
        )
        assert r.returncode == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert data["result"]["classification"] == "INFORMATIVE"

    def test_cli_out_md_creates_file(self, tmp_path):
        out = tmp_path / "result.md"
        r = subprocess.run(
            [PYTHON, "scripts/classify_negative_result_informativeness.py",
             "--entry", json.dumps(_make_entry()),
             "--out-md", str(out)],
            capture_output=True, text=True,
            env={"PYTHONPATH": "src"},
            cwd=str(_REPO_DIR),
        )
        assert r.returncode == 0
        assert out.exists()
        content = out.read_text()
        assert "INFORMATIVE" in content
        assert "Computational classification only" in content


class TestExampleFile:
    def test_example_file_validates_informative(self):
        """The example file should classify as INFORMATIVE."""
        path = _REPO_DIR / "examples/negative_result_entry_example.json"
        assert path.exists()
        entry = load_entry(path)
        result = classify_entry(entry)
        assert result["classification"] == "INFORMATIVE"
        assert result["total_score"] >= 6.0

    def test_example_file_is_marked_example(self):
        """The example file should have an EXAMPLE warning."""
        path = _REPO_DIR / "examples/negative_result_entry_example.json"
        entry = load_entry(path)
        assert "EXAMPLE" in json.dumps(entry).upper() or "NOT REAL" in json.dumps(entry).upper()
