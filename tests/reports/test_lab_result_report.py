"""Tests for the portable lab-result report contract."""

import json
import shutil
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.reports.lab_result_report import (
    LAB_RESULT_REPORT_SCHEMA,
    build_lab_result_report,
    validate_lab_result_report,
)


ROOT = Path(__file__).parents[2]


def test_schema_exists_and_is_valid_json():
    schema = json.loads(LAB_RESULT_REPORT_SCHEMA.read_text(encoding="utf-8"))
    assert schema["$id"].endswith("lab_result_report/1.0.0")
    assert schema["title"] == "OpenAMP Lab Result Report"


def test_example_report_validates_against_portable_schema():
    report = build_lab_result_report(ROOT / "examples" / "lab_results")
    validate_lab_result_report(report)
    validate_json_schema(report, LAB_RESULT_REPORT_SCHEMA)


def test_schema_rejects_missing_data_origin():
    report = build_lab_result_report(ROOT / "examples" / "lab_results")
    del report["data_origin"]
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(report, LAB_RESULT_REPORT_SCHEMA)


def test_schema_rejects_unknown_input_validation_status():
    report = build_lab_result_report(ROOT / "examples" / "lab_results")
    report["input_validation_status"] = "synthetic_is_real"
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(report, LAB_RESULT_REPORT_SCHEMA)


def test_schema_rejects_malformed_candidate_rollup():
    report = build_lab_result_report(ROOT / "examples" / "lab_results")
    report["by_candidate"][0]["n_results"] = 0
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(report, LAB_RESULT_REPORT_SCHEMA)


def test_duplicate_result_ids_remain_valid_audit_data(tmp_path):
    source = ROOT / "examples" / "lab_results" / "RES-SYN-001.json"
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    shutil.copyfile(source, results_dir / "first.json")
    shutil.copyfile(source, results_dir / "second.json")

    report = build_lab_result_report(results_dir)

    assert report["n_duplicate_lab_result_ids"] == 1
    assert report["raw_data_provenance"]["result_ids_without_raw_data_sha256"] == [
        "RES-SYN-001", "RES-SYN-001"
    ]
