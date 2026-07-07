"""Tests for the claim-language scanner."""

import subprocess
import sys
import tempfile
from pathlib import Path

from scripts.safety.check_claims import scan_file, scan_docs


def _write_tmp(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_clean_text_no_findings(tmp_path):
    f = _write_tmp(tmp_path / "clean.md", "This is a computationally nominated candidate.")
    result = scan_file(f)
    assert len(result) == 0


def test_risky_text_flagged(tmp_path):
    f = _write_tmp(tmp_path / "risky.md", "This is a drug candidate.")
    result = scan_file(f)
    assert len(result) >= 1


def test_multiple_patterns(tmp_path):
    f = _write_tmp(tmp_path / "bad.md", "proven antimicrobial\ndrug candidate")
    result = scan_file(f)
    assert len(result) >= 2


def test_scanner_runs_on_docs():
    result = scan_docs(docs_dir="docs")
    assert result["files_scanned"] > 0
    assert "total_findings" in result


def test_allowlist_excludes(tmp_path):
    f = _write_tmp(tmp_path / "AGENTS.md", "proven antimicrobial")
    result = scan_docs(docs_dir=str(tmp_path))
    assert result["total_findings"] == 0


def test_cli_runs():
    r = subprocess.run(
        [sys.executable, "scripts/safety/check_claims.py", "--path", "docs"],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src"},
    )
    assert r.returncode == 0
