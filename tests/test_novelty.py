"""Tests for scoring/novelty.py — levenshtein, normalized_similarity, novelty_score."""
from __future__ import annotations

from openamp_foundry.scoring.novelty import levenshtein, normalized_similarity, novelty_score
from openamp_foundry.types import PeptideCandidate


def _ref(cid: str, seq: str) -> PeptideCandidate:
    return PeptideCandidate(candidate_id=cid, sequence=seq, source="test")


class TestLevenshtein:
    def test_identical_strings(self):
        assert levenshtein("ABCDE", "ABCDE") == 0

    def test_single_substitution(self):
        assert levenshtein("ABCDE", "ABCDF") == 1

    def test_single_insertion(self):
        assert levenshtein("ABCD", "ABCDE") == 1

    def test_single_deletion(self):
        assert levenshtein("ABCDE", "ABCD") == 1

    def test_empty_vs_string(self):
        assert levenshtein("", "ABC") == 3

    def test_string_vs_empty(self):
        assert levenshtein("ABC", "") == 3

    def test_both_empty(self):
        assert levenshtein("", "") == 0

    def test_completely_different_same_length(self):
        assert levenshtein("AAA", "ZZZ") == 3

    def test_symmetric(self):
        a, b = "KWKLF", "DEDED"
        assert levenshtein(a, b) == levenshtein(b, a)


class TestNormalizedSimilarity:
    def test_identical_returns_one(self):
        assert normalized_similarity("ABC", "ABC") == 1.0

    def test_completely_different_short(self):
        # 3 edits to go from AAA to ZZZ, max_len=3 → 0.0
        assert normalized_similarity("AAA", "ZZZ") == 0.0

    def test_both_empty_returns_one(self):
        assert normalized_similarity("", "") == 1.0

    def test_one_empty_returns_zero(self):
        assert normalized_similarity("ABC", "") == 0.0

    def test_symmetric(self):
        a, b = "KWKLF", "KWKLI"
        assert normalized_similarity(a, b) == normalized_similarity(b, a)

    def test_single_substitution_in_short_peptide(self):
        # ABCDE vs ABCDF: 1 edit, max_len=5 → 1 - 1/5 = 0.8
        result = normalized_similarity("ABCDE", "ABCDF")
        assert abs(result - 0.8) < 1e-9

    def test_range_between_zero_and_one(self):
        result = normalized_similarity("KWKLFKKIGAVLKVL", "DEDEDEDEDEDEDEDE")
        assert 0.0 <= result <= 1.0

    def test_lower_for_different_than_similar(self):
        similar = normalized_similarity("KWKLFKKIGAVLKVL", "KWKLFKKIGAVLKVK")
        different = normalized_similarity("KWKLFKKIGAVLKVL", "DEDEDEDEDEDEDEDE")
        assert similar > different


class TestNoveltyScore:
    def test_no_references_returns_one(self):
        score, nearest = novelty_score("KWKLF", [])
        assert score == 1.0
        assert nearest is None

    def test_identical_to_reference_returns_zero(self):
        refs = [_ref("R1", "KWKLF")]
        score, nearest = novelty_score("KWKLF", refs)
        assert score == 0.0
        assert nearest is not None
        assert nearest["candidate_id"] == "R1"
        assert nearest["similarity"] == 1.0

    def test_score_between_zero_and_one(self):
        refs = [_ref("R1", "DEDEDEDE")]
        score, _ = novelty_score("KWKLF", refs)
        assert 0.0 <= score <= 1.0

    def test_nearest_has_required_keys(self):
        refs = [_ref("R1", "DEDEDEDE")]
        _, nearest = novelty_score("KWKLF", refs)
        assert nearest is not None
        for key in ("candidate_id", "source", "similarity", "sequence"):
            assert key in nearest

    def test_picks_most_similar_reference(self):
        refs = [
            _ref("far", "DEDEDEDEDEDEDEDE"),
            _ref("close", "KWKLF"),
        ]
        _, nearest = novelty_score("KWKLF", refs)
        assert nearest["candidate_id"] == "close"

    def test_high_novelty_for_unique_sequence(self):
        refs = [_ref("R1", "DEDEDEDEDEDEDEDE")]
        score, _ = novelty_score("KWKLFKKIGAVLKVL", refs)
        assert score > 0.5

    def test_low_novelty_for_near_duplicate(self):
        refs = [_ref("R1", "KWKLFKKIGAVLKVL")]
        score, _ = novelty_score("KWKLFKKIGAVLKVK", refs)  # 1 substitution in 15
        assert score < 0.2

    def test_empty_sequence_with_references_does_not_crash(self):
        # Empty candidate sequence → levenshtein("", ref) = len(ref), sim = 0 → novelty = 1.0
        # Pinned to detect any future change in empty-sequence handling.
        refs = [_ref("R1", "KWKLFKKIGAVLKVL")]
        score, nearest = novelty_score("", refs)
        assert 0.0 <= score <= 1.0
