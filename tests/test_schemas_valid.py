"""Test all JSON Schema files are valid JSON and parseable."""  
import json
from pathlib import Path

import jsonschema

SCHEMA_DIR = Path("schemas")


def test_all_schemas_are_valid_json():
    for f in sorted(SCHEMA_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        assert "$schema" in data or "type" in data, f"{f.name}: not a valid schema"


def test_all_schemas_have_title():
    for f in sorted(SCHEMA_DIR.glob("*.json")):
        data = json.loads(f.read_text())
        assert "title" in data or "description" in data, f"{f.name}: missing title/description"


def test_schemas_directory_has_files():
    files = list(SCHEMA_DIR.glob("*.json"))
    assert len(files) >= 8, f"Expected at least 8 schemas, got {len(files)}"
