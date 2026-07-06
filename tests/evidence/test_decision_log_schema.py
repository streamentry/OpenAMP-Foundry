"""Tests for the decision-log JSON Schema."""

import json
from pathlib import Path

import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

SCHEMA_DIR = Path("schemas")
DECISION_LOG_DIR = Path("decision_logs")


def _load_schema() -> dict:
    path = SCHEMA_DIR / "decision_log.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_file_exists():
    assert (SCHEMA_DIR / "decision_log.schema.json").exists()


def test_schema_is_valid_json_schema():
    schema = _load_schema()
    assert schema["$schema"].startswith("https://json-schema.org/")
    assert schema["title"] == "OpenAMP Human Review Decision Log"


def test_schema_required_fields():
    schema = _load_schema()
    for field in ["entry_id", "date", "reviewer_name", "decision_type",
                  "decision", "evidence_refs", "reasoning_notes"]:
        assert field in schema["required"], f"Missing required field: {field}"


def test_schema_decision_types():
    schema = _load_schema()
    valid_types = schema["properties"]["decision_type"]["enum"]
    for dt in ["publish_candidate_sequences", "contact_lab",
               "release_generator_weights", "change_safety_policy",
               "external_scientific_claim", "submit_paper_or_press_release",
               "recalibration_approval", "expert_review_override", "other"]:
        assert dt in valid_types, f"Missing decision type: {dt}"


def test_schema_decision_values():
    schema = _load_schema()
    valid_decisions = schema["properties"]["decision"]["enum"]
    for d in ["approved", "rejected", "deferred"]:
        assert d in valid_decisions


def test_valid_decision_passes_validation():
    example = {
        "entry_id": "DR-2026-07-06-001",
        "date": "2026-07-06",
        "reviewer_name": "Dr. Jane Smith",
        "reviewer_affiliation": "University of Example",
        "decision_type": "contact_lab",
        "decision": "approved",
        "evidence_refs": ["https://github.com/Open-Problem-Lab/OpenAMP-Foundry/pull/145"],
        "reasoning_notes": "Pipeline passes honesty benchmarks. Candidate panel is diverse.",
        "dissent_flag": False,
    }
    validate_json_schema(example, SCHEMA_DIR / "decision_log.schema.json")


def test_missing_required_field_fails():
    example = {
        "entry_id": "DR-001",
        "date": "2026-07-06",
        "reviewer_name": "Dr. Smith",
        # missing decision_type, decision, evidence_refs, reasoning_notes
    }
    with pytest.raises(Exception, match="required"):
        validate_json_schema(example, SCHEMA_DIR / "decision_log.schema.json")


def test_dissent_requires_notes():
    example = {
        "entry_id": "DR-002",
        "date": "2026-07-06",
        "reviewer_name": "Dr. Smith",
        "decision_type": "recalibration_approval",
        "decision": "rejected",
        "evidence_refs": [],
        "reasoning_notes": "Insufficient cohort size.",
        "dissent_flag": True,
        # missing dissent_notes — should fail
    }
    with pytest.raises(Exception, match="dissent_notes"):
        validate_json_schema(example, SCHEMA_DIR / "decision_log.schema.json")


def test_invalid_decision_type_fails():
    example = {
        "entry_id": "DR-003",
        "date": "2026-07-06",
        "reviewer_name": "Dr. Smith",
        "decision_type": "invalid_type",
        "decision": "approved",
        "evidence_refs": [],
        "reasoning_notes": "Test",
    }
    with pytest.raises(Exception):
        validate_json_schema(example, SCHEMA_DIR / "decision_log.schema.json")


def test_rejected_decision_valid():
    example = {
        "entry_id": "DR-004",
        "date": "2026-07-06",
        "reviewer_name": "Dr. Jones",
        "decision_type": "publish_candidate_sequences",
        "decision": "rejected",
        "evidence_refs": ["PR #150"],
        "reasoning_notes": "Novelty analysis incomplete.",
        "dissent_flag": True,
        "dissent_notes": "I believe novelty is sufficient.",
    }
    validate_json_schema(example, SCHEMA_DIR / "decision_log.schema.json")


def test_existing_decision_log_is_parsable():
    """The existing Markdown decision log is not JSON — this test verifies
    the file exists. Real decision logs should use the JSON format for
    machine readability."""
    log_files = list(DECISION_LOG_DIR.glob("*.md")) + list(DECISION_LOG_DIR.glob("*.json"))
    assert len(log_files) >= 1, "No decision log files found"
