"""Tests for synthetic data policy doc."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/evidence/SYNTHETIC_DATA_POLICY.md").exists()


def test_has_definitions():
    text = Path("docs/evidence/SYNTHETIC_DATA_POLICY.md").read_text()
    assert "Toy fixture" in text
    assert "Synthetic data" in text
    assert "Real data" in text


def test_has_allowed_use():
    text = Path("docs/evidence/SYNTHETIC_DATA_POLICY.md").read_text()
    assert "Allowed Use" in text


def test_has_forbidden_use():
    text = Path("docs/evidence/SYNTHETIC_DATA_POLICY.md").read_text()
    assert "Forbidden Use" in text


def test_disclaimer_required():
    text = Path("docs/evidence/SYNTHETIC_DATA_POLICY.md").read_text()
    assert "SYNTHETIC" in text
    assert "disclaimer" in text
