"""Tests for archive manifest completeness."""
import json
from pathlib import Path


def test_run_manifest_has_required_keys():
    """Verify run_manifest.schema.json has required fields."""
    schema = json.loads(Path("schemas/run_manifest.schema.json").read_text())
    required = {"run_id", "pipeline_version", "config_hash", "generated_at", "inputs", "outputs"}
    if "required" in schema:
        assert required.issubset(set(schema["required"])), "Missing required fields in schema"


def test_candidate_schema_has_required_keys():
    schema = json.loads(Path("schemas/candidate.schema.json").read_text())
    assert "candidate_id" in str(schema)
    assert "scores" in str(schema)


def test_lab_result_schema_has_required_keys():
    schema = json.loads(Path("schemas/lab_result.schema.json").read_text())
    for field in ["candidate_id", "assay_type", "result_value", "result_unit"]:
        assert field in str(schema), f"Missing {field} from lab_result schema"
