"""Tests for generators/simple_mutation.py — mutate_sequence."""
from __future__ import annotations

from openamp_foundry.generators.simple_mutation import CANONICAL_AA, mutate_sequence

_SEQ = "KWKLFKKIGAVLKVL"
_CANONICAL = set(CANONICAL_AA)


def _hamming(a: str, b: str) -> int:
    return sum(c1 != c2 for c1, c2 in zip(a, b))


class TestMutateSequence:
    def test_empty_sequence_returns_empty(self):
        assert mutate_sequence("") == ""

    def test_empty_with_seed_returns_empty(self):
        assert mutate_sequence("", seed=42) == ""

    def test_zero_mutations_returns_original(self):
        assert mutate_sequence(_SEQ, mutations=0) == _SEQ

    def test_zero_mutations_with_seed_returns_original(self):
        assert mutate_sequence(_SEQ, mutations=0, seed=7) == _SEQ

    def test_negative_mutations_treated_as_zero(self):
        assert mutate_sequence(_SEQ, mutations=-5) == _SEQ

    def test_length_preserved_single_mutation(self):
        result = mutate_sequence(_SEQ, mutations=1, seed=0)
        assert len(result) == len(_SEQ)

    def test_length_preserved_many_mutations(self):
        result = mutate_sequence(_SEQ, mutations=10, seed=0)
        assert len(result) == len(_SEQ)

    def test_length_preserved_single_char(self):
        result = mutate_sequence("K", mutations=5, seed=0)
        assert len(result) == 1

    def test_all_chars_canonical_after_single_mutation(self):
        result = mutate_sequence(_SEQ, mutations=1, seed=42)
        assert all(c in _CANONICAL for c in result)

    def test_all_chars_canonical_after_many_mutations(self):
        result = mutate_sequence(_SEQ, mutations=8, seed=42)
        assert all(c in _CANONICAL for c in result)

    def test_single_mutation_changes_at_most_one_position(self):
        result = mutate_sequence(_SEQ, mutations=1, seed=7)
        assert _hamming(_SEQ, result) <= 1

    def test_seed_is_deterministic(self):
        a = mutate_sequence(_SEQ, mutations=3, seed=99)
        b = mutate_sequence(_SEQ, mutations=3, seed=99)
        assert a == b

    def test_different_seeds_produce_different_results(self):
        results = {mutate_sequence(_SEQ, mutations=1, seed=i) for i in range(100)}
        assert len(results) > 1

    def test_unseeded_calls_can_differ(self):
        # random.Random(None) seeds from os.urandom() in CPython 3.x.
        # With 278+ possible distinct outputs for a 15-mer, P(all 30 identical) is negligible.
        results = {mutate_sequence(_SEQ, mutations=1) for _ in range(30)}
        assert len(results) > 1, (
            "Expected at least 2 distinct outputs from 30 unseeded calls; "
            "failure indicates entropy source is broken or the function is constant."
        )

    def test_single_mutation_can_produce_identity_substitution(self):
        # mutate_sequence picks uniformly from 20 AAs including the original;
        # at least one seed among 200 should land on an identity substitution.
        found = any(
            mutate_sequence(_SEQ, mutations=1, seed=s) == _SEQ
            for s in range(200)
        )
        assert found, "Expected at least one seed to produce an identity substitution"

    def test_returns_str(self):
        assert isinstance(mutate_sequence(_SEQ), str)

    def test_returns_str_on_empty(self):
        assert isinstance(mutate_sequence(""), str)

    def test_canonical_aa_constant_has_20_entries(self):
        assert len(CANONICAL_AA) == 20

    def test_canonical_aa_constant_correct_residues(self):
        assert set(CANONICAL_AA) == set("ACDEFGHIKLMNPQRSTVWY")

    def test_single_residue_sequence_returns_valid_aa(self):
        result = mutate_sequence("K", mutations=5, seed=0)
        assert result in _CANONICAL

    def test_two_char_sequence_length_preserved(self):
        result = mutate_sequence("KW", mutations=3, seed=1)
        assert len(result) == 2
        assert all(c in _CANONICAL for c in result)
