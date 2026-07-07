"""Tests for docs readiness checklist."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/evidence/DOCS_READINESS_CHECKLIST.md").exists()


def test_has_link_health():
    text = Path("docs/evidence/DOCS_READINESS_CHECKLIST.md").read_text()
    assert "Link Health" in text


def test_has_claim_wording():
    text = Path("docs/evidence/DOCS_READINESS_CHECKLIST.md").read_text()
    assert "Claim Wording" in text


def test_has_blocker_vs_warning():
    text = Path("docs/evidence/DOCS_READINESS_CHECKLIST.md").read_text()
    assert "Blocker" in text and "Warning" in text


def test_has_quickstart():
    text = Path("docs/evidence/DOCS_READINESS_CHECKLIST.md").read_text()
    assert "Quickstart" in text
