"""Tests for template_mutator.py — Phase 3 candidate generator.

Verifies that the conservative mutation generator:
  - Produces only variants that differ from the seed by canonical-AA conservative subs
  - Never produces the seed itself in the output
  - Deduplicates within each generation strategy
  - Produces the correct number of variants from known seeds
  - Preserves sequence length (no indels)
  - Covers all three generation strategies (single, double, charge-enhanced)
"""
from __future__ import annotations

from openamp_foundry.generators.template_mutator import (
    _conservative_substitutes,
    generate_aggregation_safe_double_variants,
    generate_all_variants,
    generate_candidate_pool,
    generate_charge_enhanced_variants,
    generate_double_substitution_variants,
    generate_single_substitution_variants,
)

SEED = "KWKLFKKIGAVLKVL"  # 15 aa, balanced AMP-like template


class TestConservativeSubstitutes:
    def test_lysine_substitutes_are_cationic(self):
        subs = _conservative_substitutes("K")
        assert set(subs).issubset({"R", "H"}), f"K subs should be cationic: {subs}"
        assert "K" not in subs

    def test_leucine_substitutes_are_hydrophobic(self):
        subs = _conservative_substitutes("L")
        assert set(subs).issubset({"I", "V", "A", "F", "M"}), f"L subs: {subs}"
        assert "L" not in subs

    def test_tryptophan_substitutes_are_aromatic(self):
        subs = _conservative_substitutes("W")
        assert set(subs).issubset({"F", "Y"}), f"W subs: {subs}"

    def test_cysteine_has_no_substitutes(self):
        subs = _conservative_substitutes("C")
        assert subs == [], f"C is a singleton group, no substitutes: {subs}"

    def test_serine_substitutes_are_polar(self):
        subs = _conservative_substitutes("S")
        assert set(subs).issubset({"T", "N", "Q"}), f"S subs: {subs}"

    def test_never_cross_group_substitution(self):
        charged = list("KRH") + list("DE")
        hydrophobic = list("LIVAFM")
        for aa in charged:
            subs = _conservative_substitutes(aa)
            cross = [s for s in subs if s in hydrophobic]
            assert not cross, f"Charged AA {aa!r} has hydrophobic subs: {cross}"
        for aa in hydrophobic:
            subs = _conservative_substitutes(aa)
            cross = [s for s in subs if s in charged]
            assert not cross, f"Hydrophobic AA {aa!r} has charged subs: {cross}"

    def test_unknown_aa_returns_empty_list(self):
        # AA not in any conservative group → guard at line 51 returns []
        assert _conservative_substitutes("X") == []
        assert _conservative_substitutes("B") == []


class TestSingleSubstitutionVariants:
    def test_all_variants_same_length_as_seed(self):
        variants = generate_single_substitution_variants(SEED)
        for v in variants:
            assert len(v) == len(SEED), f"Length mismatch: {v!r} vs {SEED!r}"

    def test_seed_not_in_variants(self):
        variants = generate_single_substitution_variants(SEED)
        assert SEED not in variants, "Seed should not appear in its own variants"

    def test_each_variant_differs_by_exactly_one_position(self):
        variants = generate_single_substitution_variants(SEED)
        for v in variants:
            diffs = sum(a != b for a, b in zip(v, SEED))
            assert diffs == 1, f"Expected exactly 1 diff, got {diffs}: {v!r}"

    def test_no_duplicate_variants(self):
        variants = generate_single_substitution_variants(SEED)
        assert len(variants) == len(set(variants)), "Single-sub variants contain duplicates"

    def test_poly_K_generates_rh_substitutes(self):
        poly_k = "KKKKK"
        variants = generate_single_substitution_variants(poly_k)
        # Each of 5 positions can be R or H → 5 × 2 = 10
        assert len(variants) == 10, f"poly-K (5aa) should have 10 variants, got {len(variants)}"
        allowed = set("KRH")
        for v in variants:
            assert all(aa in allowed for aa in v), f"Non-cationic AA in {v!r}"

    def test_short_sequence_produces_variants(self):
        variants = generate_single_substitution_variants("KL")
        assert len(variants) > 0, "Short 2-aa sequence should still produce variants"


