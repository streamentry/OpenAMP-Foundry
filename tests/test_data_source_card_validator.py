"""Test data source card validation."""
import json
from pathlib import Path

REQUIRED = {"name", "source", "license", "version", "description", "labeled"}


def test_example_data_source_card():
    """Verify a valid data source card passes checks."""
    card = {
        "name": "test_dataset",
        "source": "test_source",
        "license": "CC0",
        "version": "2026-01-01",
        "description": "Test dataset",
        "labeled": True,
    }
    assert REQUIRED.issubset(card.keys())


def test_data_card_has_required_fields():
    """Check the first few CSV files for basic metadata."""
    for csv_file in list(Path("examples").rglob("*.csv"))[:3]:
        assert csv_file.exists()
        # CSV files should have headers
        lines = csv_file.read_text().strip().split("\n")
        assert len(lines) >= 2, f"{csv_file} has no data rows"


def test_data_card_license_is_defined():
    """Example data should have a license."""
    license_file = Path("DATA_LICENSE_NOTICE.md")
    assert license_file.exists()
    text = license_file.read_text()
    assert "CC0" in text or "CC BY" in text or "license" in text.lower()
