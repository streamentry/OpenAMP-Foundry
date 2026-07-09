"""Tests for rejection_taxonomy.schema.json."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.utils.io import read_json

_SCHEMA_DIR = Path(__file__).parents[2] / "schemas"
_EXAMPLES_DIR = Path(__file__).parents[2] / "examples"

TAXONOMY_SCHEMA = _SCHEMA_DIR / "rejection_taxonomy.schema.json"
TAXONOMY_EXAMPLE = _EXAMPLES_DIR / "rejection_taxonomy_example.json"


def _valid_entry() -> dict:
    return {
        "code": "PIPE_ACTIVITY_LOW",
        "category": "pipeline",
        "label": "Activity score below threshold",
        "description": "The pipeline activity score falls below the configured minimum gate threshold.",
        "severity": "soft",
        "evidence_impact": "downgrade_by_1",
        "applies_at_stage": "after_scoring",
        "related_reason_category": "pre_selection_reject",
        "example": "Activity score 0.42 below minimum threshold 0.50.",
    }


def _valid_taxonomy() -> list[dict]:
    return [_valid_entry()]


class TestRejectionTaxonomySchema:
    def test_schema_file_exists(self):
        assert TAXONOMY_SCHEMA.exists()

    def test_valid_entry_passes(self):
        validate_json_schema([_valid_entry()], TAXONOMY_SCHEMA)

    def test_missing_code_fails(self):
        entry = _valid_entry()
        del entry["code"]
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_missing_required_field_fails(self):
        entry = {"code": "TEST_CODE"}
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_invalid_category_fails(self):
        entry = _valid_entry()
        entry["category"] = "invalid_phase"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_invalid_severity_fails(self):
        entry = _valid_entry()
        entry["severity"] = "critical"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_invalid_evidence_impact_fails(self):
        entry = _valid_entry()
        entry["evidence_impact"] = "invalid_impact"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_invalid_applies_at_stage_fails(self):
        entry = _valid_entry()
        entry["applies_at_stage"] = "never"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_invalid_reason_category_fails(self):
        entry = _valid_entry()
        entry["related_reason_category"] = "not_a_valid_category"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_code_pattern_validation(self):
        entry = _valid_entry()
        entry["code"] = "invalid code"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_min_description_length(self):
        entry = _valid_entry()
        entry["description"] = "Short"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_multiple_valid_entries(self):
        entries = [
            _valid_entry(),
            {
                "code": "PRE_SEQ_INVALID",
                "category": "pre_selection",
                "label": "Invalid sequence",
                "description": "Sequence contains non-canonical amino-acid symbols.",
                "severity": "hard",
                "evidence_impact": "claim_unsupported",
                "applies_at_stage": "pre_selection",
                "related_reason_category": "pre_selection_reject",
                "example": "Sequence contains 'X' at position 5.",
            },
        ]
        validate_json_schema(entries, TAXONOMY_SCHEMA)

    def test_optional_fields_accepted(self):
        entry = _valid_entry()
        entry["example"] = "Optional example text."
        validate_json_schema([entry], TAXONOMY_SCHEMA)

    def test_all_categories_covered(self):
        taxonomy = read_json(TAXONOMY_EXAMPLE)
        categories = {e["category"] for e in taxonomy}
        expected = {"pre_selection", "pipeline", "diversity", "reviewer", "lab", "lifecycle"}
        assert categories == expected, (
            f"Missing categories: {expected - categories}"
        )

    def test_all_severities_covered(self):
        taxonomy = read_json(TAXONOMY_EXAMPLE)
        severities = {e["severity"] for e in taxonomy}
        expected = {"hard", "soft", "informational"}
        assert severities == expected, (
            f"Missing severities: {expected - severities}"
        )

    def test_all_evidence_impacts_covered(self):
        taxonomy = read_json(TAXONOMY_EXAMPLE)
        impacts = {e["evidence_impact"] for e in taxonomy}
        expected = {"claim_unsupported", "downgrade_by_1", "downgrade_by_2", "no_impact"}
        assert impacts == expected, (
            f"Missing evidence impacts: {expected - impacts}"
        )

    def test_example_file_validates_against_schema(self):
        validate_json_schema(read_json(TAXONOMY_EXAMPLE), TAXONOMY_SCHEMA)

    def test_example_has_all_unique_codes(self):
        taxonomy = read_json(TAXONOMY_EXAMPLE)
        codes = [e["code"] for e in taxonomy]
        assert len(codes) == len(set(codes)), "Duplicate codes found in example"

    def test_each_code_has_a_category(self):
        taxonomy = read_json(TAXONOMY_EXAMPLE)
        for entry in taxonomy:
            assert entry["category"] in {
                "pre_selection", "pipeline", "diversity", "reviewer", "lab", "lifecycle"
            }, f"Entry {entry['code']} has invalid category"
