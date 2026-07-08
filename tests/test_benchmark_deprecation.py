"""Tests for the benchmark deprecation system."""
from pathlib import Path

from scripts.check_benchmark_deprecation import scan_cards

CARDS_DIR = Path("configs/benchmark_cards")


def test_cards_directory_exists():
    assert CARDS_DIR.exists(), "configs/benchmark_cards/ must exist"


def test_cards_are_yaml():
    files = list(CARDS_DIR.glob("*.yaml"))
    assert len(files) > 0, "Expected at least one benchmark card"
    for f in files:
        text = f.read_text()
        assert "name:" in text
        assert "target:" in text


def test_deprecated_benchmarks_have_superseded_by():
    """Deprecated benchmarks must specify what superseded them."""
    deprecated = scan_cards()
    for d in deprecated:
        assert d["superseded_by"], (
            f"Deprecated benchmark '{d['name']}' must specify superseded_by"
        )


def test_deprecated_benchmarks_have_note():
    """Deprecated benchmarks should explain why they were deprecated."""
    deprecated = scan_cards()
    for d in deprecated:
        assert d["deprecation_note"], (
            f"Deprecated benchmark '{d['name']}' must have a deprecation_note"
        )


def test_scan_returns_list():
    result = scan_cards()
    assert isinstance(result, list)


def test_scan_non_existent_dir():
    result = scan_cards("/nonexistent/path")
    assert result == []


def test_cli_reports_deprecated():
    import subprocess, sys
    r = subprocess.run(
        [sys.executable, "scripts/check_benchmark_deprecation.py"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0
    assert "Deprecated benchmarks" in r.stdout


def test_cli_fail_on_deprecated_exits_3():
    import subprocess, sys
    r = subprocess.run(
        [sys.executable, "scripts/check_benchmark_deprecation.py",
         "--fail-on-deprecated"],
        capture_output=True, text=True,
    )
    assert r.returncode == 3
