"""Regression tests for the repo-root import shim."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_PACKAGE = REPO_ROOT / "src" / "openamp_foundry"


def test_root_import_shim_includes_src_package_once():
    import openamp_foundry

    path_entries = list(openamp_foundry.__path__)
    assert str(SRC_PACKAGE) in path_entries
    assert path_entries.count(str(SRC_PACKAGE)) == 1


def test_repo_root_python_m_cli_still_works():
    result = subprocess.run(
        [sys.executable, "-m", "openamp_foundry.cli", "--help"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
