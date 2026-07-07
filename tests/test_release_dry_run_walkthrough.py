"""Tests for release dry-run walkthrough."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/review/RELEASE_DRY_RUN_WALKTHROUGH.md").exists()


def test_has_when_not_to_release():
    text = Path("docs/review/RELEASE_DRY_RUN_WALKTHROUGH.md").read_text()
    assert "When NOT to Release" in text


def test_has_read_only():
    text = Path("docs/review/RELEASE_DRY_RUN_WALKTHROUGH.md").read_text()
    assert "read-only" in text.lower()


def test_has_phase_section():
    text = Path("docs/review/RELEASE_DRY_RUN_WALKTHROUGH.md").read_text()
    assert "Phase Status" in text


def test_has_simulation_section():
    text = Path("docs/review/RELEASE_DRY_RUN_WALKTHROUGH.md").read_text()
    assert "Simulation Module" in text
