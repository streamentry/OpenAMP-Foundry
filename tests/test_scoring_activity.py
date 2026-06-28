"""Tests for scoring/activity.py — activity_likeness_score and clamp01.

activity_likeness_score combines:
  - length_score  (weight 0.24): 1 - min(|length - 18| / 25, 1.0)
  - charge_score  (weight 0.27): clamp01((charge_density + 0.05) / 0.55)
  - hydro_score   (weight 0.17): 1 - min(|hf - 0.45| / 0.45, 1.0)
  - aromatic_bonus (max 0.10): min(aromatic / 0.20, 1.0) * 0.10
  - amphipathicity (max 0.15): clamp01(mu_h / 0.8) * 0.15

Total max ~0.93. Result is clamped to [0, 1] and rounded to 4 dp.
"""
from __future__ import annotations

from openamp_foundry.scoring.activity import activity_likeness_score, clamp01


def _feat(
    length: int = 18,
    charge_density: float = 0.30,
    hydrophobic: float = 0.45,
    aromatic: float = 0.0,
    mu_h: float = 0.0,
) -> dict:
    return {
        "length": length,
        "charge_density": charge_density,
        "hydrophobic_fraction": hydrophobic,
        "aromatic_fraction": aromatic,
        "hydrophobic_moment": mu_h,
    }


class TestClamp01:
    def test_clamps_below_zero(self):
        assert clamp01(-5.0) == 0.0

    def test_clamps_above_one(self):
        assert clamp01(3.0) == 1.0

    def test_passes_through_mid_range(self):
        assert abs(clamp01(0.5) - 0.5) < 1e-9

    def test_at_zero(self):
        assert clamp01(0.0) == 0.0

    def test_at_one(self):
        assert clamp01(1.0) == 1.0


class TestActivityLikenessScore:
    def test_returns_float(self):
        assert isinstance(activity_likeness_score(_feat()), float)

    def test_returns_value_in_unit_interval(self):
        for length in [5, 8, 18, 35, 50]:
            s = activity_likeness_score(_feat(length=length))
            assert 0.0 <= s <= 1.0, f"score={s} out of range for length={length}"

    def test_result_rounded_to_4dp(self):
        s = activity_likeness_score(_feat(length=20, charge_density=0.33))
        assert s == round(s, 4)

    def test_no_hydrophobic_moment_key_defaults_gracefully(self):
        feat = {
            "length": 18, "charge_density": 0.30,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            # hydrophobic_moment deliberately omitted — should default to 0.0
        }
        score = activity_likeness_score(feat)
        expected = activity_likeness_score(_feat(mu_h=0.0))
        assert score == expected


class TestLengthComponent:
    def test_optimal_length_18_highest(self):
        # length_score peaks at length=18
        s_18 = activity_likeness_score(_feat(length=18))
        s_10 = activity_likeness_score(_feat(length=10))
        s_30 = activity_likeness_score(_feat(length=30))
        assert s_18 > s_10 and s_18 > s_30

    def test_length_43_scores_zero_length_component(self):
        # |43 - 18| / 25 = 1.0 → length_score = 0.0
        # contribution = 0.24 * 0.0 = 0 from length
        score_43 = activity_likeness_score(_feat(length=43))
        score_44 = activity_likeness_score(_feat(length=44))
        # Both have zero length_score → same contribution
        assert score_43 == score_44

    def test_shorter_sequence_penalised_vs_optimal(self):
        assert activity_likeness_score(_feat(length=5)) < activity_likeness_score(_feat(length=18))

    def test_longer_sequence_penalised_vs_optimal(self):
        assert activity_likeness_score(_feat(length=40)) < activity_likeness_score(_feat(length=18))

    def test_length_30_midrange_verifies_normalization_constant(self):
        # |30-18|/25 = 0.48 → length_score = 0.52 → 0.24*0.52 = 0.1248
        # + 0.27*clamp01(0.35/0.55) = 0.1718 + 0.17*1.0 = 0.4666
        # Changing the constant 25 to 20 would give |30-18|/20=0.60 → score≠0.4666
        score = activity_likeness_score(_feat(length=30))
        assert abs(score - 0.4666) < 0.001


class TestChargeComponent:
    def test_negative_charge_penalised(self):
        neg = activity_likeness_score(_feat(charge_density=-0.5))
        pos = activity_likeness_score(_feat(charge_density=0.3))
        assert pos > neg

    def test_charge_score_formula(self):
        # charge_score = clamp01((0.30 + 0.05) / 0.55) = clamp01(0.6364) = 0.6364
        # contribution = 0.27 * 0.6364 ≈ 0.1718
        # At length=18, hydrophobic=0.45, aromatic=0, mu_h=0:
        #   length_score = 1.0, contribution = 0.24
        #   hydro_score = 1.0 - 0 = 1.0, contribution = 0.17
        #   total ≈ 0.24 + 0.1718 + 0.17 = 0.5818
        score = activity_likeness_score(_feat(charge_density=0.30))
        assert abs(score - 0.5818) < 0.001

    def test_increasing_charge_improves_score_up_to_ceiling(self):
        low = activity_likeness_score(_feat(charge_density=0.10))
        mid = activity_likeness_score(_feat(charge_density=0.30))
        high = activity_likeness_score(_feat(charge_density=0.50))
        assert low < mid < high

    def test_very_high_charge_clamped(self):
        # charge_score saturates at 1.0 when (cd + 0.05) / 0.55 >= 1.0 (cd >= 0.50)
        score_0_50 = activity_likeness_score(_feat(charge_density=0.50))
        score_0_90 = activity_likeness_score(_feat(charge_density=0.90))
        assert score_0_50 == score_0_90


