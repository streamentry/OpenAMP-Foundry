"""Tests for the docs index coverage checker."""
import subprocess
import sys

from scripts.check_docs_index_coverage import check_coverage, get_docs_files, get_indexed_docs


def test_get_indexed_docs_returns_set():
    result = get_indexed_docs()
    assert isinstance(result, set)
    assert len(result) > 10  # PROJECT_INDEX.md references many docs


def test_get_docs_files_returns_set():
    result = get_docs_files()
    assert isinstance(result, set)
    assert len(result) > 50


def test_check_coverage_returns_dict():
    result = check_coverage()
    assert "total_docs" in result
    assert "indexed" in result
    assert "missing" in result


def test_cli_runs():
    r = subprocess.run(
        [sys.executable, "scripts/check_docs_index_coverage.py", "--warn-only"],
        capture_output=True, text=True,
    )
    assert r.returncode in (0, 3)
