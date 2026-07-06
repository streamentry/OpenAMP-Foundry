"""Tests for aggregation-safe mutation generation and balanced charge variants.

Verifies:
  - _max_hydrophobic_run() counts consecutive VILMFW residues correctly
  - generate_aggregation_safe_double_variants() filters out high-run sequences
  - generate_balanced_charge_variants() produces both K and R for each polar position
  - SynthQC.aggregation_propensity_score is populated and consistent with aggregation_risk
"""
from __future__ import annotations

from openamp_foundry.generators.template_mutator import (
    _AGG_HYDROPHOBIC,
    _max_hydrophobic_run,
    generate_aggregation_safe_double_variants,
    generate_balanced_charge_variants,
    generate_all_variants,
)
from openamp_foundry.qc.presynth_check import check_sequence


SEED = "KWKLFKKIGAVLKVL"   # typical AMP-like template, max run = 2


class TestMaxHydrophobicRun:
    def test_empty_string_returns_zero(self):
        assert _max_hydrophobic_run("") == 0

    def test_no_agg_residues_returns_zero(self):
        # KDKE: K, D, K, E — none in VILMFW
        assert _max_hydrophobic_run("KDKE") == 0

    def test_single_agg_residue_returns_one(self):
        assert _max_hydrophobic_run("KVK") == 1

    def test_run_of_four_detected(self):
        # KVLLLK: V,L,L,L at pos 1-4 → run = 4
        assert _max_hydrophobic_run("KVLLLK") == 4

    def test_run_of_eight_detected(self):
        # KVLLLLLLLK: 8 consecutive VILMFW residues
        assert _max_hydrophobic_run("KVLLLLLLLK") == 8

    def test_run_broken_by_non_agg_residue(self):
        # VLK LV: run of 2, break at K, run of 2 → max = 2
        assert _max_hydrophobic_run("VLKLV") == 2

    def test_agg_hydrophobic_constant_matches_expected_set(self):
        # Sanity: the module constant agrees with the documented set VILMFW
        assert _AGG_HYDROPHOBIC == frozenset("VILMFW")

    def test_glycine_alanine_not_in_agg_set(self):
        # G and A are NOT aggregation-driving; VILMFW is the threshold set
        assert "G" not in _AGG_HYDROPHOBIC
        assert "A" not in _AGG_HYDROPHOBIC

    def test_aromatic_in_agg_set(self):
        # F and W are included (aromatic → aggregation-prone)
        assert "F" in _AGG_HYDROPHOBIC
        assert "W" in _AGG_HYDROPHOBIC


class TestAggregationSafeDoubleVariants:
    def test_no_variant_has_run_ge_threshold(self):
        # All output variants must have max hydrophobic run < 4
        variants = generate_aggregation_safe_double_variants(SEED, n_samples=30, seed=42)
        for v in variants:
            run = _max_hydrophobic_run(v)
            assert run < 4, f"Variant {v!r} has hydrophobic run {run} >= 4"

    def test_variants_same_length_as_seed(self):
        variants = generate_aggregation_safe_double_variants(SEED, n_samples=15, seed=42)
        for v in variants:
            assert len(v) == len(SEED), f"Length mismatch: {v!r}"

    def test_seed_not_in_output(self):
        variants = generate_aggregation_safe_double_variants(SEED, n_samples=20, seed=42)
        assert SEED not in variants

    def test_differs_by_at_most_two_positions(self):
        variants = generate_aggregation_safe_double_variants(SEED, n_samples=15, seed=42)
        for v in variants:
            diffs = sum(a != b for a, b in zip(v, SEED))
            assert diffs <= 2, f"Expected ≤2 diffs, got {diffs}: {v!r}"

    def test_no_duplicate_output(self):
        variants = generate_aggregation_safe_double_variants(SEED, n_samples=20, seed=42)
        assert len(variants) == len(set(variants))

    def test_deterministic_with_same_seed(self):
        v1 = generate_aggregation_safe_double_variants(SEED, n_samples=10, seed=99)
        v2 = generate_aggregation_safe_double_variants(SEED, n_samples=10, seed=99)
        assert v1 == v2

    def test_custom_max_run_threshold(self):
        # With max_run=3, even a run of 3 is rejected
        variants = generate_aggregation_safe_double_variants(SEED, n_samples=20, seed=42, max_run=3)
        for v in variants:
            assert _max_hydrophobic_run(v) < 3, f"Run >= 3 in {v!r}"

    def test_produces_output_from_typical_amp_seed(self):
        variants = generate_aggregation_safe_double_variants(SEED, n_samples=10, seed=42)
        assert len(variants) >= 1, "Should produce at least one safe double-sub variant"

    def test_filtering_hydrophobic_seed(self):
        # Seed with run=3 (one below threshold): safe doubles should not extend it to 4+
        seed = "KKVLLK"  # VLL = run of 3
        variants = generate_aggregation_safe_double_variants(seed, n_samples=30, seed=42, max_run=4)
        for v in variants:
            assert _max_hydrophobic_run(v) < 4, f"Created unsafe run in {v!r}"


