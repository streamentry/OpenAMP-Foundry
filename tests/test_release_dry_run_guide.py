"""Tests for release dry-run reading guide."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/review/RELEASE_DRY_RUN_GUIDE.md").exists()


def test_has_run_command():
    text = Path("docs/review/RELEASE_DRY_RUN_GUIDE.md").read_text()
    assert "make full-reproducibility-report" in text


def test_has_verdict_section():
    text = Path("docs/review/RELEASE_DRY_RUN_GUIDE.md").read_text()
    assert "Interpreting the Verdict" in text


def test_has_does_not_do():
    text = Path("docs/review/RELEASE_DRY_RUN_GUIDE.md").read_text()
    assert "does not publish" in text


def test_has_next_actions():
    text = Path("docs/review/RELEASE_DRY_RUN_GUIDE.md").read_text()
    assert "Next Actions" in text
