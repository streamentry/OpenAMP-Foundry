"""Test schema changelog consistency."""
import json
from pathlib import Path


def test_schema_files_exist():
    schema_dir = Path("schemas")
    schemas = list(schema_dir.glob("*.json"))
    assert len(schemas) >= 5, f"Only {len(schemas)} schemas found"


def test_schemas_are_valid_json():
    for f in Path("schemas").glob("*.json"):
        data = json.loads(f.read_text())
        assert "$schema" in data, f"{f.name} missing $schema"
        assert "type" in data, f"{f.name} missing type"


def test_schemas_have_titles():
    for f in Path("schemas").glob("*.json"):
        data = json.loads(f.read_text())
        assert "title" in data, f"{f.name} missing title"
