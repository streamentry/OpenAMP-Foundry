"""Tests for metric naming consistency checker."""
import json
import subprocess
import sys
from pathlib import Path
import pytest

from scripts.check_metric_naming import check_metric_name, load_registry


@pytest.fixture
def registry():
    return load_registry()


def test_known_canonical(registry):
    r = check_metric_name("auroc", registry)
    assert r["status"] == "canonical"


def test_known_alias(registry):
    r = check_metric_name("roc_auc", registry)
    assert r["status"] == "alias"
    assert r["canonical_name"] == "auroc"


def test_unknown_name(registry):
    r = check_metric_name("nonexistent_metric", registry)
    assert r["status"] == "unknown"


def test_cli_known(tmp_path):
    f = tmp_path / "test.json"
    f.write_text(json.dumps({"auroc": "ensemble"}))
    r = subprocess.run([sys.executable, "scripts/check_metric_naming.py", "--file", str(f)],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0


def test_registry_has_canonical_names(registry):
    assert "canonical_names" in registry
    assert len(registry["canonical_names"]) >= 5


def test_registry_has_aliases(registry):
    assert "aliases" in registry
    assert len(registry["aliases"]) >= 3


def test_aliases_resolve_to_canonical(registry):
    for alias, canonical in registry["aliases"].items():
        assert canonical in registry["canonical_names"], f"{alias} -> {canonical} not in canonical_names"
