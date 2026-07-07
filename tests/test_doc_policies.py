"""Tests for documentation policy docs."""
from pathlib import Path

POLICIES = [
    "DOCS_EXCEPTION_POLICY.md",
    "DOCS_ESCALATION_POLICY.md",
    "DOCS_REVIEW_CADENCE_POLICY.md",
    "DOCS_RETIREMENT_POLICY.md",
    "DOCS_MINOR_EDIT_POLICY.md",
]


def test_all_exist():
    for p in POLICIES:
        assert Path(f"docs/evidence/{p}").exists(), f"Missing: {p}"


def test_each_has_content():
    for p in POLICIES:
        text = Path(f"docs/evidence/{p}").read_text()
        assert len(text) > 100, f"{p} is too short"
