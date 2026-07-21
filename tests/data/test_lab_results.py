"""Tests for lab_results.py — active-learning loop ingestion.

Verifies that:
  - Valid lab result JSON loads and validates against schema
  - Invalid lab results are rejected with useful errors
  - summarise_lab_results produces correct aggregates
  - candidate_result_map groups correctly
  - load_lab_results_dir loads all valid files, skips invalid, returns sorted
"""
from __future__ import annotations

import json
import warnings

import pytest

from openamp_foundry.data.lab_results import (
    candidate_result_map,
    duplicate_result_ids,
    load_lab_result,
    load_lab_results_dir,
    load_lab_results_dir_with_errors,
    summarise_candidate_outcomes,
    summarise_lab_results,
    validate_lab_results_directory,
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

    def test_qualitative_counts_separate_raw_and_usable_observations(self):
        results = [
            _valid_result(result_id="R1", result_qualitative="active"),
            _valid_result(
                result_id="R2",
                result_qualitative="toxic",
                positive_control_passed=False,
            ),
            _valid_result(result_id="R3", result_qualitative="inactive"),
        ]

        summary = summarise_lab_results(results)

        assert summary["by_qualitative_result"] == {
            "active": 1,
            "inactive": 1,
            "toxic": 1,
        }
        assert summary["by_usable_qualitative_result"] == {
            "active": 1,
            "inactive": 1,
        }
        assert summary["n_valid_controls"] == 2

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


def test_duplicate_result_ids_are_reported_once():
    results = [
        _valid_result(result_id="R-1"),
        _valid_result(result_id="R-1", candidate_id="CAND-2"),
        _valid_result(result_id="R-2"),
    ]

    assert duplicate_result_ids(results) == ["R-1"]


class TestSummariseCandidateOutcomes:
    def test_rolls_up_candidate_status(self):
        results = [
            _valid_result(result_id="R1", candidate_id="CAND-001", result_qualitative="active"),
            _valid_result(
                result_id="R2",
                candidate_id="CAND-001",
                assay_type="hemolysis_RBC",
                result_qualitative="toxic",
                positive_control_passed=False,
            ),
            _valid_result(result_id="R3", candidate_id="CAND-002", result_qualitative="inactive"),
        ]
        rows = summarise_candidate_outcomes(results)
        by_id = {row["candidate_id"]: row for row in rows}
        assert by_id["CAND-001"]["n_results"] == 2
        assert by_id["CAND-001"]["n_usable_results"] == 1
        assert by_id["CAND-001"]["has_any_active"] is True
        assert by_id["CAND-001"]["has_any_toxic"] is False
        assert by_id["CAND-001"]["raw_has_any_toxic"] is True
        assert by_id["CAND-001"]["qualitative_results"] == ["active"]
        assert by_id["CAND-001"]["raw_qualitative_results"] == ["active", "toxic"]
        assert by_id["CAND-001"]["all_controls_passed"] is False
        assert by_id["CAND-001"]["control_fail_result_ids"] == ["R2"]
        assert by_id["CAND-002"]["all_controls_passed"] is True

    def test_failed_control_only_result_has_no_usable_outcome(self):
        result = _valid_result(
            result_id="R4",
            candidate_id="CAND-004",
            result_qualitative="active",
            positive_control_passed=False,
        )
        row = summarise_candidate_outcomes([result])[0]
        assert row["n_results"] == 1
        assert row["n_usable_results"] == 0
        assert row["has_any_active"] is False
        assert row["raw_has_any_active"] is True
        assert row["control_fail_result_ids"] == ["R4"]


class TestLoadLabResultsDir:
    def test_empty_directory_returns_empty_list(self, tmp_path):
        results = load_lab_results_dir(tmp_path)
        assert results == []

    @pytest.mark.parametrize("path_kind", ["missing", "file"])
    def test_result_input_must_be_existing_directory(self, tmp_path, path_kind):
        path = tmp_path / "results.json"
        if path_kind == "file":
            path.write_text("{}")

        expected = "not found" if path_kind == "missing" else "not a directory"
        with pytest.raises((FileNotFoundError, NotADirectoryError), match=expected):
            validate_lab_results_directory(path)

        with pytest.raises((FileNotFoundError, NotADirectoryError), match=expected):
            load_lab_results_dir_with_errors(path)

    def test_loads_all_valid_files(self, results_dir):
        results = load_lab_results_dir(results_dir)
        assert len(results) == 3

    def test_structured_loader_retains_invalid_file_provenance(self, tmp_path):
        good = _valid_result(result_id="GOOD-001")
        (tmp_path / "good.json").write_text(json.dumps(good))
        (tmp_path / "bad.json").write_text(json.dumps({"result_id": "BAD-001"}))

        results, errors = load_lab_results_dir_with_errors(tmp_path)

        assert [r["result_id"] for r in results] == ["GOOD-001"]
        assert errors[0]["file"] == "bad.json"
        assert errors[0]["error"]

    def test_sorted_by_assay_date(self, tmp_path):
        date_map = {0: "2026-07-03", 1: "2026-07-01", 2: "2026-07-02"}
        for i in range(3):
            result = _valid_result(
                result_id=f"RES-{i:03d}",
                candidate_id=f"CAND-{i:03d}",
                assay_date=date_map[i],
            )
            (tmp_path / f"RES-{i:03d}.json").write_text(json.dumps(result))
        results = load_lab_results_dir(tmp_path)
        dates = [r["assay_date"] for r in results]
        assert dates == sorted(dates)
        assert dates[0] == "2026-07-01"

    def test_sorted_by_result_id_within_same_date(self, tmp_path):
        for i in [3, 1, 2]:
            result = _valid_result(
                result_id=f"RES-{i:03d}",
                candidate_id=f"CAND-{i:03d}",
                assay_date="2026-07-10",
            )
            (tmp_path / f"RES-{i:03d}.json").write_text(json.dumps(result))
        results = load_lab_results_dir(tmp_path)
        ids = [r["result_id"] for r in results]
        assert ids == sorted(ids)

    def test_skips_invalid_json_file_with_warning(self, tmp_path):
        valid = _valid_result(result_id="GOOD-001", candidate_id="CAND-A", assay_date="2026-07-01")
        (tmp_path / "good.json").write_text(json.dumps(valid))
        (tmp_path / "bad.json").write_text("this is not valid json {{{")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = load_lab_results_dir(tmp_path)
        assert len(results) == 1
        assert results[0]["result_id"] == "GOOD-001"
        assert any("bad.json" in str(w.message) or "Skipped" in str(w.message) for w in caught)

    def test_skips_schema_invalid_file_with_warning(self, tmp_path):
        valid = _valid_result(result_id="GOOD-001", candidate_id="CAND-A", assay_date="2026-07-01")
        invalid = _valid_result()
        del invalid["candidate_id"]
        (tmp_path / "good.json").write_text(json.dumps(valid))
        (tmp_path / "invalid_schema.json").write_text(json.dumps(invalid))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            results = load_lab_results_dir(tmp_path)
        assert len(results) == 1
        assert results[0]["result_id"] == "GOOD-001"
        assert any("Skipped" in str(w.message) for w in caught)

    def test_non_json_files_ignored(self, tmp_path):
        valid = _valid_result(result_id="R001", candidate_id="C001", assay_date="2026-07-01")
        (tmp_path / "result.json").write_text(json.dumps(valid))
        (tmp_path / "notes.txt").write_text("not a json file")
        (tmp_path / "data.csv").write_text("col1,col2\n1,2")
        results = load_lab_results_dir(tmp_path)
        assert len(results) == 1