class TestBalancedChargeVariants:
    def test_generates_both_k_and_r_per_position(self):
        # KSSK: S at positions 1 and 2 → expect K and R variants for both S positions
        seq = "KSSK"
        variant_set = set(generate_balanced_charge_variants(seq, n_positions=5))
        # S at index 1: expect KKSK and KRSK
        assert "KKSK" in variant_set, "Missing S1→K variant"
        assert "KRSK" in variant_set, "Missing S1→R variant"
        # S at index 2: "KS" + replacement + "K"
        assert "KSKK" in variant_set, "Missing S2→K variant"
        assert "KSRK" in variant_set, "Missing S2→R variant"

    def test_all_variants_same_length(self):
        variants = generate_balanced_charge_variants(SEED, n_positions=5)
        for v in variants:
            assert len(v) == len(SEED)

    def test_no_variants_when_no_polar_residues(self):
        # All charged — no S/T/N/Q to replace
        assert generate_balanced_charge_variants("KRKRKR") == []

    def test_replacements_are_k_or_r_only(self):
        seq = "KWKSFKKIGAVLKVL"  # S at position 3
        variants = generate_balanced_charge_variants(seq, n_positions=3)
        for v in variants:
            diff_positions = [i for i, (a, b) in enumerate(zip(v, seq)) if a != b]
            assert len(diff_positions) == 1
            pos = diff_positions[0]
            assert v[pos] in "KR", f"Replacement is {v[pos]!r}, expected K or R"

    def test_seed_not_in_variants(self):
        seq = "KWKSFKKIGAVLKVL"
        variants = generate_balanced_charge_variants(seq)
        assert seq not in variants

    def test_no_duplicates(self):
        variants = generate_balanced_charge_variants(SEED, n_positions=10)
        assert len(variants) == len(set(variants))


class TestGenerateAllVariantsUpdated:
    def test_no_variant_in_all_variants_has_run_ge_4(self):
        # generate_all_variants filters both single- and double-substitution variants
        variants = generate_all_variants(SEED, n_double=20, n_charge_enhance=8)
        for v in variants:
            assert _max_hydrophobic_run(v) < 4, f"{v!r} has run >= 4"

    def test_borderline_seed_single_sub_filtered(self):
        # "KVLLAK": max run = 3 (VLL). Single sub A→L at pos 4 gives "KVLLLK" = run 4.
        # generate_all_variants must NOT include "KVLLLK" (filtered by single-sub guard).
        seed = "KVLLAK"
        variants = set(generate_all_variants(seed, n_double=10, n_charge_enhance=3))
        assert "KVLLLK" not in variants, "KVLLLK (run=4) should be filtered from single subs"
        # All returned variants must respect the threshold
        for v in variants:
            assert _max_hydrophobic_run(v) < 4, f"{v!r} has run >= 4 from borderline seed"

    def test_all_variants_includes_both_k_and_r_charge_variants(self):
        # KWKSFKKIGAVLKVL has S at position 3; should produce S→K and S→R variants
        seq = "KWKSFKKIGAVLKVL"
        variants = set(generate_all_variants(seq, n_charge_enhance=5))
        # K and R replacement at position 3
        k_variant = seq[:3] + "K" + seq[4:]
        r_variant = seq[:3] + "R" + seq[4:]
        assert k_variant in variants, f"K-charge variant {k_variant!r} missing"
        assert r_variant in variants, f"R-charge variant {r_variant!r} missing"


class TestSynthQCAggregationPropensityScore:
    def test_field_exists_on_synthqc(self):
        qc = check_sequence("test", "KWKLFKKIGAVLKVL")
        assert hasattr(qc, "aggregation_propensity_score")

    def test_field_in_to_dict(self):
        qc = check_sequence("test", "KWKLFKKIGAVLKVL")
        d = qc.to_dict()
        assert "aggregation_propensity_score" in d

    def test_score_is_unit_interval(self):
        for seq in ["KKKKKK", "IIIIIIII", "KWKLFKKIGAVLKVL", "GIGKFLHSAKKFGKAFVGEIMNS"]:
            qc = check_sequence("test", seq)
            s = qc.aggregation_propensity_score
            assert 0.0 <= s <= 1.0, f"score={s} out of [0,1] for {seq}"

    def test_high_run_peptide_has_high_score(self):
        # IIIIIIIIII: run of 10 → aggregation_propensity = 1.0
        qc = check_sequence("high_agg", "IIIIIIIIII")
        assert qc.aggregation_propensity_score > 0.5
        assert qc.aggregation_risk is True

    def test_polar_peptide_has_zero_score(self):
        qc = check_sequence("polar", "KRKRKRKR")
        assert qc.aggregation_propensity_score == 0.0
        assert qc.aggregation_risk is False

    def test_score_consistent_with_boolean_flag(self):
        # When aggregation_risk is True (run >= 4), score should be > 0
        qc_risky = check_sequence("risky", "KVLLLKVLLLK")
        assert qc_risky.aggregation_risk is True
        assert qc_risky.aggregation_propensity_score > 0.0

    def test_score_zero_when_no_run(self):
        # Pure cationic: no VILMFW residues → score = 0
        qc = check_sequence("nocr", "KKKKKKKKK")
        assert qc.aggregation_propensity_score == 0.0
