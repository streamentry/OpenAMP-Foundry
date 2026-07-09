"""Verify all config YAML files are valid YAML and parseable."""
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

import pytest

CONFIG_DIR = Path("configs")


def test_all_configs_are_valid_yaml():
    if yaml is None:
        pytest.skip("PyYAML not installed")
    for f in sorted(CONFIG_DIR.glob("*.yaml")):
        data = yaml.safe_load(f.read_text())
        assert data is not None, f"{f.name}: empty YAML"
        assert isinstance(data, dict), f"{f.name}: not a mapping"


def test_pipeline_yaml_has_required_keys():
    if yaml is None:
        pytest.skip("PyYAML not installed")
    data = yaml.safe_load((CONFIG_DIR / "pipeline.yaml").read_text())
    for key in ["weights", "filters", "selection"]:
        assert key in data, f"Missing required key: {key}"


def test_phase3_yaml_differs_from_pipeline():
    if yaml is None:
        pytest.skip("PyYAML not installed")
    pipe = yaml.safe_load((CONFIG_DIR / "pipeline.yaml").read_text())
    phase3 = yaml.safe_load((CONFIG_DIR / "phase3.yaml").read_text())
    assert pipe != phase3, "pipeline.yaml and phase3.yaml should differ"
