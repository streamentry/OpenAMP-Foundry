"""Tests for helix_propensity_score() (Chou-Fasman Pα) and its integration."""
from __future__ import annotations

from openamp_foundry.features.physchem import compute_features, helix_propensity_score
from openamp_foundry.scoring.activity import activity_likeness_score


class TestHelixPropensityScore:
    def test_empty_sequence_returns_zero(self):
        assert helix_propensity_score("") == 0.0

    def test_single_ala_returns_142(self):
        # Ala is the strongest helix-former: Pα = 1.42
        result = helix_propensity_score("A")
        assert result == 1.42

    def test_single_gly_low_propensity(self):
        # Gly is helix-breaking: Pα = 0.57
        assert helix_propensity_score("G") == 0.57

    def test_single_pro_low_propensity(self):
        # Pro is helix-breaking: Pα = 0.57
        assert helix_propensity_score("P") == 0.57

    def test_poly_ala_high_propensity(self):
        result = helix_propensity_score("AAAAAAAAAA")
        assert result == 1.42

    def test_poly_glu_highest_propensity(self):
        # Glu is the strongest helix-former in the table: Pα = 1.51
        result = helix_propensity_score("EEEEEEEEEE")
        assert result == 1.51

    def test_poly_gly_helix_breaking(self):
        result = helix_propensity_score("GGGGGGGGGG")
        assert result == 0.57

    def test_helix_forming_gt_breaking(self):
        # Ala-rich > Gly-rich
        assert helix_propensity_score("AAAAAAA") > helix_propensity_score("GGGGGGG")

    def test_indifferent_near_1p0(self):
        # His has Pα = 1.0 (exactly indifferent)
        result = helix_propensity_score("H")
        assert result == 1.0

    def test_mean_computed_correctly(self):
        # A (1.42) + G (0.57) = mean 0.995
        result = helix_propensity_score("AG")
        assert abs(result - round((1.42 + 0.57) / 2, 4)) < 1e-6

    def test_unknown_residue_uses_indifferent_1p0(self):
        # X not in table → default 1.0
        # A (1.42) + X (1.0) = mean 1.21
        result = helix_propensity_score("AX")
        assert abs(result - round((1.42 + 1.0) / 2, 4)) < 1e-6

    def test_returns_float_rounded_to_4dp(self):
        result = helix_propensity_score("KWKLFKK")
        assert isinstance(result, float)
        assert result == round(result, 4)

    def test_classic_amp_above_1p0(self):
        # KWKLFKKIGAVLKVL is a well-characterized helical AMP; should have Pα > 1.0
        result = helix_propensity_score("KWKLFKKIGAVLKVL")
        assert result > 1.0

    def test_proline_rich_below_1p0(self):
        # GNRPVYIPQPRPPHPR (apidaecin) — many P residues → helix-breaking
        result = helix_propensity_score("GNRPVYIPQPRPPHPR")
        assert result < 1.0


class TestComputeFeaturesHelixPropensity:
    def test_helix_propensity_key_present(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert "helix_propensity" in features

    def test_helix_propensity_is_float(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert isinstance(features["helix_propensity"], float)

    def test_helix_propensity_positive(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        assert features["helix_propensity"] > 0.0

    def test_helix_propensity_reasonable_range(self):
        # Realistic sequences: Pα range 0.57–1.51, typical AMPs ~0.95–1.15
        features = compute_features("KWKLFKKIGAVLKVL")
        assert 0.5 <= features["helix_propensity"] <= 1.6

    def test_empty_sequence_no_crash(self):
        features = compute_features("")
        assert features["helix_propensity"] == 0.0

    def test_helical_amp_vs_proline_rich(self):
        # Helical AMP (magainin-like) should have higher Pα than proline-rich
        helical_features = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        proline_features = compute_features("GNRPVYIPQPRPPHPR")
        assert helical_features["helix_propensity"] > proline_features["helix_propensity"]


class TestActivityScoreWithHelixPropensity:
    def test_activity_score_still_in_0_1(self):
        features = compute_features("KWKLFKKIGAVLKVL")
        score = activity_likeness_score(features)
        assert 0.0 <= score <= 1.0

    def test_helix_forming_amp_gets_bonus(self):
        # KWKLFKKIGAVLKVL (Leu-rich helical AMP) vs GGGGGGGGGG (helix-breaker)
        # The helix-forming sequence should score higher
        helical_features = compute_features("KWKLFKKIGAVLKVL")
        gly_features = compute_features("GGGGGGGGGG")
        assert activity_likeness_score(helical_features) > activity_likeness_score(gly_features)

    def test_fallback_when_helix_propensity_missing(self):
        # If helix_propensity is absent (old feature dict), should not crash
        minimal_features = {
            "length": 15, "charge_density": 0.27, "hydrophobic_fraction": 0.47,
            "aromatic_fraction": 0.07, "hydrophobic_moment": 0.55,
        }
        score = activity_likeness_score(minimal_features)
        assert 0.0 <= score <= 1.0
