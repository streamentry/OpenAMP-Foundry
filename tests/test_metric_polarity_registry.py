"""Tests for metric polarity registry."""
import json
from pathlib import Path


def _registry():
    return json.loads(Path("configs/metric_polarity_registry.json").read_text())


def test_file_exists():
    assert Path("configs/metric_polarity_registry.json").exists()


def test_is_valid_json():
    data = _registry()
    assert "pipeline_metrics" in data
    assert "simulation_metrics" in data
    assert "safety_metrics" in data


def test_auroc_is_higher_better():
    data = _registry()
    assert data["pipeline_metrics"]["auroc"]["polarity"] == "higher_is_better"


def test_disagreement_is_lower_better():
    data = _registry()
    assert data["pipeline_metrics"]["disagreement"]["polarity"] == "lower_is_better"


def test_all_metrics_have_description():
    data = _registry()
    for category in data.values():
        if isinstance(category, dict):
            for name, info in category.items():
                assert "description" in info, f"{name} missing description"
                assert "polarity" in info, f"{name} missing polarity"


def test_polarity_values():
    data = _registry()
    valid = {"higher_is_better", "lower_is_better", "depends"}
    for category in data.values():
        if isinstance(category, dict):
            for name, info in category.items():
                assert info["polarity"] in valid, f"{name} has invalid polarity: {info['polarity']}"


def test_known_metric_count():
    data = _registry()
    total = sum(len(cat) for cat in data.values() if isinstance(cat, dict))
    assert total >= 10
