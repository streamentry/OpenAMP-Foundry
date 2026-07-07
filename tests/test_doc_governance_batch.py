"""Tests for doc governance docs batch."""
from pathlib import Path

FILES = [
    "DOCS_URGENT_CORRECTION_POLICY.md",
    "DOCS_GOVERNANCE_FAQ.md",
    "DOCS_OPS_MANUAL_INDEX.md",
    "DOCS_DECISION_RECORD_POLICY.md",
    "DOCS_ROLE_DEFINITIONS.md",
]


def test_all_exist():
    for f in FILES:
        assert Path(f"docs/evidence/{f}").exists(), f"Missing: {f}"


def test_each_has_content():
    for f in FILES:
        text = Path(f"docs/evidence/{f}").read_text()
        assert len(text) > 100, f"{f} too short"
