"""Tests for 10 audit checklists."""
from pathlib import Path

FILES = [
    "AUDIT_CHECKLIST_ONBOARDING.md",
    "AUDIT_CHECKLIST_SAFETY_DOCS.md",
    "AUDIT_CHECKLIST_BENCHMARK_DOCS.md",
    "AUDIT_CHECKLIST_REVIEW_DOCS.md",
    "AUDIT_CHECKLIST_RELEASE_DOCS.md",
    "AUDIT_CHECKLIST_EXAMPLE_DOCS.md",
    "AUDIT_CHECKLIST_GLOSSARY_DOCS.md",
    "AUDIT_CHECKLIST_STALE_DOCS.md",
    "AUDIT_CHECKLIST_DEAD_ENDS.md",
    "AUDIT_CHECKLIST_CLAIM_WORDING.md",
]


def test_all_exist():
    for f in FILES:
        assert Path("docs/evidence", f).exists(), f"Missing: {f}"


def test_each_has_checklist():
    for f in FILES:
        text = Path("docs/evidence", f).read_text()
        assert "- [" in text, f"{f} missing checklist items"
