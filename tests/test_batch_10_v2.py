"""Tests for batch of 10 docs."""
from pathlib import Path

FILES = [
    "MIGRATION_GUIDE_README_TO_DOCS.md",
    "MIGRATION_GUIDE_SCHEMA_DOCS.md",
    "MIGRATION_GUIDE_BENCHMARK_DOCS.md",
    "MIGRATION_GUIDE_ARTIFACT_DOCS.md",
    "MIGRATION_GUIDE_TUTORIAL_DOCS.md",
    "MIGRATION_GUIDE_DEPRECATED_DOCS.md",
    "CONCEPT_CARD_CALIBRATION_GATE.md",
    "CONCEPT_CARD_REVIEW_PACKET.md",
    "CONCEPT_CARD_REDACTION.md",
    "CONCEPT_CARD_OFFLINE_MODE.md",
]


def test_all_exist():
    for f in FILES:
        assert Path(f"docs/evidence/{f}").exists(), f"Missing: {f}"


def test_each_has_content():
    for f in FILES:
        text = Path(f"docs/evidence/{f}").read_text()
        assert len(text) > 50, f"{f} too short"
