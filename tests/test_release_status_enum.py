"""Test release status enum values against registries."""
from pathlib import Path
import json


def test_exit_code_registry_has_expected_codes():
    registry = json.loads(Path("configs/exit_code_registry.json").read_text())
    codes = registry.get("codes", {})
    for code_str in ["0", "1", "2", "3"]:
        assert code_str in codes, f"Missing exit code {code_str}"
        assert "meaning" in codes[code_str]


def test_exit_code_meanings_are_consistent():
    registry = json.loads(Path("configs/exit_code_registry.json").read_text())
    codes = registry.get("codes", {})
    meanings = {v["meaning"] for v in codes.values()}
    assert len(meanings) == len(codes), "Duplicate meanings found"


def test_decision_log_enum_values():
    schema = json.loads(Path("schemas/decision_log.schema.json").read_text())
    decision_types = schema["properties"]["decision_type"]["enum"]
    for dt in ["approved", "rejected", "deferred"]:
        assert dt in schema["properties"]["decision"]["enum"]
