"""Tests for lab_results.py — active-learning loop ingestion.

Verifies that:
  - Valid lab result JSON loads and validates against schema
  - Invalid lab results are rejected with useful errors
  - summarise_lab_results produces correct aggregates
  - candidate_result_map groups correctly
"""
from __future__ import annotations

import json

import pytest

from openamp_foundry.data.lab_results import (
    candidate_result_map,
    load_lab_result,
    summarise_lab_results,
)


def _valid_result(**overrides) -> dict:
    base = {
        "result_id": "RES-001",
        "candidate_id": "SEED-005_VAR_049",
        "assay_type": "MIC",
        "organism_or_cell_line": "E. coli ATCC 25922",
        "result_value": 4.0,
        "result_unit": "µg/mL",
        "result_qualitative": "active",
        "positive_control_passed": True,
        "negative_control_passed": True,
        "positive_control_id": "ciprofloxacin 0.25 µg/mL",
        "negative_control_id": "PBS",
        "assay_date": "2026-07-01",
        "replicate_count": 3,
        "performed_by_lab": "University Test Lab",
        "raw_data_sha256": None,
        "computational_candidate_certificate_hash": "abc123def456",
        "notes": None,
        "disclaimer": (
            "This is an experimental result on a computationally nominated candidate. "
            "It does not constitute a drug or clinical claim."
        ),
    }
    base.update(overrides)
    return base


@pytest.fixture
def valid_result_file(tmp_path):
    result = _valid_result()
    path = tmp_path / "RES-001.json"
    path.write_text(json.dumps(result))
    return path


@pytest.fixture
def results_dir(tmp_path):
    for i in range(3):
        result = _valid_result(
            result_id=f"RES-{i:03d}",
            candidate_id=f"CAND-{i:03d}",
            assay_date=f"2026-07-0{i+1}",
        )
        (tmp_path / f"RES-{i:03d}.json").write_text(json.dumps(result))
    return tmp_path


class TestLoadLabResult:
    def test_valid_result_loads(self, valid_result_file):
        result = load_lab_result(valid_result_file)
        assert result["result_id"] == "RES-001"
        assert result["candidate_id"] == "SEED-005_VAR_049"
        assert result["assay_type"] == "MIC"

    def test_invalid_assay_type_rejected(self, tmp_path):
        result = _valid_result(assay_type="unknown_assay")
        path = tmp_path / "bad.json"
        path.write_text(json.dumps(result))
        with pytest.raises(Exception):
            load_lab_result(path)

    def test_missing_required_field_rejected(self, tmp_path):
        result = _valid_result()
        del result["candidate_id"]
        path = tmp_path / "missing.json"
        path.write_text(json.dumps(result))
        with pytest.raises(Exception):
            load_lab_result(path)

    def test_negative_replicate_count_rejected(self, tmp_path):
        result = _valid_result(replicate_count=0)
        path = tmp_path / "bad_reps.json"
        path.write_text(json.dumps(result))
        with pytest.raises(Exception):
            load_lab_result(path)

    def test_null_result_value_allowed(self, tmp_path):
        result = _valid_result(result_value=None, result_qualitative="inconclusive")
        path = tmp_path / "null_val.json"
        path.write_text(json.dumps(result))
        loaded = load_lab_result(path)
        assert loaded["result_value"] is None

    def test_file_not_found_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_lab_result(tmp_path / "nonexistent.json")


class TestSummariseLabResults:
    def test_empty_results_handled(self):
        summary = summarise_lab_results([])
        assert summary["n_results"] == 0
        assert "disclaimer" in summary

    def test_n_results_correct(self):
        results = [_valid_result(result_id=f"R{i}") for i in range(5)]
        summary = summarise_lab_results(results)
        assert summary["n_results"] == 5

    def test_by_assay_type_counts(self):
        results = [
            _valid_result(result_id="R1", assay_type="MIC"),
            _valid_result(result_id="R2", assay_type="MIC"),
            _valid_result(result_id="R3", assay_type="hemolysis_RBC"),
        ]
        summary = summarise_lab_results(results)
        assert summary["by_assay_type"]["MIC"] == 2
        assert summary["by_assay_type"]["hemolysis_RBC"] == 1

    def test_by_qualitative_counts(self):
        results = [
            _valid_result(result_id="R1", result_qualitative="active"),
            _valid_result(result_id="R2", result_qualitative="inactive"),
            _valid_result(result_id="R3", result_qualitative="active"),
        ]
        summary = summarise_lab_results(results)
        assert summary["by_qualitative_result"]["active"] == 2
        assert summary["by_qualitative_result"]["inactive"] == 1

    def test_valid_controls_counted(self):
        results = [
            _valid_result(result_id="R1", positive_control_passed=True, negative_control_passed=True),
            _valid_result(result_id="R2", positive_control_passed=True, negative_control_passed=False),
        ]
        summary = summarise_lab_results(results)
        assert summary["n_valid_controls"] == 1

    def test_disclaimer_present(self):
        results = [_valid_result()]
        summary = summarise_lab_results(results)
        assert "disclaimer" in summary
        assert len(summary["disclaimer"]) > 20


class TestCandidateResultMap:
    def test_groups_by_candidate_id(self):
        results = [
            _valid_result(result_id="R1", candidate_id="CAND-001"),
            _valid_result(result_id="R2", candidate_id="CAND-001"),
            _valid_result(result_id="R3", candidate_id="CAND-002"),
        ]
        mapping = candidate_result_map(results)
        assert len(mapping["CAND-001"]) == 2
        assert len(mapping["CAND-002"]) == 1

    def test_unknown_candidate_not_in_map(self):
        results = [_valid_result(candidate_id="CAND-001")]
        mapping = candidate_result_map(results)
        assert "CAND-999" not in mapping

    def test_empty_results_gives_empty_map(self):
        assert candidate_result_map([]) == {}
