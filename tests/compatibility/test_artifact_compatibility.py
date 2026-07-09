"""Tests for cross-artifact schema compatibility checks — prevents schema drift.

Dry-lab only — does not measure biological activity.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from openamp_foundry.compatibility.artifact_compatibility import (
    check_schema_conventions,
    run_compatibility_check,
    SchemaCompatibilityResult,
    UNIVERSAL_REQUIRED_FIELDS,
    CONVENTION_CHECKS,
)


def _valid_schema() -> dict:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "TestSchema",
        "type": "object",
        "properties": {
            "dry_lab_only": {
                "type": "boolean",
                "const": True,
            },
            "version": {
                "type": "string",
                "pattern": "^\\d+\\.\\d+\\.\\d+$",
            },
        },
        "required": ["dry_lab_only", "version"],
        "additionalProperties": False,
    }


def test_candidate_manifest_schema_passes():
    path = Path(__file__).parent.parent.parent / "schemas" / "candidate_manifest.schema.json"
    schema = json.loads(path.read_text())
    result = check_schema_conventions("candidate_manifest", schema)
    assert result.passed, f"candidate_manifest failed: {result.errors}"
    assert result.dry_lab_only


def test_benchmark_card_schema_passes():
    path = Path(__file__).parent.parent.parent / "schemas" / "benchmark_card.schema.json"
    schema = json.loads(path.read_text())
    result = check_schema_conventions("benchmark_card", schema)
    assert result.passed, f"benchmark_card failed: {result.errors}"
    assert result.dry_lab_only


def test_simulation_result_schema_detected():
    path = Path(__file__).parent.parent.parent / "schemas" / "simulation_result.schema.json"
    assert path.exists(), "simulation_result.schema.json must exist"
    schema = json.loads(path.read_text())
    result = check_schema_conventions("simulation_result", schema)
    assert not result.passed
    assert any("dry_lab_only" in e for e in result.errors)
    assert result.dry_lab_only


def test_missing_dry_lab_only_in_properties_fails():
    schema = _valid_schema()
    del schema["properties"]["dry_lab_only"]
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("dry_lab_only" in e and "properties" in e for e in result.errors)


def test_missing_dry_lab_only_in_required_fails():
    schema = _valid_schema()
    schema["required"] = ["version"]
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("dry_lab_only" in e and "required" in e for e in result.errors)


def test_dry_lab_only_not_const_true_fails():
    schema = _valid_schema()
    schema["properties"]["dry_lab_only"]["const"] = False
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("const" in e for e in result.errors)


def test_missing_version_in_properties_fails():
    schema = _valid_schema()
    del schema["properties"]["version"]
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("version" in e and "properties" in e for e in result.errors)


def test_version_not_type_string_fails():
    schema = _valid_schema()
    schema["properties"]["version"] = {"type": "integer"}
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("type: string" in e for e in result.errors)


def test_evidence_level_not_type_integer_fails():
    schema = _valid_schema()
    schema["properties"]["evidence_level"] = {"type": "string"}
    schema["required"].append("evidence_level")
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("type: integer" in e for e in result.errors)


def test_evidence_level_minimum_not_one_fails():
    schema = _valid_schema()
    schema["properties"]["evidence_level"] = {"type": "integer", "minimum": 0, "maximum": 6}
    schema["required"].append("evidence_level")
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("minimum" in e for e in result.errors)


def test_evidence_level_maximum_not_six_fails():
    schema = _valid_schema()
    schema["properties"]["evidence_level"] = {"type": "integer", "minimum": 1, "maximum": 5}
    schema["required"].append("evidence_level")
    result = check_schema_conventions("test", schema)
    assert not result.passed
    assert any("maximum" in e for e in result.errors)


def test_valid_synthetic_schema_passes():
    schema = _valid_schema()
    result = check_schema_conventions("test", schema)
    assert result.passed
    assert result.dry_lab_only


def test_run_compatibility_check_returns_expected_keys():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        schema = _valid_schema()
        (td_path / "test.schema.json").write_text(json.dumps(schema))
        report = run_compatibility_check(td_path)
    assert "total" in report
    assert "passed" in report
    assert "failed" in report
    assert "all_passed" in report
    assert "dry_lab_only" in report
    assert report["total"] == 1
    assert report["passed"] == 1
    assert report["failed"] == 0
    assert report["all_passed"] is True


def test_run_compatibility_check_dry_lab_only():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / "test.schema.json").write_text(json.dumps(_valid_schema()))
        report = run_compatibility_check(td_path)
    assert report["dry_lab_only"] is True


def test_schema_compatibility_result_default_dry_lab_only():
    result = SchemaCompatibilityResult(
        schema_name="test",
        schema_path="/dev/null",
        passed=True,
        errors=[],
        warnings=[],
    )
    assert result.dry_lab_only


def test_missing_additional_properties_produces_warning_not_error():
    schema = _valid_schema()
    del schema["additionalProperties"]
    result = check_schema_conventions("test", schema)
    assert result.passed
    assert any("additionalProperties" in w for w in result.warnings)


def test_missing_dollar_schema_produces_warning():
    schema = _valid_schema()
    del schema["$schema"]
    result = check_schema_conventions("test", schema)
    assert result.passed
    assert any("$schema" in w for w in result.warnings)


def test_run_compatibility_check_with_multiple_schemas():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        for name in ("alpha", "beta", "gamma"):
            (td_path / f"{name}.schema.json").write_text(json.dumps(_valid_schema()))
        report = run_compatibility_check(td_path)
    assert report["total"] == 3
    assert report["passed"] == 3
    assert report["failed"] == 0
    assert report["all_passed"] is True


def test_universal_required_fields_contains_dry_lab_only_and_version():
    assert "dry_lab_only" in UNIVERSAL_REQUIRED_FIELDS
    assert "version" in UNIVERSAL_REQUIRED_FIELDS


def test_convention_checks_contains_expected_keys():
    assert "dry_lab_only" in CONVENTION_CHECKS
    assert "version" in CONVENTION_CHECKS
    assert "evidence_level" in CONVENTION_CHECKS
