"""Tests for artifact map."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/evidence/ARTIFACT_MAP.md").exists()


def test_has_inputs():
    text = Path("docs/evidence/ARTIFACT_MAP.md").read_text()
    assert "Inputs" in text


def test_has_benchmark():
    text = Path("docs/evidence/ARTIFACT_MAP.md").read_text()
    assert "Benchmark Outputs" in text


def test_has_lab():
    text = Path("docs/evidence/ARTIFACT_MAP.md").read_text()
    assert "Lab and Review" in text


def test_has_release():
    text = Path("docs/evidence/ARTIFACT_MAP.md").read_text()
    assert "Release Artifacts" in text
