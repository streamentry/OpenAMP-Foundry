"""Tests for quickstart guide."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/getting-started/QUICKSTART.md").exists()


def test_has_demo_command():
    text = Path("docs/getting-started/QUICKSTART.md").read_text()
    assert "make demo" in text


def test_has_setup_instructions():
    text = Path("docs/getting-started/QUICKSTART.md").read_text()
    assert "pip install" in text
    assert "git clone" in text


def test_has_next_steps():
    text = Path("docs/getting-started/QUICKSTART.md").read_text()
    assert "Next Steps" in text
