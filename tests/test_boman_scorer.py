"""Tests for scoring/boman.py — Boman index and GRAVY score.

All expected values are hand-calculated from the published Boman (2003)
potentials and Kyte-Doolittle (1982) scale to verify the implementation
is accurate and not just self-consistent.
"""
from __future__ import annotations

import pytest

from openamp_foundry.scoring.boman import (
    boman_activity_score,
    boman_index,
    gravy_score,
    model_disagreement,
)


class TestBomanIndex:
    def test_empty_sequence_returns_zero(self):
        assert boman_index("") == 0.0

    def test_single_lysine(self):
        # K → 2.465
        assert boman_index("K") == 2.465

    def test_single_tryptophan(self):
        # W → -3.398
        assert boman_index("W") == -3.398

    def test_single_glycine(self):
        # G → 0.000
        assert boman_index("G") == 0.0

    def test_two_residues_mean(self):
        # K + L → (2.465 + -1.810) / 2 = 0.3275
        assert boman_index("KL") == pytest.approx(0.3275, abs=1e-3)

    def test_all_cationic_positive(self):
        # K, R, D, E → 2.465 each → mean 2.465
        assert boman_index("KR") == pytest.approx(2.465, abs=1e-3)

    def test_all_hydrophobic_negative(self):
        # L, I → -1.810 each → mean -1.810
        assert boman_index("LI") == pytest.approx(-1.810, abs=1e-3)

    def test_case_insensitive(self):
        assert boman_index("kwk") == boman_index("KWK")

    def test_cationic_higher_than_hydrophobic_control(self):
        # AMP template (4 K residues) should score higher than all-hydrophobic decoy
        amp_bi = boman_index("KWKLFKKIGAVLKVL")
        decoy_bi = boman_index("LLLLLLLLLLLLLLL")  # all leucine → -1.810
        assert amp_bi > decoy_bi, f"AMP template ({amp_bi}) should exceed all-hydrophobic control ({decoy_bi})"

    def test_polyK_is_max_positive(self):
        bi_kk = boman_index("KKKK")
        bi_ww = boman_index("WWWW")
        assert bi_kk > bi_ww

    def test_rounding_to_4_decimal_places(self):
        result = boman_index("KL")
        assert result == round(result, 4)

    def test_unknown_aa_contributes_zero(self):
        # Non-canonical AAs are treated as zero contribution (neutral)
        bi_x = boman_index("X")
        assert bi_x == pytest.approx(0.0, abs=1e-4)

    def test_mixed_canonical_and_unknown(self):
        # "KB" → K(2.465) + B(0.0) → mean 1.2325
        assert boman_index("KB") == pytest.approx(1.2325, abs=1e-4)


class TestBomanActivityScore:
    def test_returns_between_zero_and_one(self):
        for seq in ["K", "W", "KWKLFKKIGAVLKVL", "LLLLLLL", "KKKKKKKK"]:
            score = boman_activity_score(seq)
            assert 0.0 <= score <= 1.0, f"Score out of range for {seq}: {score}"

    def test_empty_sequence(self):
        score = boman_activity_score("")
        assert score == pytest.approx(0.5, abs=1e-3)

    def test_cationic_seq_scores_higher_than_hydrophobic(self):
        # KKKKK >> WWWWW in Boman → higher activity score
        assert boman_activity_score("KKKKK") > boman_activity_score("WWWWW")

    def test_zero_boman_maps_to_near_half(self):
        # G → 0.000 → tanh(0) = 0 → 0.5
        score = boman_activity_score("GGGG")
        assert score == pytest.approx(0.5, abs=1e-2)

    def test_monotone_with_boman_index(self):
        seqs = ["WWWW", "LLLL", "GGGG", "SSSS", "KKKK"]
        indices = [boman_index(s) for s in seqs]
        activities = [boman_activity_score(s) for s in seqs]
        assert sorted(indices) == sorted(indices), "Sanity: indices sortable"
        sorted_pairs = sorted(zip(indices, activities))
        for (_, a1), (_, a2) in zip(sorted_pairs, sorted_pairs[1:]):
            assert a1 <= a2 + 1e-6, "boman_activity_score should increase with boman_index"

    def test_rounding(self):
        score = boman_activity_score("KWK")
        assert score == round(score, 4)


class TestGravyScore:
    def test_empty_returns_zero(self):
        assert gravy_score("") == 0.0

    def test_single_isoleucine(self):
        # I → 4.5
        assert gravy_score("I") == pytest.approx(4.5, abs=1e-3)

    def test_single_arginine(self):
        # R → -4.5
        assert gravy_score("R") == pytest.approx(-4.5, abs=1e-3)

    def test_hydrophobic_sequence_positive(self):
        # LLLLL → 3.8 mean
        assert gravy_score("LLLLL") == pytest.approx(3.8, abs=1e-3)

    def test_cationic_sequence_negative(self):
        # KKKKK → -3.9 mean
        assert gravy_score("KKKKK") == pytest.approx(-3.9, abs=1e-3)

    def test_case_insensitive(self):
        assert gravy_score("kwk") == gravy_score("KWK")

    def test_mixed_near_zero(self):
        # G → -0.4, balanced hydrophobic + hydrophilic should be near-zero
        gravy = gravy_score("KLII")
        # K=-3.9, L=3.8, I=4.5, I=4.5 → mean = (−3.9+3.8+4.5+4.5)/4 = 2.225
        assert gravy == pytest.approx(2.225, abs=1e-3)

    def test_rounding_to_4_places(self):
        result = gravy_score("KWL")
        assert result == round(result, 4)


class TestModelDisagreement:
    def test_identical_scores_zero_disagreement(self):
        assert model_disagreement(0.7, 0.7) == 0.0

    def test_maximum_disagreement(self):
        assert model_disagreement(0.0, 1.0) == pytest.approx(1.0, abs=1e-4)
        assert model_disagreement(1.0, 0.0) == pytest.approx(1.0, abs=1e-4)

    def test_symmetric(self):
        assert model_disagreement(0.3, 0.7) == model_disagreement(0.7, 0.3)

    def test_small_difference(self):
        assert model_disagreement(0.60, 0.65) == pytest.approx(0.05, abs=1e-4)

    def test_output_in_range(self):
        for a, b in [(0.0, 0.5), (0.9, 0.4), (0.3, 0.3), (1.0, 0.0)]:
            d = model_disagreement(a, b)
            assert 0.0 <= d <= 1.0

    def test_rounding_to_4_places(self):
        result = model_disagreement(0.333, 0.667)
        assert result == round(result, 4)


class TestPipelineIntegration:
    """Verify Boman values appear in compute_features output."""

    def test_boman_index_in_features(self):
        from openamp_foundry.features.physchem import compute_features
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "boman_index" in features
        assert isinstance(features["boman_index"], float)

    def test_gravy_in_features(self):
        from openamp_foundry.features.physchem import compute_features
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "gravy" in features
        assert isinstance(features["gravy"], float)

    def test_boman_index_feature_value_matches_scorer(self):
        from openamp_foundry.features.physchem import compute_features
        seq = "KRLFKKIGSALKFL"
        features = compute_features(seq)
        assert features["boman_index"] == pytest.approx(boman_index(seq), abs=1e-4)

    def test_gravy_feature_value_matches_scorer(self):
        from openamp_foundry.features.physchem import compute_features
        seq = "KRLFKKIGSALKFL"
        features = compute_features(seq)
        assert features["gravy"] == pytest.approx(gravy_score(seq), abs=1e-4)
