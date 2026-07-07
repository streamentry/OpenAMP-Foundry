"""Tests for limitations overview doc."""
from pathlib import Path


def test_file_exists():
    assert Path("docs/evidence/LIMITATIONS_OVERVIEW.md").exists()


def test_has_required_sections():
    text = Path("docs/evidence/LIMITATIONS_OVERVIEW.md").read_text()
    for section in ["Model Limitations", "Data Limitations", "Benchmark Limitations",
                    "Calibration Limitations", "Safety and Review Limitations",
                    "Reproducibility Limitations"]:
        assert section in text, f"Missing section: {section}"


def test_does_not_overclaim():
    text = Path("docs/evidence/LIMITATIONS_OVERVIEW.md").read_text()
    assert "proven" not in text.lower()
    assert "No antimicrobial activity has been demonstrated" in text


def test_links_to_related_docs():
    text = Path("docs/evidence/LIMITATIONS_OVERVIEW.md").read_text()
    assert "METRICS_CURRENT.md" in text
    assert "RISK_REGISTER.md" in text