class TestHydrophobicComponent:
    def test_optimal_hydrophobic_fraction_0_45(self):
        # hydro_score = 1 - |0.45-0.45|/0.45 = 1.0
        s_opt = activity_likeness_score(_feat(hydrophobic=0.45))
        s_low = activity_likeness_score(_feat(hydrophobic=0.10))
        s_high = activity_likeness_score(_feat(hydrophobic=0.80))
        assert s_opt > s_low and s_opt > s_high

    def test_hydrophobic_0_0_zero_score_component(self):
        # hydro_score = 1 - min(0.45/0.45, 1.0) = 0.0
        score_0 = activity_likeness_score(_feat(hydrophobic=0.00))
        score_0_01 = activity_likeness_score(_feat(hydrophobic=0.01))
        assert score_0 < score_0_01

    def test_hydrophobic_0_90_penalised(self):
        # hydro_score = 1 - min(0.45/0.45, 1.0) = 0.0 (clamped)
        s_90 = activity_likeness_score(_feat(hydrophobic=0.90))
        s_45 = activity_likeness_score(_feat(hydrophobic=0.45))
        assert s_90 < s_45

    def test_hydrophobic_225_midrange_verifies_normalization_constant(self):
        # |0.225-0.45|/0.45 = 0.5 → hydro_score = 0.5 → 0.17*0.5 = 0.085
        # + 0.24*1.0 (length=18) + 0.27*clamp01(0.35/0.55) = 0.4968
        # Changing the denominator 0.45 to 0.40 would give |0.225-0.45|/0.40=0.5625 → score≠0.4968
        score = activity_likeness_score(_feat(hydrophobic=0.225))
        assert abs(score - 0.4968) < 0.001


class TestAromaticBonus:
    def test_no_aromatic_no_bonus(self):
        score_0 = activity_likeness_score(_feat(aromatic=0.0))
        # At aromatic=0, aromatic_bonus = 0; verify by checking aromatic != 0 gives more
        score_01 = activity_likeness_score(_feat(aromatic=0.10))
        assert score_01 > score_0

    def test_aromatic_0_20_full_bonus(self):
        # aromatic_bonus = min(0.20/0.20, 1.0) * 0.10 = 0.10
        s_20 = activity_likeness_score(_feat(aromatic=0.20))
        s_25 = activity_likeness_score(_feat(aromatic=0.25))
        # Both give full bonus (capped at 1.0 * 0.10 = 0.10)
        assert s_20 == s_25

    def test_aromatic_half_gives_half_bonus(self):
        # aromatic = 0.10 → aromatic_bonus = 0.5 * 0.10 = 0.05
        # aromatic = 0.20 → aromatic_bonus = 1.0 * 0.10 = 0.10 (+0.05)
        diff = (
            activity_likeness_score(_feat(aromatic=0.20)) -
            activity_likeness_score(_feat(aromatic=0.10))
        )
        assert abs(diff - 0.05) < 0.001


class TestAmphipathicityBonus:
    def test_no_amphipathicity_no_bonus(self):
        s_0 = activity_likeness_score(_feat(mu_h=0.0))
        s_4 = activity_likeness_score(_feat(mu_h=0.4))
        assert s_4 > s_0

    def test_mu_h_0_8_full_bonus(self):
        # amphipathicity = clamp01(0.8/0.8) * 0.15 = 0.15
        s_08 = activity_likeness_score(_feat(mu_h=0.8))
        s_10 = activity_likeness_score(_feat(mu_h=1.0))
        # Both give full bonus (capped)
        assert s_08 == s_10

    def test_mu_h_0_4_half_bonus(self):
        # amphipathicity = clamp01(0.4/0.8) * 0.15 = 0.5 * 0.15 = 0.075
        # diff between mu_h=0.8 and mu_h=0.4 should be 0.075
        diff = (
            activity_likeness_score(_feat(mu_h=0.8)) -
            activity_likeness_score(_feat(mu_h=0.4))
        )
        assert abs(diff - 0.075) < 0.001

    def test_mu_h_improves_score_monotonically_up_to_ceiling(self):
        scores = [activity_likeness_score(_feat(mu_h=v)) for v in [0.0, 0.2, 0.4, 0.6, 0.8]]
        for a, b in zip(scores, scores[1:]):
            assert b > a, f"score did not increase: {a} → {b}"


class TestKnownAMPs:
    def test_magainin_like_scores_well(self):
        # KWKLFKKIGAVLKVL — canonical AMP-like sequence
        # length=15, moderate charge, 40% hydrophobic → should score > 0.5
        feat = {
            "length": 15, "charge_density": 0.40,
            "hydrophobic_fraction": 0.47, "aromatic_fraction": 0.07,
            "hydrophobic_moment": 0.55,
        }
        assert activity_likeness_score(feat) > 0.5

    def test_polyglutamate_scores_poorly(self):
        # EEEEEEEEEEEEEEEE — highly negative, no hydrophobic, not AMP-like
        feat = {
            "length": 16, "charge_density": -1.0,
            "hydrophobic_fraction": 0.0, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.0,
        }
        assert activity_likeness_score(feat) < 0.3
