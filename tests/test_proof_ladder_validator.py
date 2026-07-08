"""Test proof ladder field validation in artifacts."""
from pathlib import Path


def test_evidence_certificate_has_proof_fields():
    """Evidence certificates should contain fields relevant to proof level."""
    import json
    schema = json.loads(Path("schemas/candidate.schema.json").read_text())
    props = str(schema.get("properties", {}))
    assert "scores" in props, "Missing scores in evidence schema"
    assert "candidate" in props or "candidate_id" in props


def test_lab_result_has_proof_fields():
    import json
    schema = json.loads(Path("schemas/lab_result.schema.json").read_text())
    required = schema.get("required", [])
    for field in ["candidate_id", "assay_type", "result_value"]:
        assert field in required


def test_pipeline_version_tracked():
    """Pipeline version should be tracked in key artifacts."""
    import json
    for schema_name in ["candidate.schema.json", "run_manifest.schema.json"]:
        schema = json.loads(Path(f"schemas/{schema_name}").read_text())
        assert "version" in str(schema) or "pipeline" in str(schema).lower()
