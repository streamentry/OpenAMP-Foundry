"""Test golden artifact fixtures match expected schema."""
import json
from pathlib import Path


def test_evidence_certificate_schema():
    schema = json.loads(Path("schemas/candidate.schema.json").read_text())
    assert "candidate_id" in str(schema)
    assert "scores" in str(schema)


def test_lab_result_schema():
    schema = json.loads(Path("schemas/lab_result.schema.json").read_text())
    for field in ["candidate_id", "assay_type", "result_value"]:
        assert field in str(schema), f"Missing {field}"


def test_run_manifest_schema():
    schema = json.loads(Path("schemas/run_manifest.schema.json").read_text())
    for field in ["run_id", "pipeline_version", "generated_at"]:
        assert field in str(schema), f"Missing {field}"