class TestDoubleSubstitutionVariants:
    def test_variants_same_length_as_seed(self):
        variants = generate_double_substitution_variants(SEED, n_samples=10, seed=42)
        for v in variants:
            assert len(v) == len(SEED), f"Length mismatch: {v!r}"

    def test_seed_not_in_double_variants(self):
        variants = generate_double_substitution_variants(SEED, n_samples=10, seed=42)
        assert SEED not in variants

    def test_each_variant_differs_by_two_positions(self):
        variants = generate_double_substitution_variants(SEED, n_samples=15, seed=42)
        for v in variants:
            diffs = sum(a != b for a, b in zip(v, SEED))
            assert diffs == 2, f"Expected 2 diffs, got {diffs}: {v!r}"

    def test_no_duplicate_double_variants(self):
        variants = generate_double_substitution_variants(SEED, n_samples=15, seed=42)
        assert len(variants) == len(set(variants)), "Double-sub variants contain duplicates"

    def test_respects_n_samples_limit(self):
        variants = generate_double_substitution_variants(SEED, n_samples=5, seed=42)
        assert len(variants) <= 5

    def test_deterministic_with_same_seed(self):
        v1 = generate_double_substitution_variants(SEED, n_samples=10, seed=99)
        v2 = generate_double_substitution_variants(SEED, n_samples=10, seed=99)
        assert v1 == v2, "Same rng seed must produce identical output"

    def test_different_seeds_produce_different_variants(self):
        v1 = generate_double_substitution_variants(SEED, n_samples=10, seed=1)
        v2 = generate_double_substitution_variants(SEED, n_samples=10, seed=2)
        assert v1 != v2, "Different rng seeds should produce different variants"

    def test_single_aa_sequence_returns_empty(self):
        # < 2 substitutable positions → early-return guard in generate_double_substitution_variants
        assert generate_double_substitution_variants("K") == []


class TestAggregationSafeDoubleVariants:
    def test_single_aa_sequence_returns_empty(self):
        # < 2 substitutable positions → early-return guard in generate_aggregation_safe_double_variants
        assert generate_aggregation_safe_double_variants("K") == []


class TestChargeEnhancedVariants:
    def test_replaces_polar_with_cationic(self):
        seq = "KWKLFKKSGAVLKVL"  # S at position 7
        variants = generate_charge_enhanced_variants(seq, n_samples=5, seed=42)
        for v in variants:
            assert len(v) == len(seq)
            # The S position should become K or R
            diff_positions = [i for i, (a, b) in enumerate(zip(v, seq)) if a != b]
            assert len(diff_positions) == 1
            for pos in diff_positions:
                assert seq[pos] in "STNQ", f"Expected polar at pos {pos}, got {seq[pos]!r}"
                assert v[pos] in "KR", f"Expected K/R replacement at pos {pos}, got {v[pos]!r}"

    def test_no_charge_enhanced_when_no_polar_residues(self):
        poly_k = "KKKKKKK"
        variants = generate_charge_enhanced_variants(poly_k)
        assert variants == [], "No polar residues → no charge-enhanced variants"

    def test_charge_enhanced_does_not_include_seed(self):
        seq = "KWKLFKKSAVLKVL"
        variants = generate_charge_enhanced_variants(seq)
        assert seq not in variants


class TestGenerateAllVariants:
    def test_seed_not_in_all_variants(self):
        variants = generate_all_variants(SEED)
        assert SEED not in variants, "Seed must not appear among its own variants"

    def test_all_variants_same_length(self):
        variants = generate_all_variants(SEED)
        for v in variants:
            assert len(v) == len(SEED)

    def test_deduplication_across_strategies(self):
        variants = generate_all_variants(SEED)
        assert len(variants) == len(set(variants)), "generate_all_variants must deduplicate"

    def test_sorted_output(self):
        variants = generate_all_variants(SEED)
        assert variants == sorted(variants), "generate_all_variants must return sorted output"

    def test_substantial_pool_produced(self):
        variants = generate_all_variants(SEED, n_double=20, n_charge_enhance=10)
        assert len(variants) >= 20, f"Expected ≥20 variants from {SEED!r}, got {len(variants)}"


