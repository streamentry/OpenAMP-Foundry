"""Test scorers handle edge-case sequences gracefully."""
import pytest

from openamp_foundry.features.physchem import compute_features
from openamp_foundry.scoring.activity import activity_likeness_score
from openamp_foundry.scoring.safety import safety_score
from openamp_foundry.scoring.synthesis import synthesis_feasibility_score


def test_empty_sequence_handled_gracefully():
    features = compute_features("")
    # compute_features may return empty dict for empty sequence
    if any(features.values()):
        act = activity_likeness_score(features)
        assert 0 <= act <= 1
    else:
        pytest.skip("compute_features returns empty for empty sequence")


def test_very_long_sequence_does_not_crash():
    seq = "K" * 200
    features = compute_features(seq)
    act = activity_likeness_score(features)
    safe = safety_score(features)
    assert 0 <= act <= 1
    assert 0 <= safe <= 1


def test_reasonable_sequence_synthesis():
    """Synthesis scorer requires valid features dict."""
    seq = "KWKLFKKIGAVLKVL"
    features = compute_features(seq)
    synth = synthesis_feasibility_score(features, valid_sequence=True)
    assert 0 <= synth <= 1


def test_single_amino_acid_returns_scores():
    for aa in "ACDEFGHIKLMNPQRSTVWY":
        features = compute_features(aa)
        act = activity_likeness_score(features)
        assert 0 <= act <= 1, f"Activity score out of range for '{aa}': {act}"


@pytest.mark.parametrize("seq", [
    "ACDEFGHIKLMNPQRSTVWY",
    "KKKKKKKKKK",
    "GGGGGGGGGG",
    "P" * 15,
    "CCCCCCCCCC",
])
def test_multiple_sequences_produce_valid_scores(seq):
    features = compute_features(seq)
    act = activity_likeness_score(features)
    safe = safety_score(features)
    synth = synthesis_feasibility_score(features, valid_sequence=True)
    assert 0 <= act <= 1, f"Activity out of range for '{seq[:10]}...': {act}"
    assert 0 <= safe <= 1, f"Safety out of range for '{seq[:10]}...': {safe}"
    assert 0 <= synth <= 1, f"Synthesis out of range for '{seq[:10]}...': {synth}"
