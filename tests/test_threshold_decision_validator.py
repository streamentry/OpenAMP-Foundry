"""Test that threshold decisions are recorded and valid."""
import json
from pathlib import Path


def test_decision_log_schema_exists():
    assert Path("schemas/decision_log.schema.json").exists()


def test_decision_log_is_valid_json():
    schema = json.loads(Path("schemas/decision_log.schema.json").read_text())
    assert "required" in schema
    assert "properties" in schema


def test_decision_log_has_threshold_types():
    schema = json.loads(Path("schemas/decision_log.schema.json").read_text())
    decision_types = schema.get("properties", {}).get("decision_type", {}).get("enum", [])
    assert "recalibration_approval" in decision_types


def test_example_decision_passes_schema():
    from openamp_foundry.evidence.schemas import validate_json_schema
    example = {
        "entry_id": "DR-THRESHOLD-001",
        "date": "2026-07-08",
        "reviewer_name": "Test Reviewer",
        "decision_type": "recalibration_approval",
        "decision": "approved",
        "evidence_refs": ["test-evidence"],
        "reasoning_notes": "Threshold change approved for testing",
        "dissent_flag": False,
    }
    validate_json_schema(example, Path("schemas/decision_log.schema.json"))
