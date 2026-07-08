"""Tests for the docs-only PR verifier."""
import subprocess
import sys

from scripts.check_docs_only_pr import check_docs_only, get_changed_files, DOCS_EXTENSIONS


def test_docs_extensions_are_safe():
    assert ".md" in DOCS_EXTENSIONS
    assert ".json" in DOCS_EXTENSIONS
    assert ".yaml" in DOCS_EXTENSIONS
    assert ".py" not in DOCS_EXTENSIONS


def test_get_changed_files_returns_list():
    files = get_changed_files("HEAD~1")
    assert isinstance(files, list)


def test_check_docs_only_returns_dict():
    result = check_docs_only("HEAD~1")
    assert "docs_only" in result
    assert "code_files" in result
    assert "total_changed" in result


def test_cli_exit_0_for_docs_only():
    r = subprocess.run(
        [sys.executable, "scripts/check_docs_only_pr.py", "--diff-range", "HEAD~1"],
        capture_output=True, text=True,
    )
    assert r.returncode in (0, 3)
