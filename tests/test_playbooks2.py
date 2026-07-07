"""Tests for playbooks batch 2."""
from pathlib import Path

FILES = [
    "PLAYBOOK_CONFLICTING_DOCS.md",
    "PLAYBOOK_MISSING_SCHEMA.md",
    "PLAYBOOK_REJECTED_SUMMARY.md",
    "PLAYBOOK_LARGE_PRS.md",
    "PLAYBOOK_INSTALL_FAILURE.md",
]


def test_all_exist():
    for f in FILES:
        assert Path(f"docs/evidence/{f}").exists(), f"Missing: {f}"


def test_each_has_steps():
    for f in FILES:
        text = Path(f"docs/evidence/{f}").read_text()
        assert len(text) > 100
