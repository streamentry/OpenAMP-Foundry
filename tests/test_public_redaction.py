"""Test public artifact redaction policy."""
import json
from pathlib import Path


def test_redaction_policy_exists():
    assert Path("docs/evidence/GUIDE_REDACTION_POLICY.md").exists()


def test_synthetic_data_policy_exists():
    assert Path("docs/evidence/SYNTHETIC_DATA_POLICY.md").exists()


def test_lab_result_schema_has_disclaimer():
    schema = json.loads(Path("schemas/lab_result.schema.json").read_text())
    props = schema.get("properties", {})
    assert "disclaimer" in props, "Lab result schema should have disclaimer field"
