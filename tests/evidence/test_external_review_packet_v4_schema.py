"""Tests for the canonical V4 external-review packet schema."""

from dataclasses import asdict
from pathlib import Path

import jsonschema
import pytest

from openamp_foundry.evidence.external_review_packet import build_external_review_packet
from openamp_foundry.evidence.schemas import validate_json_schema


SCHEMA = Path(__file__).parents[2] / "schemas" / "external_review_packet_v4.schema.json"


def _packet(**kwargs):
    defaults = {
        "erp_id": "ERP-001",
        "batch_id": "BATCH-001",
        "pipeline_version": "v0.10.3",
        "brc_artifact_id": "BRC-001",
        "eci_artifact_id": "ECI-001",
        "fet_artifact_id": "FET-001",
        "ptr_artifact_id": "PTR-001",
        "srs_artifact_id": "SRS-001",
        "limitations": ["dry-lab only"],
        "created_at": "2026-08-10T00:00:00Z",
    }
    defaults.update(kwargs)
    return asdict(build_external_review_packet(**defaults))


def test_v4_schema_exists():
    assert SCHEMA.exists()


def test_ready_v4_packet_passes_schema():
    validate_json_schema(_packet(), SCHEMA)


def test_draft_v4_packet_passes_schema():
    validate_json_schema(
        _packet(
            brc_artifact_id="",
            eci_artifact_id="",
            fet_artifact_id="",
            ptr_artifact_id="",
            srs_artifact_id="",
        ),
        SCHEMA,
    )


def test_schema_rejects_cross_typed_artifact_reference():
    packet = _packet()
    brc = next(component for component in packet["components"] if component["component_type"] == "BRC")
    brc["artifact_id"] = "ECI-001"
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(packet, SCHEMA)


def test_schema_rejects_prefix_only_artifact_reference():
    packet = _packet()
    brc = next(component for component in packet["components"] if component["component_type"] == "BRC")
    brc["artifact_id"] = "BRC-"
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(packet, SCHEMA)


def test_schema_rejects_artifact_reference_marked_absent():
    packet = _packet()
    brc = next(component for component in packet["components"] if component["component_type"] == "BRC")
    brc["present"] = False
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(packet, SCHEMA)


def test_schema_rejects_missing_component_type():
    packet = _packet()
    packet["components"] = packet["components"][:-1]
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(packet, SCHEMA)


def test_schema_rejects_unknown_top_level_field():
    packet = _packet()
    packet["reviewer_email"] = "reviewer@example.com"
    with pytest.raises(jsonschema.ValidationError):
        validate_json_schema(packet, SCHEMA)
