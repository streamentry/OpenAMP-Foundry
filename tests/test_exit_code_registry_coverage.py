"""Test exit code registry is complete and accurate."""
import json
from pathlib import Path

REGISTRY = Path("configs/exit_code_registry.json")


def test_registry_exists():
    assert REGISTRY.exists()


def test_registry_is_valid_json():
    data = json.loads(REGISTRY.read_text())
    assert "codes" in data
    assert "command_patterns" in data


def test_recent_commands_are_registered():
    """Key commands added in recent loops should be in the registry."""
    data = json.loads(REGISTRY.read_text())
    registered = set(data["command_patterns"].keys())
    for cmd in ["validate-cert-quality", "rank", "validate"]:
        assert cmd in registered or any(k.startswith(cmd) for k in registered), f"{cmd} not in registry"
