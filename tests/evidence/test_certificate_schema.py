from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.certificate import _infer_proof_ladder_level, build_certificate
from openamp_foundry.evidence.schemas import validate_json_schema
from openamp_foundry.features.physchem import compute_features
from openamp_foundry.types import PeptideCandidate, ScoredCandidate

_SCHEMA = Path(__file__).parents[2] / "schemas" / "candidate.schema.json"


def test_certificate_validates():
    candidate = PeptideCandidate("AMPF-TEST", "KWKLFKKIGAVLKVL", "test")
    scored = ScoredCandidate(
        candidate=candidate,
        features=compute_features(candidate.sequence),
        scores={"activity": 0.8, "safety": 0.9, "synthesis": 0.9, "novelty": 0.5, "ensemble": 0.8},
        selection_reason=["test"],
        known_failure_modes=["No wet-lab assay has been run."],
    )
    cert = build_certificate(scored, {"weights": {}}, [])
    validate_json_schema(cert, _SCHEMA)


class TestValidateJsonSchemaErrors:
    def test_invalid_payload_raises_validation_error(self, tmp_path):
        schema = tmp_path / "test.schema.json"
        schema.write_text(json.dumps({
            "type": "object",
            "required": ["candidate_id"],
            "properties": {"candidate_id": {"type": "string"}},
        }))
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema({"wrong_key": 123}, schema)

    def test_missing_required_field_raises(self, tmp_path):
        schema = tmp_path / "test.schema.json"
        schema.write_text(json.dumps({
            "type": "object",
            "required": ["candidate_id", "sequence"],
        }))
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema({"candidate_id": "X"}, schema)

    def test_wrong_type_raises_validation_error(self, tmp_path):
        schema = tmp_path / "test.schema.json"
        schema.write_text(json.dumps({
            "type": "object",
            "properties": {"score": {"type": "number"}},
        }))
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema({"score": "not-a-number"}, schema)

    def test_nonexistent_schema_raises(self):
        with pytest.raises((FileNotFoundError, OSError)):
            validate_json_schema({"x": 1}, "/nonexistent/schema.json")


class TestProofLadderLevel:
    def test_certificate_contains_proof_ladder_level(self):
        candidate = PeptideCandidate("AMPF-PROOF", "KWKLFKKIGAVLKVL", "test")
        scored = ScoredCandidate(
            candidate=candidate,
            features=compute_features(candidate.sequence),
            scores={"activity": 0.8, "safety": 0.9, "synthesis": 0.9, "novelty": 0.5, "ensemble": 0.8},
            selection_reason=["test"],
            known_failure_modes=["test"],
        )
        cert = build_certificate(scored, {"weights": {}}, [])
        assert "proof_ladder_level" in cert
        assert cert["proof_ladder_level"] == "multi_signal_candidate_evidence"

    def test_proof_ladder_level_schema_validates(self):
        candidate = PeptideCandidate("AMPF-SCHEMA", "KWKLFKKIGAVLKVL", "test")
        scored = ScoredCandidate(
            candidate=candidate,
            features=compute_features(candidate.sequence),
            scores={"activity": 0.8, "safety": 0.9, "synthesis": 0.9, "novelty": 0.5, "ensemble": 0.8},
            selection_reason=["test"],
            known_failure_modes=["test"],
        )
        cert = build_certificate(scored, {"weights": {}}, [])
        validate_json_schema(cert, _SCHEMA)

    def test_infer_downgrades_on_missing_signals(self):
        candidate = PeptideCandidate("AMPF-LOW", "AAAA", "test")
        scored = ScoredCandidate(
            candidate=candidate,
            features=compute_features(candidate.sequence),
            scores={"activity": 0.0, "safety": 0.0, "synthesis": 0.0, "novelty": 0.0, "ensemble": 0.0},
            selection_reason=["test"],
            known_failure_modes=["No activity signal"],
        )
        level = _infer_proof_ladder_level(scored)
        assert level == "baseline_triaged"
