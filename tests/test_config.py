"""Tests for config.py — load_config loading and error handling."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from openamp_foundry.config import load_config


class TestLoadConfig:
    def _write_config(self, content: str, path: Path) -> None:
        path.write_text(content, encoding="utf-8")

    def test_loads_valid_yaml(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "config.yaml"
            self._write_config("key: value\nnested:\n  a: 1\n", cfg_path)
            result = load_config(cfg_path)
        assert result["key"] == "value"
        assert result["nested"]["a"] == 1

    def test_loads_default_pipeline_config(self):
        default = Path(__file__).parents[1] / "configs" / "pipeline.yaml"
        result = load_config(default)
        assert "filters" in result
        assert "weights" in result
        assert "selection" in result

    def test_default_config_weights_are_positive(self):
        default = Path(__file__).parents[1] / "configs" / "pipeline.yaml"
        result = load_config(default)
        for name, w in result["weights"].items():
            assert w > 0, f"Weight '{name}' must be positive, got {w}"

    def test_default_config_filters_present(self):
        default = Path(__file__).parents[1] / "configs" / "pipeline.yaml"
        result = load_config(default)
        filters = result["filters"]
        assert "min_length" in filters
        assert "max_length" in filters
        assert filters["min_length"] < filters["max_length"]

    def test_default_config_selection_present(self):
        default = Path(__file__).parents[1] / "configs" / "pipeline.yaml"
        result = load_config(default)
        sel = result["selection"]
        assert "top_n" in sel
        assert "min_novelty" in sel
        assert "max_safety_risk" in sel
        assert 0.0 < sel["max_safety_risk"] <= 1.0
        assert "max_disagreement" in sel
        assert 0.0 <= sel["max_disagreement"] <= 1.0

    def test_phase3_config_selection_present(self):
        phase3 = Path(__file__).parents[1] / "configs" / "phase3.yaml"
        result = load_config(phase3)
        sel = result["selection"]
        assert "top_n" in sel
        assert "min_novelty" in sel
        assert "max_safety_risk" in sel
        assert 0.0 < sel["max_safety_risk"] <= 1.0
        assert "max_disagreement" in sel
        assert 0.0 <= sel["max_disagreement"] <= 1.0

    def test_phase3_config_weights_are_positive(self):
        phase3 = Path(__file__).parents[1] / "configs" / "phase3.yaml"
        result = load_config(phase3)
        for name, w in result["weights"].items():
            assert w > 0, f"phase3.yaml weight '{name}' must be positive, got {w}"

    def test_phase3_config_filters_present(self):
        phase3 = Path(__file__).parents[1] / "configs" / "phase3.yaml"
        result = load_config(phase3)
        filters = result["filters"]
        assert "min_length" in filters
        assert "max_length" in filters
        assert filters["min_length"] < filters["max_length"]

    def test_string_path_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "config.yaml"
            self._write_config("x: 42\n", cfg_path)
            result = load_config(str(cfg_path))
        assert result["x"] == 42

    def test_missing_file_raises(self):
        with pytest.raises((FileNotFoundError, OSError)):
            load_config("/nonexistent/path/config.yaml")

    def test_empty_yaml_raises(self):
        # yaml.safe_load("") returns None; load_config rejects this to protect
        # downstream callers that always expect a dict.
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "config.yaml"
            self._write_config("", cfg_path)
            with pytest.raises(ValueError, match="empty"):
                load_config(cfg_path)

    def test_list_yaml_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "config.yaml"
            self._write_config("items:\n  - a\n  - b\n", cfg_path)
            result = load_config(cfg_path)
        assert result["items"] == ["a", "b"]

    def test_numeric_values_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "config.yaml"
            self._write_config("threshold: 0.75\ncount: 42\n", cfg_path)
            result = load_config(cfg_path)
        assert abs(result["threshold"] - 0.75) < 1e-9
        assert result["count"] == 42

    def test_bool_values_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "config.yaml"
            self._write_config("enabled: true\ndisabled: false\n", cfg_path)
            result = load_config(cfg_path)
        assert result["enabled"] is True
        assert result["disabled"] is False

    def test_malformed_yaml_raises(self):
        import yaml as _yaml
        with tempfile.TemporaryDirectory() as d:
            cfg_path = Path(d) / "bad.yaml"
            self._write_config("key: [unclosed\n", cfg_path)
            with pytest.raises(_yaml.YAMLError):
                load_config(cfg_path)
