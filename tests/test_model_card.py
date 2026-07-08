"""Tests for model cards in docs/trust/ directory."""
from pathlib import Path


def test_ensemble_scorer_card_exists():
    card = Path("docs/trust/ensemble_scorer_card.md")
    assert card.exists(), "Ensemble scorer model card required"
    text = card.read_text()
    assert "model_id" in text
    assert "Intended use" in text
    assert "Limitations" in text
