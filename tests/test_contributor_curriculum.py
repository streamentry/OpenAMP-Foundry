"""Tests for contributor curriculum."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/getting-started/CONTRIBUTOR_CURRICULUM.md").exists()


def test_has_stages():
    text = Path("docs/getting-started/CONTRIBUTOR_CURRICULUM.md").read_text()
    for stage in ["Stage 1", "Stage 2", "Stage 3", "Stage 4"]:
        assert stage in text


def test_has_prerequisites():
    text = Path("docs/getting-started/CONTRIBUTOR_CURRICULUM.md").read_text()
    assert "Prerequisites" in text


def test_has_docs_only():
    text = Path("docs/getting-started/CONTRIBUTOR_CURRICULUM.md").read_text()
    assert "Docs-only" in text


def test_has_maintainer_discussion():
    text = Path("docs/getting-started/CONTRIBUTOR_CURRICULUM.md").read_text()
    assert "Maintainer Discussion" in text
