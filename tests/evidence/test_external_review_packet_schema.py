"""Tests for external_review_packet.schema.json."""
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

_SCHEMA_DIR = Path(__file__).parents[2] / "schemas"
_EXAMPLES_DIR = Path(__file__).parents[2] / "examples"

EXTERNAL_REVIEW_SCHEMA = _SCHEMA_DIR / "external_review_packet.schema.json"
EXTERNAL_REVIEW_V4_SCHEMA = _SCHEMA_DIR / "external_review_packet_v4.schema.json"


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


def _valid_v4_packet() -> dict:
    components = [
        {"component_type": "BRC", "artifact_id": "BRC-001", "present": True},
        {"component_type": "ECI", "artifact_id": "ECI-001", "present": True},
        {"component_type": "FET", "artifact_id": "FET-001", "present": True},
        {"component_type": "PTR", "artifact_id": "PTR-001", "present": True},
        {"component_type": "SRS", "artifact_id": "SRS-001", "present": True},
    ]
    return {
        "erp_id": "ERP-2026-08-12-001",
        "batch_id": "BATCH-001",
        "pipeline_version": "v0.10.3",
        "components": components,
        "n_components_required": 5,
        "n_components_present": 5,
        "missing_component_types": [],
        "packet_status": "ready",
        "dry_lab_only": True,
        "limitations": ["Component presence does not authenticate artifacts or science."],
        "created_at": "2026-08-12T00:00:00Z",
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


class TestExternalReviewPacketV4Schema:
    def test_valid_v4_packet_passes(self):
        validate_json_schema(_valid_v4_packet(), EXTERNAL_REVIEW_V4_SCHEMA)

    def test_component_count_mismatch_fails_portable_schema(self):
        packet = _valid_v4_packet()
        packet["n_components_present"] = 0
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_V4_SCHEMA)

    def test_missing_component_list_mismatch_fails_portable_schema(self):
        packet = _valid_v4_packet()
        packet["components"][0]["present"] = False
        packet["components"][0]["artifact_id"] = ""
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_V4_SCHEMA)

    def test_packet_status_mismatch_fails_portable_schema(self):
        packet = _valid_v4_packet()
        packet["packet_status"] = "incomplete"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(packet, EXTERNAL_REVIEW_V4_SCHEMA)
