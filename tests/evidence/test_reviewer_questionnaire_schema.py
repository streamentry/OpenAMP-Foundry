"""Tests for reviewer_questionnaire.schema.json."""
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

_SCHEMA_DIR = Path(__file__).parents[2] / "schemas"

REVIEWER_QUESTIONNAIRE_SCHEMA = _SCHEMA_DIR / "reviewer_questionnaire.schema.json"


def _valid_questionnaire() -> dict:
    return {
        "reviewer_id": "REV-001",
        "packet_id": "ERP-2026-07-09-001",
        "reviewed_at": "2026-07-15T14:30:00Z",
        "scientific_validity": 4,
        "benchmark_adequacy": 3,
        "safety_concerns": False,
        "recommendation": "revise",
        "comments": "The candidate selection rationale is clear but benchmark caveats could be more detailed.",
        "conflict_of_interest_declared": False,
    }


class TestReviewerQuestionnaireSchema:
    def test_schema_file_exists(self):
        assert REVIEWER_QUESTIONNAIRE_SCHEMA.exists()

    def test_valid_questionnaire_passes(self):
        validate_json_schema(_valid_questionnaire(), REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_missing_required_field_fails(self):
        q = {"reviewer_id": "REV-001"}
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_safety_concerns_requires_description(self):
        q = _valid_questionnaire()
        q["safety_concerns"] = True
        with pytest.raises(jsonschema.ValidationError, match="safety_concern_description"):
            validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_safety_concern_description_provided_passes(self):
        q = _valid_questionnaire()
        q["safety_concerns"] = True
        q["safety_concern_description"] = "Hemolysis risk not adequately addressed for high-charge candidates."
        validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_invalid_scientific_validity_fails(self):
        q = _valid_questionnaire()
        q["scientific_validity"] = 6
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_invalid_scientific_validity_zero_fails(self):
        q = _valid_questionnaire()
        q["scientific_validity"] = 0
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_invalid_recommendation_fails(self):
        q = _valid_questionnaire()
        q["recommendation"] = "maybe"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_approve_recommendation_passes(self):
        q = _valid_questionnaire()
        q["recommendation"] = "approve"
        validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_reject_recommendation_passes(self):
        q = _valid_questionnaire()
        q["recommendation"] = "reject"
        validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_conflict_of_interest_requires_detail(self):
        q = _valid_questionnaire()
        q["conflict_of_interest_declared"] = True
        with pytest.raises(jsonschema.ValidationError, match="conflict_of_interest_detail"):
            validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_conflict_of_interest_with_detail_passes(self):
        q = _valid_questionnaire()
        q["conflict_of_interest_declared"] = True
        q["conflict_of_interest_detail"] = "Former collaborator on AMP database curation."
        q["domain_expertise"] = ["antimicrobial_peptides"]
        validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_domain_expertise_other_no_description_fails(self):
        q = _valid_questionnaire()
        q["domain_expertise"] = ["other"]
        q["conflict_of_interest_declared"] = True
        q["conflict_of_interest_detail"] = "None."
        validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)

    def test_all_fields_maximal_passes(self):
        q = {
            "reviewer_id": "REV-002",
            "packet_id": "ERP-2026-07-09-002",
            "reviewed_at": "2026-07-20T09:00:00Z",
            "scientific_validity": 5,
            "benchmark_adequacy": 4,
            "safety_concerns": False,
            "recommendation": "approve",
            "comments": "Well-structured review packet with appropriate caveats.",
            "conflict_of_interest_declared": False,
            "domain_expertise": ["antimicrobial_peptides", "computational_biology"],
        }
        validate_json_schema(q, REVIEWER_QUESTIONNAIRE_SCHEMA)
