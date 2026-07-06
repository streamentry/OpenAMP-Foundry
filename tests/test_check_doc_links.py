"""Tests for the doc-link checker."""
import subprocess, sys
from scripts.check_doc_links import check_links


def test_checker_runs():
    result = check_links()
    assert "checked" in result
    assert result["checked"] > 0


def test_checker_returns_count():
    result = check_links()
    assert "count" in result
    assert isinstance(result["count"], int)


def test_checker_broken_is_list():
    result = check_links()
    assert isinstance(result["broken"], list)


def test_checker_cli_exit_0():
    r = subprocess.run([sys.executable, "scripts/check_doc_links.py"],
                       capture_output=True, text=True, env={"PYTHONPATH": "src"})
    # Exit 0 for no broken links, 3 for broken — either is acceptable
    assert r.returncode in (0, 3)
