"""Tests for negative_result_entry.schema.json and pilot_preregistration.schema.json."""
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

_SCHEMA_DIR = Path(__file__).parents[2] / "schemas"

NEGATIVE_RESULT_SCHEMA = _SCHEMA_DIR / "negative_result_entry.schema.json"
PREREG_SCHEMA = _SCHEMA_DIR / "pilot_preregistration.schema.json"


class TestNegativeResultSchema:
    def test_schema_file_exists(self):
        assert NEGATIVE_RESULT_SCHEMA.exists()

    def test_valid_entry_passes(self):
        entry = {
            "entry_id": 1,
            "date": "2026-08-01",
            "candidate_id": "WAVE0.5-001",
            "sequence": "ACDEFGHIKLMNPQRSTVWY",
            "reason_category": "pre_selection_reject",
            "reason_detail": "Net charge exceeds safety gate",
            "pipeline_version": "v0.5.49",
            "source_batch": "wave0.5",
        }
        validate_json_schema(entry, NEGATIVE_RESULT_SCHEMA)

    def test_missing_required_fails(self):
        entry = {"entry_id": 1}
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(entry, NEGATIVE_RESULT_SCHEMA)

    def test_invalid_reason_category_fails(self):
        entry = {
            "entry_id": 1,
            "date": "2026-08-01",
            "candidate_id": "X",
            "sequence": "AAAA",
            "reason_category": "invalid_category",
            "reason_detail": "test",
            "pipeline_version": "v1",
            "source_batch": "test",
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(entry, NEGATIVE_RESULT_SCHEMA)

    def test_optional_fields_accepted(self):
        entry = {
            "entry_id": 2,
            "date": "2026-08-15",
            "candidate_id": "WAVE0.5-012",
            "sequence": "ACDEFGHIKLMNPQRSTVWY",
            "reason_category": "lab_inactive",
            "reason_detail": "MIC > 64 ug/mL",
            "pipeline_version": "v0.5.49",
            "source_batch": "wave0.5",
            "assay_type": "MIC",
            "assay_result": "128",
            "assay_unit": "ug/mL",
            "score_activity": 0.82,
            "score_safety": 0.79,
        }
        validate_json_schema(entry, NEGATIVE_RESULT_SCHEMA)


class TestPilotPreregistrationSchema:
    def test_schema_file_exists(self):
        assert PREREG_SCHEMA.exists()

    def test_valid_registration_passes(self):
        entry = {
            "pilot_name": "Wave 1 Pilot",
            "preregistered_at": "2026-08-01T00:00:00Z",
            "preregistered_by": "agent",
            "candidate_pool_source": "outputs/phase3_ranked.jsonl",
            "selection_rules": {"top_n": 20, "min_novelty": 0.3},
            "exclusion_criteria": ["safety < 0.5", "novelty < 0.2"],
            "pass_fail_criteria": {"min_active": 2, "max_toxic": 3},
        }
        validate_json_schema(entry, PREREG_SCHEMA)

    def test_missing_required_fails(self):
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema({"pilot_name": "test"}, PREREG_SCHEMA)
