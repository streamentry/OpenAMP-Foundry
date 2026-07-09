"""Tests for external_review_packet.schema.json."""
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

_SCHEMA_DIR = Path(__file__).parents[2] / "schemas"
_EXAMPLES_DIR = Path(__file__).parents[2] / "examples"

EXTERNAL_REVIEW_SCHEMA = _SCHEMA_DIR / "external_review_packet.schema.json"


def _valid_packet() -> dict:
    return {
        "packet_id": "ERP-2026-07-09-001",
        "version": "1.0.0",
        "generated_at": "2026-07-09T12:00:00Z",
        "pipeline_version": "v0.5.72",
        "git_sha": "abcdef1234567890abcdef1234567890abcdef12",
        "candidate_count": 1,
        "candidates": [
            {
                "candidate_id": "CAND-001",
                "sequence": "KLAKLAKKLAKLAK",
                "ensemble_score": 0.84,
                "proof_ladder_level": 2,
            }
        ],
        "benchmark_summary": {
            "auroc": 0.78,
            "benchmark_name": "500-AMP benchmark",
            "n_positives": 500,
            "n_negatives": 500,
        },
        "calibration_summary": {
            "brier_score": 0.32,
            "calibration_slope": 0.43,
            "calibration_assessment": "uninformative",
        },
        "limitations": [
            "Computational outputs are hypotheses and review aids. They are not biological proof."
        ],
        "safety_attestations": {
            "reviewed_by_human": False,
            "safety_gate_passed": True,
            "no_known_toxicity_claim": True,
        },
        "dry_lab_only_attestation": True,
        "proof_ladder_level": 2,
        "contact": "reviewer@example.com",
    }


class TestExternalReviewPacketSchema:
    def test_schema_file_exists(self):
        assert EXTERNAL_REVIEW_SCHEMA.exists()

    def test_valid_packet_passes(self):
        validate_json_schema(_valid_packet(), EXTERNAL_REVIEW_SCHEMA)

    def test_missing_required_field_fails(self):
        packet = {"packet_id": "ERP-001"}
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_dry_lab_only_attestation_false_fails(self):
        packet = _valid_packet()
        packet["dry_lab_only_attestation"] = False
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_dry_lab_only_attestation_missing_fails(self):
        packet = _valid_packet()
        del packet["dry_lab_only_attestation"]
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_invalid_git_sha_fails(self):
        packet = _valid_packet()
        packet["git_sha"] = "not-a-valid-sha!!!"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_candidate_count_mismatch_fails_minimum(self):
        packet = _valid_packet()
        packet["candidate_count"] = 0
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_empty_candidates_fails(self):
        packet = _valid_packet()
        packet["candidates"] = []
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_limitations_empty_fails(self):
        packet = _valid_packet()
        packet["limitations"] = []
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_no_known_toxicity_claim_false_fails(self):
        packet = _valid_packet()
        packet["safety_attestations"]["no_known_toxicity_claim"] = False
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_example_packet_validates(self):
        import json
        example_path = _EXAMPLES_DIR / "external_review_packet_example.json"
        example = json.loads(example_path.read_text(encoding="utf-8"))
        validate_json_schema(example, EXTERNAL_REVIEW_SCHEMA)

    def test_proof_ladder_level_maximum_enforced(self):
        packet = _valid_packet()
        packet["proof_ladder_level"] = 9
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)

    def test_calibration_assessment_enum_enforced(self):
        packet = _valid_packet()
        packet["calibration_summary"]["calibration_assessment"] = "excellent"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_SCHEMA)
