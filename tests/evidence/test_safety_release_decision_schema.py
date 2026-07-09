"""Tests for safety_release_decision.schema.json."""
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.schemas import validate_json_schema

_SCHEMA_DIR = Path(__file__).parents[2] / "schemas"

SAFETY_RELEASE_SCHEMA = _SCHEMA_DIR / "safety_release_decision.schema.json"


def _valid_decision() -> dict:
    return {
        "decision_id": "SRD-2026-07-09-001",
        "packet_id": "ERP-2026-07-09-001",
        "decided_at": "2026-07-10T14:00:00Z",
        "decided_by": "Dr. Jane Smith, Safety Lead",
        "decision": "hold",
        "rationale": "Hemolysis assay results are pending for 3 high-charge candidates. Decision deferred until complete data is available.",
        "safety_checks_passed": {
            "toxicity_screened": True,
            "hemolysis_screened": True,
            "dual_use_reviewed": True,
        },
        "novelty_confirmed": True,
        "dry_lab_only_acknowledged": True,
        "next_steps": "Request updated hemolysis data and reconvene review panel within 2 weeks.",
    }


class TestSafetyReleaseDecisionSchema:
    def test_schema_file_exists(self):
        assert SAFETY_RELEASE_SCHEMA.exists()

    def test_valid_decision_passes(self):
        validate_json_schema(_valid_decision(), SAFETY_RELEASE_SCHEMA)

    def test_missing_required_field_fails(self):
        d = {"decision_id": "SRD-001"}
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_agent_authored_true_fails(self):
        d = _valid_decision()
        d["agent_authored"] = True
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_agent_authored_absent_passes(self):
        d = _valid_decision()
        validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_agent_authored_false_passes(self):
        d = _valid_decision()
        d["agent_authored"] = False
        validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_dry_lab_only_acknowledged_false_fails(self):
        d = _valid_decision()
        d["dry_lab_only_acknowledged"] = False
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_dry_lab_only_acknowledged_missing_fails(self):
        d = _valid_decision()
        del d["dry_lab_only_acknowledged"]
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_invalid_decision_enum_fails(self):
        d = _valid_decision()
        d["decision"] = "maybe"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_release_decision_passes(self):
        d = _valid_decision()
        d["decision"] = "release"
        validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_reject_decision_passes(self):
        d = _valid_decision()
        d["decision"] = "reject"
        validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_too_short_rationale_fails(self):
        d = _valid_decision()
        d["rationale"] = "Looks fine."
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_missing_safety_checks_fails(self):
        d = _valid_decision()
        del d["safety_checks_passed"]
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_incomplete_safety_checks_fails(self):
        d = _valid_decision()
        d["safety_checks_passed"] = {"toxicity_screened": True}
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_safety_check_field_wrong_type_fails(self):
        d = _valid_decision()
        d["safety_checks_passed"]["hemolysis_screened"] = "yes"
        with pytest.raises(jsonschema.ValidationError):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_dissent_optional(self):
        d = _valid_decision()
        d["dissent"] = "Reviewer B expressed concern about false discovery rate."
        validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_decided_by_agent_name_fails(self):
        d = _valid_decision()
        d["decided_by"] = "AI Agent v2.0"
        with pytest.raises(jsonschema.ValidationError, match="does not match"):
            validate_json_schema(d, SAFETY_RELEASE_SCHEMA)

    def test_maximal_release_passes(self):
        d = {
            "decision_id": "SRD-2026-07-09-002",
            "packet_id": "ERP-2026-07-09-002",
            "decided_at": "2026-07-11T09:30:00Z",
            "decided_by": "Dr. Alan Turing, External Review Board",
            "decision": "release",
            "rationale": "All safety checks passed. Candidates are dry-lab nominations with no biological claim. External review board approved release under standard terms.",
            "safety_checks_passed": {
                "toxicity_screened": True,
                "hemolysis_screened": True,
                "dual_use_reviewed": True,
            },
            "novelty_confirmed": True,
            "dry_lab_only_acknowledged": True,
            "next_steps": "Prepare release summary and distribute to partner labs.",
            "agent_authored": False,
        }
        validate_json_schema(d, SAFETY_RELEASE_SCHEMA)
