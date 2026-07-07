"""Tests for pyproject consistency checker."""
import subprocess
import sys
import tomllib
from pathlib import Path
import pytest

from scripts.check_pyproject import check_pyproject


def test_check_runs():
    r = check_pyproject()
    assert "project_name" in r
    assert r["project_name"]


def test_python_requirement_present():
    r = check_pyproject()
    assert r["python_requirement"] != ""


def test_entrypoints_defined():
    r = check_pyproject()
    assert r["entrypoints"] > 0


def test_extras_defined():
    r = check_pyproject()
    assert r["extras"] >= 1


def test_cli_exit():
    r = subprocess.run([sys.executable, "scripts/check_pyproject.py"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    assert r.returncode == 0


def test_pyproject_is_valid_toml():
    data = tomllib.loads(Path("pyproject.toml").read_text())
    assert "project" in data
    assert data["project"]["name"] == "openamp-foundry"


def test_missing_file():
    r = check_pyproject("/nonexistent.toml")
    assert "error" in r
