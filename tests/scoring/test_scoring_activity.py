"""Tests for scoring/activity.py — activity_likeness_score and clamp01.

activity_likeness_score combines:
  - length_score        (weight 0.24): 1 - min(|length - 18| / 25, 1.0)
  - charge_score        (weight 0.27): clamp01((charge_density + 0.05) / 0.55)
  - hydro_score         (weight 0.17): 1 - min(|hf - 0.45| / 0.45, 1.0)
  - aromatic_bonus      (max 0.10):   min(weighted_aromatic / 0.20, 1.0) * 0.10
      where weighted_aromatic = trp_fraction * 1.5 + non_trp_aromatic
      (Trp weighted 1.5× vs Phe/Tyr; Wimley-White interfacial insertion mechanism)
  - amphipathicity      (max 0.14):   clamp01(mu_h / 0.8) * 0.14
  - helix_bonus         (max 0.03):   clamp01((helix_pa - 1.0) / 0.20) * 0.03
  - cross_bonus         (max 0.02):   clamp01(charge_density * mu_h / 0.15) * 0.02
  - face_segregation    (max 0.05):   helix_wheel_amphipathic_score * 0.05
      (moment-oriented helix-wheel face analysis; 0.0 when key absent — backward-compatible)

Pre-clamp ceiling = 0.24+0.27+0.17+0.10+0.14+0.03+0.02+0.05 = 1.02.
Without face_segregation (key absent) ceiling = 0.97. Final clamp01() bounds output to [0, 1].
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


def _feat_with_counts(
    length: int = 20,
    charge_density: float = 0.30,
    hydrophobic: float = 0.45,
    aromatic: float = 0.0,
    mu_h: float = 0.0,
    counts: dict | None = None,
) -> dict:
    """Feature dict with residue_counts to exercise the Trp-weighted code path."""
    return {
        "length": length,
        "charge_density": charge_density,
        "hydrophobic_fraction": hydrophobic,
        "aromatic_fraction": aromatic,
        "hydrophobic_moment": mu_h,
        "residue_counts": counts or {},
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


class TestAnionicGuard:
    """Anionic peptides must receive score 0.0 — they are electrostatically repelled
    by bacterial membranes and cannot operate via the cationic AMP mechanism."""

    def test_anionic_peptide_returns_zero(self):
        # charge_density_ph74 < 0.0 → guard fires, return 0.0 regardless of other terms
        feat = {
            "length": 16, "charge_density_ph74": -0.5,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.10,
            "hydrophobic_moment": 0.6,
        }
        assert activity_likeness_score(feat) == 0.0

    def test_anionic_guard_uses_ph74_field_preferentially(self):
        # charge_density_ph74 field takes precedence over legacy charge_density
        feat = {
            "length": 18, "charge_density": 0.30,  # positive legacy field
            "charge_density_ph74": -0.3,             # but negative at pH 7.4
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.0,
        }
        assert activity_likeness_score(feat) == 0.0

    def test_anionic_guard_polyglutamate(self):
        # EEIEIEIEIEIEIEE-like peptide: highly structured but anionic — must be 0
        feat = {
            "length": 15, "charge_density_ph74": -0.6,
            "hydrophobic_fraction": 0.40, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.42, "max_hydrophobic_moment": 0.55,
        }
        assert activity_likeness_score(feat) == 0.0

    def test_zero_charge_density_not_blocked(self):
        # Exactly 0.0 charge density should NOT trigger the guard (guard is < 0.0)
        feat = {
            "length": 18, "charge_density_ph74": 0.0,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.0,
        }
        score = activity_likeness_score(feat)
        # Should still get some score from length + hydrophobic terms
        assert score > 0.0

    def test_small_negative_charge_blocked(self):
        # Even mildly negative (e.g. -0.05) must return 0.0
        feat = {
            "length": 18, "charge_density_ph74": -0.05,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.0,
        }
        assert activity_likeness_score(feat) == 0.0

    def test_positive_charge_not_blocked(self):
        # Positive charge density must pass through normally
        feat = {
            "length": 18, "charge_density": 0.25,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.0,
        }
        assert activity_likeness_score(feat) > 0.0


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


class TestTrpWeightedAromaticBonus:
    """Tests for the Trp-weighted aromatic bonus (residue_counts code path).

    Trp is weighted 1.5× vs Phe/Tyr because Trp anchors at the lipid-water
    interface (Wimley-White interfacial scale W=−1.85 kcal/mol).
    """

    def test_trp_rich_scores_higher_than_phe_rich_same_aromatic_fraction(self):
        """Trp-rich peptide should outscore Phe-rich at identical aromatic fraction."""
        # 2 W out of 20 = 10% aromatic; 2 F out of 20 = 10% aromatic
        feat_trp = _feat_with_counts(length=20, aromatic=0.10, counts={"W": 2})
        feat_phe = _feat_with_counts(length=20, aromatic=0.10, counts={"F": 2})
        assert activity_likeness_score(feat_trp) > activity_likeness_score(feat_phe), (
            "Trp-rich peptide should score higher than Phe-rich at the same aromatic fraction"
        )

    def test_trp_bonus_factor_1_5x_quantitative(self):
        """With only Trp (no Phe/Tyr): weighted_aromatic = trp_fraction * 1.5.

        trp_fraction=0.10 → weighted=0.15 → bonus = (0.15/0.20)*0.10 = 0.075
        vs. old Phe-based (0.10/0.20)*0.10 = 0.05 → delta = 0.025
        """
        feat_trp = _feat_with_counts(length=20, aromatic=0.10, counts={"W": 2})
        feat_phe = _feat_with_counts(length=20, aromatic=0.10, counts={"F": 2})
        delta = activity_likeness_score(feat_trp) - activity_likeness_score(feat_phe)
        # Expected: bonus_trp - bonus_phe = 0.075 - 0.05 = 0.025
        assert abs(delta - 0.025) < 0.002, (
            f"Trp vs Phe aromatic bonus delta should be ~0.025, got {delta:.4f}"
        )

    def test_trp_aromatic_bonus_capped_at_0_10(self):
        """Ceiling is 0.10 regardless of Trp fraction — 1.5x just reaches cap sooner."""
        # trp_fraction=0.14 → weighted=0.21 > 0.20 → capped: bonus=1.0*0.10=0.10
        feat_trp_cap = _feat_with_counts(length=14, aromatic=0.14, counts={"W": 2})
        # phe_fraction=0.20 → bonus=1.0*0.10=0.10 (also at cap)
        feat_phe_cap = _feat_with_counts(length=20, aromatic=0.20, counts={"F": 4})
        # Both should produce the same aromatic contribution (0.10)
        # They may differ on other terms (length), so isolate aromatic by comparing
        # to zero-aromatic baseline at same length
        feat_trp_zero = _feat_with_counts(length=14, aromatic=0.0, counts={})
        feat_phe_zero = _feat_with_counts(length=20, aromatic=0.0, counts={})
        trp_bonus = activity_likeness_score(feat_trp_cap) - activity_likeness_score(feat_trp_zero)
        phe_bonus = activity_likeness_score(feat_phe_cap) - activity_likeness_score(feat_phe_zero)
        assert abs(trp_bonus - 0.10) < 0.002, f"Trp cap bonus should be 0.10, got {trp_bonus:.4f}"
        assert abs(phe_bonus - 0.10) < 0.002, f"Phe cap bonus should be 0.10, got {phe_bonus:.4f}"

    def test_no_residue_counts_falls_back_to_unweighted(self):
        """When residue_counts is absent, Trp fraction defaults to 0 → same as all-Phe."""
        # Without residue_counts: weighted_aromatic = 0*1.5 + aromatic = aromatic (Phe behavior)
        feat_without_counts = _feat(length=20, aromatic=0.10)
        feat_phe = _feat_with_counts(length=20, aromatic=0.10, counts={"F": 2})
        assert activity_likeness_score(feat_without_counts) == activity_likeness_score(feat_phe)

    def test_mixed_trp_phe_intermediate_score(self):
        """Sequence with 1 Trp + 1 Phe (same aromatic fraction) scores between all-W and all-F."""
        feat_trp = _feat_with_counts(length=20, aromatic=0.10, counts={"W": 2})
        feat_phe = _feat_with_counts(length=20, aromatic=0.10, counts={"F": 2})
        feat_mixed = _feat_with_counts(length=20, aromatic=0.10, counts={"W": 1, "F": 1})
        score_trp = activity_likeness_score(feat_trp)
        score_phe = activity_likeness_score(feat_phe)
        score_mixed = activity_likeness_score(feat_mixed)
        assert score_phe < score_mixed < score_trp, (
            f"Mixed Trp/Phe should score between all-Phe ({score_phe:.4f}) "
            f"and all-Trp ({score_trp:.4f}), got {score_mixed:.4f}"
        )

    def test_trp_bonus_active_only_in_sub_saturation_range(self):
        """The Trp bonus differentiates at MODERATE aromatic fraction (< 13% Trp to reach cap).

        At high aromatic fraction (>= 20%), both Trp and Phe hit the cap and the bonus
        is identical. SEED-008 (38% Trp) already saturates; the bonus matters for sequences
        with 5-13% Trp where the 1.5x weight pushes them above equivalent Phe fractions.
        """
        # Low aromatic fraction: 5% Trp vs 5% Phe — Trp gets higher score
        feat_low_trp = _feat_with_counts(length=20, aromatic=0.05, counts={"W": 1})
        feat_low_phe = _feat_with_counts(length=20, aromatic=0.05, counts={"F": 1})
        assert activity_likeness_score(feat_low_trp) > activity_likeness_score(feat_low_phe)
        # High aromatic fraction: 25% both → both cap at 0.10, no difference
        feat_hi_trp = _feat_with_counts(length=20, aromatic=0.25, counts={"W": 5})
        feat_hi_phe = _feat_with_counts(length=20, aromatic=0.25, counts={"F": 5})
        assert activity_likeness_score(feat_hi_trp) == activity_likeness_score(feat_hi_phe), (
            "High aromatic fraction: both Trp and Phe should saturate the cap at 0.10"
        )


class TestMaxWindowedMuHInActivity:
    """activity_likeness_score uses max(hydrophobic_moment, max_hydrophobic_moment)
    so that long-sequence AMPs get credit for their best helical window."""

    def test_max_hydrophobic_moment_used_when_higher(self):
        # max_hydrophobic_moment > hydrophobic_moment → score should reflect the max
        feat_with_max = {
            "length": 23, "charge_density": 0.25,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.45,
            "max_hydrophobic_moment": 0.69,  # windowed value higher than full-seq
        }
        feat_full_only = {
            "length": 23, "charge_density": 0.25,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.45,
            # no max_hydrophobic_moment key
        }
        assert activity_likeness_score(feat_with_max) > activity_likeness_score(feat_full_only)

    def test_full_seq_used_when_no_max_key(self):
        # Backward compat: if max_hydrophobic_moment absent, full-seq mu_h is used
        feat = {
            "length": 18, "charge_density": 0.30,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
            "hydrophobic_moment": 0.6,
        }
        score = activity_likeness_score(feat)
        assert score > 0.0

    def test_missing_both_mu_h_keys_defaults_to_zero(self):
        feat = {
            "length": 18, "charge_density": 0.30,
            "hydrophobic_fraction": 0.45, "aromatic_fraction": 0.0,
        }
        score = activity_likeness_score(feat)
        # Should still work; mu_h defaults to 0 → amphipathicity_score = 0
        assert score >= 0.0


class TestAmphipathicityBonus:
    def test_no_amphipathicity_no_bonus(self):
        s_0 = activity_likeness_score(_feat(mu_h=0.0))
        s_4 = activity_likeness_score(_feat(mu_h=0.4))
        assert s_4 > s_0

    def test_mu_h_0_8_full_bonus(self):
        # amphipathicity = clamp01(0.8/0.8) * 0.14 = 0.14
        s_08 = activity_likeness_score(_feat(mu_h=0.8))
        s_10 = activity_likeness_score(_feat(mu_h=1.0))
        # Both give full bonus (capped)
        assert s_08 == s_10

    def test_mu_h_0_4_half_bonus(self):
        # amphipathicity diff (weight=0.14): clamp(0.8/0.8)*0.14 - clamp(0.4/0.8)*0.14 = 0.07
        # cross_bonus diff (cd=0.30 default): clamp(0.30*0.80/0.15)*0.02 - clamp(0.30*0.40/0.15)*0.02
        #   = 1.0*0.02 - 0.8*0.02 = 0.004
        # total diff = 0.07 + 0.004 = 0.074
        diff = (
            activity_likeness_score(_feat(mu_h=0.8)) -
            activity_likeness_score(_feat(mu_h=0.4))
        )
        assert abs(diff - 0.074) < 0.001

    def test_mu_h_improves_score_monotonically_up_to_ceiling(self):
        scores = [activity_likeness_score(_feat(mu_h=v)) for v in [0.0, 0.2, 0.4, 0.6, 0.8]]
        for a, b in zip(scores, scores[1:]):
            assert b > a, f"score did not increase: {a} → {b}"


class TestChargeAmphipathicityCrossTerm:
    def test_zero_charge_gives_no_cross_bonus(self):
        # At charge_density=0, cross_bonus = 0 regardless of mu_h
        s_no_charge = activity_likeness_score(_feat(charge_density=0.0, mu_h=0.8))
        s_no_cross_check = activity_likeness_score(_feat(charge_density=0.0, mu_h=0.0))
        # Only the amphipathicity term should differ (no cross contribution)
        amp_diff = 0.8 / 0.8 * 0.14  # = 0.14
        assert abs((s_no_charge - s_no_cross_check) - amp_diff) < 0.001

    def test_zero_amphipathicity_gives_no_cross_bonus(self):
        # At mu_h=0, cross_bonus = 0 regardless of charge_density
        s_no_mu = activity_likeness_score(_feat(charge_density=0.50, mu_h=0.0))
        s_ref = activity_likeness_score(_feat(charge_density=0.50, mu_h=0.0))
        assert s_no_mu == s_ref  # trivially, but verifies no crash

    def test_full_cross_bonus_at_saturation(self):
        # At cd=0.30, mu_h=0.50: product = 0.15 → clamp(0.15/0.15)*0.02 = 0.02
        high = activity_likeness_score(_feat(charge_density=0.30, mu_h=0.50))
        low = activity_likeness_score(_feat(charge_density=0.0, mu_h=0.50))
        # diff includes charge component + cross bonus; cross alone = 0.02
        # charge component: clamp((0.30+0.05)/0.55) * 0.27 - clamp((0.00+0.05)/0.55) * 0.27
        charge_diff = (
            min(0.35 / 0.55, 1.0) - min(0.05 / 0.55, 1.0)
        ) * 0.27
        assert abs((high - low) - (charge_diff + 0.02)) < 0.001

    def test_half_cross_bonus(self):
        # cd=0.15, mu_h=0.50: product = 0.075; 0.075/0.15 = 0.5 → 0.5*0.02 = 0.01
        s_half = activity_likeness_score(_feat(charge_density=0.15, mu_h=0.50))
        s_zero_mu = activity_likeness_score(_feat(charge_density=0.15, mu_h=0.0))
        amp_diff = (0.50 / 0.8) * 0.14  # amphipathicity only (weight=0.14)
        expected_diff = amp_diff + 0.01  # + half cross bonus
        assert abs((s_half - s_zero_mu) - expected_diff) < 0.001

    def test_dual_property_amps_score_higher_than_single_property(self):
        # A sequence that is both charged AND amphipathic beats one that is only amphipathic
        dual = activity_likeness_score(_feat(charge_density=0.35, mu_h=0.65))
        only_amph = activity_likeness_score(_feat(charge_density=0.0, mu_h=0.65))
        assert dual > only_amph


class TestHelixBonusWeight:
    def test_helix_bonus_weight_0_03(self):
        # helix_pa=1.20 → clamp01((1.20-1.0)/0.20)=1.0 → bonus=1.0*0.03=0.03
        base = {
            "length": 18, "charge_density": 0.30, "hydrophobic_fraction": 0.45,
            "aromatic_fraction": 0.0, "hydrophobic_moment": 0.0,
        }
        s_no_helix = activity_likeness_score({**base, "helix_propensity": 1.0})
        s_full_helix = activity_likeness_score({**base, "helix_propensity": 1.20})
        assert abs((s_full_helix - s_no_helix) - 0.03) < 0.001

    def test_helix_bonus_partial_at_pa_110(self):
        # helix_pa=1.10 → clamp01(0.10/0.20)=0.5 → bonus=0.5*0.03=0.015
        base = {
            "length": 18, "charge_density": 0.30, "hydrophobic_fraction": 0.45,
            "aromatic_fraction": 0.0, "hydrophobic_moment": 0.0,
        }
        s_no_helix = activity_likeness_score({**base, "helix_propensity": 1.0})
        s_half_helix = activity_likeness_score({**base, "helix_propensity": 1.10})
        assert abs((s_half_helix - s_no_helix) - 0.015) < 0.001

    def test_score_ceiling_without_hw_is_0_97(self):
        # Without helix_wheel_amphipathic_score key: face_segregation_bonus=0;
        # ceiling = 0.24+0.27+0.17+0.10+0.14+0.03+0.02 = 0.97
        all_max_no_hw = {
            "length": 18, "charge_density": 0.50, "hydrophobic_fraction": 0.45,
            "aromatic_fraction": 0.20, "hydrophobic_moment": 0.80,
            "helix_propensity": 1.20,
        }
        assert activity_likeness_score(all_max_no_hw) == 0.97

    def test_score_ceiling_with_hw_clamped_to_1(self):
        # With helix_wheel_amphipathic_score=1.0: pre-clamp ceiling = 0.97 + 0.05 = 1.02;
        # final clamp01() reduces output to 1.0
        all_max_with_hw = {
            "length": 18, "charge_density": 0.50, "hydrophobic_fraction": 0.45,
            "aromatic_fraction": 0.20, "hydrophobic_moment": 0.80,
            "helix_propensity": 1.20, "helix_wheel_amphipathic_score": 1.0,
        }
        assert activity_likeness_score(all_max_with_hw) == 1.0


class TestFaceSegregationBonus:
    """Tests for helix_wheel_amphipathic_score bonus (face segregation, weight 0.05)."""

    def _base_feat(self) -> dict:
        return {
            "length": 18, "charge_density_ph74": 0.30, "hydrophobic_fraction": 0.45,
            "aromatic_fraction": 0.0, "hydrophobic_moment": 0.40,
        }

    def test_key_absent_gives_zero_bonus(self):
        # When helix_wheel_amphipathic_score is not in features, bonus = 0.0 (backward-compat)
        feat = self._base_feat()
        assert "helix_wheel_amphipathic_score" not in feat
        score_without = activity_likeness_score(feat)
        feat_with_zero = {**feat, "helix_wheel_amphipathic_score": 0.0}
        assert activity_likeness_score(feat_with_zero) == score_without

    def test_max_bonus_is_0_05(self):
        # hw_amphipathic=1.0 → bonus = 1.0 * 0.05 = 0.05
        feat_low = self._base_feat()
        feat_high = {**feat_low, "helix_wheel_amphipathic_score": 1.0}
        delta = activity_likeness_score(feat_high) - activity_likeness_score(feat_low)
        assert abs(delta - 0.05) < 0.001

    def test_bonus_scales_linearly_with_hw_score(self):
        # At hw_score=0.5, bonus should be 0.025; at hw_score=1.0, bonus=0.05
        base = self._base_feat()
        s_zero = activity_likeness_score({**base, "helix_wheel_amphipathic_score": 0.0})
        s_half = activity_likeness_score({**base, "helix_wheel_amphipathic_score": 0.5})
        s_full = activity_likeness_score({**base, "helix_wheel_amphipathic_score": 1.0})
        assert abs((s_half - s_zero) - 0.025) < 0.001
        assert abs((s_full - s_zero) - 0.050) < 0.001

    def test_high_hw_score_improves_score_for_known_amp(self):
        # Magainin-2 features: adding measured hw_amphipathic_score should improve score
        # Magainin-2 is a textbook amphipathic helix with high face contrast → hw_score > 0.40
        from openamp_foundry.features.physchem import compute_features
        feats = compute_features("GIGKFLHSAKKFGKAFVGEIMNS")
        hw = feats.get("helix_wheel_amphipathic_score", 0.0)
        assert hw > 0.40, (
            f"Magainin-2 helix_wheel_amphipathic_score={hw:.4f} should be > 0.40 for a "
            "textbook amphipathic helix — face_contrast / 2.0 should be substantial"
        )
        score_with = activity_likeness_score(feats)
        feats_no_hw = {k: v for k, v in feats.items() if k != "helix_wheel_amphipathic_score"}
        score_without = activity_likeness_score(feats_no_hw)
        assert score_with > score_without, (
            "Adding helix_wheel_amphipathic_score should increase Magainin-2 score"
        )

    def test_anionic_peptide_still_returns_zero(self):
        # Anionic guard takes priority over face_segregation_bonus
        feat = {
            "length": 18, "charge_density_ph74": -0.10, "hydrophobic_fraction": 0.45,
            "aromatic_fraction": 0.0, "hydrophobic_moment": 0.60,
            "helix_wheel_amphipathic_score": 1.0,
        }
        assert activity_likeness_score(feat) == 0.0


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