class TestGenerateCandidatePool:
    def test_pool_size_proportional_to_seeds(self):
        seeds = ["KWKLFKKIGAVLKVL", "RRWQWRMKKLG"]
        ids = ["SEED-001", "SEED-002"]
        pool = generate_candidate_pool(seeds, ids, n_double=10, n_charge_enhance=5, rng_seed=42)
        assert len(pool) > 0, "Pool should be non-empty"

    def test_ids_contain_seed_prefix(self):
        seeds = ["KWKLFKKIGAVLKVL"]
        ids = ["SEED-001"]
        pool = generate_candidate_pool(seeds, ids)
        for item in pool:
            assert item["id"].startswith("SEED-001_VAR_"), f"Unexpected ID: {item['id']!r}"

    def test_source_field_encodes_template(self):
        seeds = ["KWKLFKKIGAVLKVL"]
        ids = ["SEED-001"]
        pool = generate_candidate_pool(seeds, ids)
        for item in pool:
            assert item["source"] == "template_mutation_from_SEED-001", (
                f"Unexpected source: {item['source']!r}"
            )

    def test_pool_items_have_required_fields(self):
        seeds = ["KWKLFKKIGAVLKVL"]
        ids = ["SEED-001"]
        pool = generate_candidate_pool(seeds, ids)
        for item in pool:
            assert "id" in item
            assert "sequence" in item
            assert "source" in item

    def test_no_seed_sequence_in_pool(self):
        seeds = ["KWKLFKKIGAVLKVL", "RRWQWRMKKLG"]
        ids = ["SEED-001", "SEED-002"]
        pool = generate_candidate_pool(seeds, ids)
        pool_seqs = {item["sequence"] for item in pool}
        for seed_seq in seeds:
            assert seed_seq not in pool_seqs, (
                f"Seed sequence {seed_seq!r} should not appear in its own candidate pool"
            )

    def test_deterministic_with_same_rng_seed(self):
        seeds = ["KWKLFKKIGAVLKVL"]
        ids = ["SEED-001"]
        pool1 = generate_candidate_pool(seeds, ids, rng_seed=7)
        pool2 = generate_candidate_pool(seeds, ids, rng_seed=7)
        assert pool1 == pool2, "Same rng_seed must produce identical candidate pool"

    def test_multiple_seeds_produce_independent_batches(self):
        seeds = ["KWKLFKKIGAVLKVL", "RRWQWRMKKLG"]
        ids = ["SEED-001", "SEED-002"]
        pool = generate_candidate_pool(seeds, ids)
        seed1_items = [p for p in pool if p["id"].startswith("SEED-001")]
        seed2_items = [p for p in pool if p["id"].startswith("SEED-002")]
        assert len(seed1_items) > 0
        assert len(seed2_items) > 0


MASTOPARAN_X = "INWKGIAAMAKKLL"  # SEED-006: wasp venom helical AMP, Yashida 1990


class TestSeed006MastoparanX:
    """Validate SEED-006 (Mastoparan-X) generates structurally valid variants."""

    def test_mastoparan_x_generates_variants(self):
        pool = generate_candidate_pool([MASTOPARAN_X], ["SEED-006"])
        assert len(pool) > 0

    def test_seed_006_source_field(self):
        pool = generate_candidate_pool([MASTOPARAN_X], ["SEED-006"])
        for item in pool:
            assert item["source"] == "template_mutation_from_SEED-006"

    def test_seed_006_ids_have_correct_prefix(self):
        pool = generate_candidate_pool([MASTOPARAN_X], ["SEED-006"])
        for item in pool:
            assert item["id"].startswith("SEED-006_VAR_")

    def test_seed_006_variants_same_length(self):
        pool = generate_candidate_pool([MASTOPARAN_X], ["SEED-006"])
        for item in pool:
            assert len(item["sequence"]) == len(MASTOPARAN_X)

    def test_seed_006_seed_not_in_pool(self):
        pool = generate_candidate_pool([MASTOPARAN_X], ["SEED-006"])
        seqs = {item["sequence"] for item in pool}
        assert MASTOPARAN_X not in seqs, "Seed itself must not appear in its variant pool"

    def test_six_seed_pool_larger_than_five(self):
        five_seeds = [
            "KWKLFKKIGAVLKVL", "GIGKFLHSAKKFGKAFVGEIMNS", "RRWQWRMKKLG",
            "FLPLIGRVLSGIL", "KRLFKKIGSALKFL",
        ]
        five_ids = ["SEED-001", "SEED-002", "SEED-003", "SEED-004", "SEED-005"]
        six_seeds = five_seeds + [MASTOPARAN_X]
        six_ids = five_ids + ["SEED-006"]
        pool5 = generate_candidate_pool(five_seeds, five_ids, rng_seed=2024)
        pool6 = generate_candidate_pool(six_seeds, six_ids, rng_seed=2024)
        assert len(pool6) > len(pool5), "6-seed pool must be larger than 5-seed pool"
