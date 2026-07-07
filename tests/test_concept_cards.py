"""Tests for concept cards."""
from pathlib import Path

CARDS = [
    "CONCEPT_CARD_PROOF_LADDER.md",
    "CONCEPT_CARD_ARTIFACT.md",
    "CONCEPT_CARD_SCHEMA.md",
    "CONCEPT_CARD_MANIFEST.md",
    "CONCEPT_CARD_BENCHMARK_CAVEAT.md",
]


def test_all_exist():
    for card in CARDS:
        assert Path(f"docs/evidence/{card}").exists(), f"Missing: {card}"


def test_each_has_related():
    for card in CARDS:
        text = Path(f"docs/evidence/{card}").read_text()
        assert "Related" in text, f"{card} missing Related section"


def test_none_overclaim():
    for card in CARDS:
        text = Path(f"docs/evidence/{card}").read_text()
        assert "proven" not in text.lower(), f"{card} contains 'proven'"
