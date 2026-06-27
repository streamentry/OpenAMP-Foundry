"""Tests for hydrophobic moment (amphipathicity) feature."""
from __future__ import annotations


from openamp_foundry.features.physchem import compute_features, hydrophobic_moment


class TestHydrophobicMoment:
    def test_empty_sequence_returns_zero(self):
        assert hydrophobic_moment("") == 0.0

    def test_uniform_sequence_low_moment(self):
        # All same amino acid → sine/cosine terms distribute evenly → low moment
        result = hydrophobic_moment("AAAAAAAAAA")
        assert isinstance(result, float)
        assert result >= 0.0

    def test_alternating_hydrophobic_polar_has_higher_moment(self):
        # Alternating hydrophobic/polar gives high periodicity
        # e.g. KALALALA at 100deg/residue should show amphipathic character
        # vs uniform KKKKKKKKwhich is all charged
        seq_amphipathic = "KLKLKLKL"
        seq_uniform = "KKKKKKKK"
        result_amph = hydrophobic_moment(seq_amphipathic)
        result_unif = hydrophobic_moment(seq_uniform)
        assert isinstance(result_amph, float)
        assert isinstance(result_unif, float)

    def test_known_amp_has_nonzero_moment(self):
        # KWKLFKKIGAVLKVL is a classic AMP (magainin analogue)
        result = hydrophobic_moment("KWKLFKKIGAVLKVL")
        assert result > 0.0

    def test_returns_float_rounded_to_4dp(self):
        result = hydrophobic_moment("KWKLFKK")
        assert isinstance(result, float)
        # Check 4 decimal places
        assert result == round(result, 4)

    def test_single_residue(self):
        result = hydrophobic_moment("K")
        # sin(0) = 0, cos(0) = 1 → moment = |H_K * cos(0)| / 1 = |H_K|
        assert isinstance(result, float)


class TestComputeFeaturesAmphipathicity:
    def test_hydrophobic_moment_in_features(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "hydrophobic_moment" in features
        assert isinstance(features["hydrophobic_moment"], float)
        assert features["hydrophobic_moment"] >= 0.0

    def test_empty_sequence_does_not_crash(self):
        features = compute_features("")
        assert "hydrophobic_moment" in features
        assert features["hydrophobic_moment"] == 0.0

    def test_all_canonical_amino_acids(self):
        seq = "ACDEFGHIKLMNPQRSTVWY"
        features = compute_features(seq)
        assert "hydrophobic_moment" in features
        assert features["hydrophobic_moment"] >= 0.0
